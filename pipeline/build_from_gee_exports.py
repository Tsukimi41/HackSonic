"""GEEのS1/S2 CSVからWebアプリ用の実観測成果を構築する。

申告は引き続き架空デモ値であり、目視検証ラベルは別工程で付与する。
"""
from __future__ import annotations

import argparse
import bisect
import copy
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

import pandas as pd

from soramamori.engine import classify_year, compare_years, priority_components
from generate_demo import sensitivity_table

JST = timezone(timedelta(hours=9))


def _row_value(row: pd.Series, names: list[str]) -> float | None:
    for name in names:
        if name in row and pd.notna(row[name]):
            return float(row[name])
    return None


def _valid(row: pd.Series, count_names: list[str]) -> bool:
    count = _row_value(row, count_names)
    ratio = _row_value(row, ["valid_ratio"])
    return count is not None and ratio is not None and count >= 3 and ratio >= .5


def _s2_with_fallback(group: pd.DataFrame) -> tuple[pd.DataFrame, bool]:
    """20%を標準とし、必須窓不足時だけ20–30%のシーンを足す。"""
    group = group.copy()
    group["date_parsed"] = pd.to_datetime(group["date"])
    cloud_source = group["scene_cloud_percent"] if "scene_cloud_percent" in group else pd.Series(0, index=group.index)
    group["cloud"] = pd.to_numeric(cloud_source, errors="coerce").fillna(0)
    group["pixel_valid"] = group.apply(lambda r: _valid(r, ["ndvi_count", "NDVI_count", "count"]), axis=1)
    selected = group[group["pixel_valid"] & (group["cloud"] <= 20)].copy()
    month = selected["date_parsed"].dt.month
    may_ok = (month == 5).sum() >= 2
    growing = selected[month.between(6, 9)]
    growing_ok = len(growing) >= 3 and growing["date_parsed"].dt.month.nunique() >= 2
    if may_ok and growing_ok:
        return selected, False
    extra = group[group["pixel_valid"] & group["cloud"].between(20, 30, inclusive="right")]
    if may_ok:
        extra = extra[extra["date_parsed"].dt.month.between(6, 9)]
    elif growing_ok:
        extra = extra[extra["date_parsed"].dt.month == 5]
    return pd.concat([selected, extra]).drop_duplicates(subset=["date"]).sort_values("date"), not extra.empty


def observations(s1: pd.DataFrame, s2: pd.DataFrame, field_id: str, year: int) -> tuple[list[dict[str, Any]], bool]:
    by_date: dict[str, dict[str, Any]] = {}
    s1_group = s1[(s1["field_id"] == field_id) & pd.to_datetime(s1["date"]).dt.year.eq(year)]
    for _, row in s1_group.iterrows():
        valid = _valid(row, ["vh_db_count", "VH_count", "count"])
        date = str(row["date"])[:10]
        by_date[date] = {"date": date, "ndvi": None, "vh_db": _row_value(row, ["vh_db_median", "VH_median", "median"]),
                         "vv_db": None, "valid_s1": valid, "valid_s2": False,
                         "valid_pixel_count": int(_row_value(row, ["vh_db_count", "VH_count", "count"]) or 0),
                         "expected_pixel_count": None, "valid_ratio": _row_value(row, ["valid_ratio"]) or 0}
    s2_group = s2[(s2["field_id"] == field_id) & pd.to_datetime(s2["date"]).dt.year.eq(year)]
    selected, fallback = _s2_with_fallback(s2_group)
    for _, row in selected.iterrows():
        date = str(row["date"])[:10]
        target = by_date.setdefault(date, {"date": date, "ndvi": None, "vh_db": None, "vv_db": None, "valid_s1": False,
                                                   "valid_s2": False, "valid_pixel_count": 0, "expected_pixel_count": None, "valid_ratio": 0})
        target.update({"ndvi": _row_value(row, ["ndvi_median", "NDVI_median", "median"]), "valid_s2": True,
                       "valid_pixel_count": int(_row_value(row, ["ndvi_count", "NDVI_count", "count"]) or 0),
                       "valid_ratio": _row_value(row, ["valid_ratio"]) or 0})
    return sorted(by_date.values(), key=lambda r: r["date"]), fallback


