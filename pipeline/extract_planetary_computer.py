"""公開STACから南相馬市ROIのSentinel実観測を筆別CSVへ集計する。

Earth Engine認証を用意できない環境向けの再現可能な代替経路。Microsoft
Planetary ComputerのSentinel-1 RTC（線形値をdBへ変換）とSentinel-2 L2Aを
使い、Webアプリへ秘密情報を持ち込まずに静的成果を作る。
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Iterable

import geopandas as gpd
import numpy as np
import pandas as pd
import planetary_computer
import pystac_client
import rasterio
from rasterio.features import geometry_mask
from rasterio.vrt import WarpedVRT
from rasterio.windows import Window, from_bounds

STAC_URL = "https://planetarycomputer.microsoft.com/api/stac/v1/"
ROI = [141.005, 37.608, 141.033, 37.620]
START, END = "2024-01-01", "2025-12-31"
INVALID_SCL = {0, 1, 3, 7, 8, 9, 10, 11}


def _clip_window(src: rasterio.DatasetReader, bounds: tuple[float, float, float, float]) -> Window:
    raw = from_bounds(*bounds, transform=src.transform)
    full = Window(0, 0, src.width, src.height)
    clipped = raw.intersection(full).round_offsets().round_lengths()
    if clipped.width <= 0 or clipped.height <= 0:
        raise ValueError("ROIがラスタ範囲と交差しません")
    return clipped


def _dilate(mask: np.ndarray, radius: int = 2) -> np.ndarray:
    """依存を増やさない小配列向けの正方形バッファ（10m画素で20m）。"""
    padded = np.pad(mask, radius, constant_values=False)
    out = np.zeros_like(mask, dtype=bool)
    height, width = mask.shape
    for dy in range(2 * radius + 1):
        for dx in range(2 * radius + 1):
            out |= padded[dy:dy + height, dx:dx + width]
    return out


def _choose_orbit(items: Iterable[Any]) -> int:
    """両年の3–4月・5–6月の最小観測数を最大にする下降軌道を選ぶ。"""
    counts: dict[int, dict[tuple[int, str], set[str]]] = defaultdict(lambda: defaultdict(set))
    for item in items:
        props = item.properties
        if str(props.get("sat:orbit_state", "")).lower() != "descending":
            continue
        orbit = props.get("sat:relative_orbit")
        dt = item.datetime
        if orbit is None or dt is None or dt.year not in (2024, 2025):
            continue
        window = "pre" if dt.month in (3, 4) else "flood" if dt.month in (5, 6) else None
        if window:
            counts[int(orbit)][(dt.year, window)].add(dt.date().isoformat())
    required = [(year, window) for year in (2024, 2025) for window in ("pre", "flood")]
    ranked = []
    for orbit, buckets in counts.items():
        values = [len(buckets[key]) for key in required]
        ranked.append((min(values), sum(values), -orbit, orbit))
    if not ranked:
        raise RuntimeError("両年の必須窓を評価できる下降軌道がありません")
    return max(ranked)[3]


def _sampling_fields(path: Path) -> gpd.GeoDataFrame:
    fields = gpd.read_file(path).to_crs(32654)
    if "field_id" not in fields:
        raise ValueError("GeoJSONにfield_idがありません")
    fields["source_geometry"] = fields.geometry
    inner = fields.geometry.buffer(-5)
    fields["geometry"] = [candidate if not candidate.is_empty and candidate.area >= 200 else original
                          for candidate, original in zip(inner, fields["source_geometry"])]
    fields["sampling_geometry"] = ["inner_5m" if a is not b else "original"
                                   for a, b in zip(fields.geometry, fields["source_geometry"])]
    fields["sampling_area_m2"] = fields.geometry.area
    return fields[["field_id", "geometry", "sampling_geometry", "sampling_area_m2"]]


def _field_stats(values: np.ndarray, valid: np.ndarray, transform: Any,
                 fields: gpd.GeoDataFrame) -> list[tuple[str, float | None, int, float, str]]:
    rows = []
    for field in fields.itertuples():
        inside = geometry_mask([field.geometry], out_shape=values.shape, transform=transform,
                               invert=True, all_touched=False)
        sample = values[inside & valid]
        count = int(sample.size)
        expected = max(float(field.sampling_area_m2) / 100.0, 1.0)
        median = float(np.median(sample)) if count else None
        rows.append((field.field_id, median, count, min(count / expected, 1.0), field.sampling_geometry))
    return rows


def _roi_bounds_in_crs(src: rasterio.DatasetReader) -> tuple[float, float, float, float]:
    return rasterio.warp.transform_bounds("EPSG:4326", src.crs, *ROI, densify_pts=21)


def _s2_rows(item: Any, fields: gpd.GeoDataFrame) -> list[dict[str, Any]]:
    signed = planetary_computer.sign(item)
    with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR", CPL_VSIL_CURL_ALLOWED_EXTENSIONS=".tif"):
        with rasterio.open(signed.assets["B04"].href) as red, rasterio.open(signed.assets["B08"].href) as nir:
            window = _clip_window(red, _roi_bounds_in_crs(red))
            red_data = red.read(1, window=window, masked=True).astype("float32")
            nir_data = nir.read(1, window=window, masked=True).astype("float32")
            transform = red.window_transform(window)
            with rasterio.open(signed.assets["SCL"].href) as scl_src:
                with WarpedVRT(scl_src, crs=red.crs, transform=red.transform,
                               width=red.width, height=red.height,
                               resampling=rasterio.enums.Resampling.nearest) as scl:
                    scl_data = scl.read(1, window=window, masked=True)
            denominator = nir_data + red_data
            ndvi = np.ma.divide(nir_data - red_data, denominator)
            invalid = np.ma.getmaskarray(red_data) | np.ma.getmaskarray(nir_data) | np.ma.getmaskarray(scl_data)
            invalid |= np.isin(np.asarray(scl_data), list(INVALID_SCL))
            invalid |= np.asarray(denominator) == 0
            valid = ~_dilate(invalid, radius=2)
            projected = fields.to_crs(red.crs)
            stats = _field_stats(np.asarray(ndvi), valid, transform, projected)
    date = item.datetime.date().isoformat()
    cloud = float(item.properties.get("eo:cloud_cover") or 0)
    return [{"field_id": field_id, "date": date, "ndvi_median": median,
             "ndvi_count": count, "valid_ratio": ratio,
             "scene_cloud_percent": cloud, "sampling_geometry": sampling,
             "source_item_id": item.id, "cloud_mask": "SCL+20m_buffer"}
            for field_id, median, count, ratio, sampling in stats]


def _s1_rows(item: Any, fields: gpd.GeoDataFrame, orbit: int) -> list[dict[str, Any]]:
    signed = planetary_computer.sign(item)
    with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR", CPL_VSIL_CURL_ALLOWED_EXTENSIONS=".tiff"):
        with rasterio.open(signed.assets["vh"].href) as vh:
            window = _clip_window(vh, _roi_bounds_in_crs(vh))
            linear = vh.read(1, window=window, masked=True).astype("float32")
            transform = vh.window_transform(window)
            raw = np.asarray(linear)
            valid = ~np.ma.getmaskarray(linear) & np.isfinite(raw) & (raw > 0)
            db = np.full(raw.shape, np.nan, dtype="float32")
            db[valid] = 10 * np.log10(raw[valid])
            projected = fields.to_crs(vh.crs)
            stats = _field_stats(db, valid, transform, projected)
    date = item.datetime.date().isoformat()
    return [{"field_id": field_id, "date": date, "vh_db_median": median,
             "vh_db_count": count, "valid_ratio": ratio,
             "relative_orbit": orbit, "orbit_pass": "DESCENDING",
             "sampling_geometry": sampling, "source_item_id": item.id,
             "source_product": "Sentinel-1 RTC"}
            for field_id, median, count, ratio, sampling in stats]


def _parallel(items: list[Any], workers: int, label: str, fn: Any) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(fn, item): item for item in items}
        for index, future in enumerate(as_completed(futures), 1):
            item = futures[future]
            rows.extend(future.result())
            print(f"{label} {index}/{len(items)} {item.datetime.date()}", flush=True)
    return rows


def extract(fields_path: Path, out_dir: Path, workers: int) -> None:
    fields = _sampling_fields(fields_path)
    catalog = pystac_client.Client.open(STAC_URL)
    print("STAC検索: Sentinel-1 RTC", flush=True)
    all_s1 = list(catalog.search(collections=["sentinel-1-rtc"], bbox=ROI,
                                 datetime=f"{START}/{END}").items())
    orbit = _choose_orbit(all_s1)
    s1_items = [item for item in all_s1
                if str(item.properties.get("sat:orbit_state", "")).lower() == "descending"
                and int(item.properties.get("sat:relative_orbit", -1)) == orbit]
    print(f"選択軌道: {orbit} DESCENDING / {len(s1_items)}シーン", flush=True)

    print("STAC検索: Sentinel-2 L2A（シーン雲量30%未満）", flush=True)
    all_s2 = list(catalog.search(collections=["sentinel-2-l2a"], bbox=ROI,
                                 datetime=f"{START}/{END}").items())
    s2_items = [item for item in all_s2 if float(item.properties.get("eo:cloud_cover") or 100) < 30]
    # 同日重複は雲量が少ない方を採用する。
    by_date: dict[str, Any] = {}
    for item in sorted(s2_items, key=lambda i: float(i.properties.get("eo:cloud_cover") or 100)):
        by_date.setdefault(item.datetime.date().isoformat(), item)
    s2_items = sorted(by_date.values(), key=lambda i: i.datetime)
    print(f"Sentinel-2: {len(s2_items)}シーン / {workers}並列", flush=True)

    s1_rows = _parallel(sorted(s1_items, key=lambda i: i.datetime), workers, "S1",
                        lambda item: _s1_rows(item, fields, orbit))
    s2_rows = _parallel(s2_items, workers, "S2", lambda item: _s2_rows(item, fields))

    out_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(s1_rows).to_csv(out_dir / "s1-vh.csv", index=False)
    pd.DataFrame(s2_rows).to_csv(out_dir / "s2-ndvi.csv", index=False)
    provenance = {
        "provider": "Microsoft Planetary Computer STAC",
        "stacUrl": STAC_URL,
        "collections": ["sentinel-1-rtc", "sentinel-2-l2a"],
        "observationRange": [START, END],
        "roi": ROI,
        "sentinel1": {"orbitPass": "DESCENDING", "relativeOrbit": orbit, "sceneCount": len(s1_items),
                      "unitConversion": "10*log10(RTC linear VH)"},
        "sentinel2": {"sceneCloudMaxPercent": 30, "sceneCount": len(s2_items),
                      "cloudMask": "SCL invalid classes + 20m square buffer",
                      "cloudProbability": "not available in this STAC collection"},
    }
    (out_dir / "provenance.json").write_text(json.dumps(provenance, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"出力: {out_dir} / S1={len(s1_rows)}行 S2={len(s2_rows)}行", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--fields", type=Path, default=Path("public/data/field-results.geojson"))
    parser.add_argument("--out", type=Path, default=Path("tmp/planetary-computer"))
    parser.add_argument("--workers", type=int, default=6)
    args = parser.parse_args()
    extract(args.fields, args.out, max(1, args.workers))