def build(s1_path: Path, s2_path: Path, template_path: Path, out_dir: Path, config_path: Path,
          provenance_path: Path | None = None) -> None:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    collection = json.loads(template_path.read_text(encoding="utf-8"))
    s1, s2 = pd.read_csv(s1_path), pd.read_csv(s2_path)
    series: dict[str, Any] = {}
    properties = [f["properties"] for f in collection["features"]]
    areas = sorted(p["area_ha"] for p in properties)
    target_records: list[tuple[list[dict[str, Any]], float]] = []
    for p in properties:
        yearly = {}
        series[p["field_id"]] = {}
        for year in (2024, 2025):
            rows, fallback = observations(s1, s2, p["field_id"], year)
            result = classify_year(rows, config, p["area_ha"])
            if fallback:
                result["quality_flags"].append("SCENE_CLOUD_FALLBACK_30")
                if result["confidence"] is not None:
                    result["confidence"] = min(result["confidence"], .79)
                if result["subtype_confidence"] is not None:
                    result["subtype_confidence"] = min(result["subtype_confidence"], .79)
            yearly[year] = result
            series[p["field_id"]][str(year)] = {"observations": rows, "features": result["features"]}
            if year == 2025:
                target_records.append((rows, p["area_ha"]))
        change, change_confidence, change_reasons = compare_years(yearly[2024], yearly[2025])
        base, target = yearly[2024], yearly[2025]
        p.update({
            "baseline_status": base["status"], "baseline_confidence": base["confidence"], "baseline_subtype": base["cultivation_subtype"],
            "status": target["status"], "confidence": target["confidence"], "reason_codes": target["reason_codes"],
            "cultivation_subtype": target["cultivation_subtype"], "subtype_confidence": target["subtype_confidence"],
            "subtype_reason_codes": target["subtype_reason_codes"], "change_type": change, "change_confidence": change_confidence,
            "change_reason_codes": change_reasons, "valid_s2_count": target["valid_s2_count"], "valid_s1_count": target["valid_s1_count"],
            "observation_quality": target["observation_quality"], "quality_flags": target["quality_flags"],
            "ndvi_max": target["ndvi_max"], "ndvi_amplitude": target["ndvi_amplitude"], "ndvi_may": target["ndvi_may"],
            "ndvi_aug": target["ndvi_aug"], "vh_may_db": target["vh_may_db"], "vh_aug_db": target["vh_aug_db"],
        })
        percentile = bisect.bisect_left(areas, p["area_ha"]) / max(len(areas) - 1, 1)
        p["priority_components"] = priority_components(p, percentile)
        p["priority_score"] = round(sum(p["priority_components"].values()), 2)
        p["auto_candidate"] = p["declaration_match"] == "mismatch" or p["status"] in {"fallow_candidate", "review_required", "insufficient_observation"} or change != "stable"

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "field-results.geojson").write_text(json.dumps(collection, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    (out_dir / "field-timeseries.json").write_text(json.dumps({"fields": series}, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    source_manifest = template_path.parent / "manifest.json"
    manifest = json.loads(source_manifest.read_text(encoding="utf-8")) if source_manifest.exists() else {}
    provenance = (json.loads(provenance_path.read_text(encoding="utf-8"))
                  if provenance_path and provenance_path.exists() else None)
    provider = provenance["provider"] if provenance else "Google Earth Engine"
    notices = ["圃場境界は農林水産省2026年筆ポリゴン",
               f"衛星時系列は{provider}で集計したSentinel-1/2実観測",
               "営農申告は照合機能確認用の参考入力データ", "24筆・2名の独立目視検証は未実施"]
    manifest.update({"generatedAt": datetime.now(JST).isoformat(timespec="seconds"),
                     "dataMode": "actual_sentinel_observations_synthetic_declarations",
                     "observationSource": provider, "notices": notices})
    if provenance:
        manifest["provenance"] = provenance
        manifest["relativeOrbitNumberStart"] = provenance["sentinel1"]["relativeOrbit"]
        manifest["orbitPass"] = provenance["sentinel1"]["orbitPass"]
        manifest["sourceObservationRange"] = {"start": provenance["observationRange"][0],
                                              "end": provenance["observationRange"][1]}
        manifest["cloudMask"] = {
            "sceneCloudPercent": 20,
            "fallbackSceneCloudPercent": provenance["sentinel2"]["sceneCloudMaxPercent"],
            "cloudProbabilityMax": None,
            "method": provenance["sentinel2"]["cloudMask"],
            "differenceFromBaseline": "Cloud Probability 40%未満は未適用",
        }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    methodology_path = template_path.parent / "methodology.json"
    if methodology_path.exists():
        methodology = json.loads(methodology_path.read_text(encoding="utf-8"))
        methodology["sensitivity"] = sensitivity_table(target_records, config)
        (out_dir / "methodology.json").write_text(json.dumps(methodology, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--s1", type=Path, required=True)
    parser.add_argument("--s2", type=Path, required=True)
    parser.add_argument("--template", type=Path, default=Path("public/data/field-results.geojson"))
    parser.add_argument("--out", type=Path, default=Path("public/data"))
    parser.add_argument("--config", type=Path, default=Path("pipeline/config.json"))
    parser.add_argument("--provenance", type=Path)
    args = parser.parse_args()
    build(args.s1, args.s2, args.template, args.out, args.config, args.provenance)
