"""Earth Engineから本番用の筆別NDVI/VH観測テーブルをDriveへ書き出す。

クライアントWebアプリはGEEへ接続しない。このバッチの出力を検査後、
``classify_year`` と同じ観測スキーマへ変換して静的成果を再生成する。
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import ee

ROI = [141.005, 37.608, 141.033, 37.620]
START, END = "2024-01-01", "2026-01-01"
ORBIT_PASS = "DESCENDING"


def fields_from_geojson(path: Path) -> ee.FeatureCollection:
    data = json.loads(path.read_text(encoding="utf-8"))
    features = []
    for feature in data["features"]:
        geom = ee.Geometry(feature["geometry"])
        inner = geom.buffer(-5)
        sampling = ee.Geometry(ee.Algorithms.If(inner.area(1).gte(200), inner, geom))
        features.append(ee.Feature(sampling, {
            "field_id": feature["properties"]["field_id"],
            "area_m2": geom.area(1),
            "sampling_geometry": ee.Algorithms.If(inner.area(1).gte(200), "inner_5m", "original"),
        }))
    return ee.FeatureCollection(features)


def choose_orbit(roi: ee.Geometry) -> int:
    collection = (ee.ImageCollection("COPERNICUS/S1_GRD").filterBounds(roi).filterDate(START, END)
                  .filter(ee.Filter.eq("instrumentMode", "IW"))
                  .filter(ee.Filter.eq("orbitProperties_pass", ORBIT_PASS))
                  .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VH")))
    counts = collection.aggregate_histogram("relativeOrbitNumber_start").getInfo()
    if not counts:
        raise RuntimeError("対象ROIにSentinel-1観測がありません")
    # 最大観測数、同数なら小さい軌道番号。2024/2025で同じ軌道を使う。
    return int(sorted(counts.items(), key=lambda item: (-item[1], int(item[0])))[0][0])


def add_s2_mask(image: ee.Image) -> ee.Image:
    probability = ee.Image(image.get("cloud_probability")).select("probability")
    scl = image.select("SCL")
    invalid_scl = (scl.eq(0).Or(scl.eq(1)).Or(scl.eq(3)).Or(scl.eq(7)).Or(scl.eq(8))
                   .Or(scl.eq(9)).Or(scl.eq(10)).Or(scl.eq(11)))
    invalid = probability.gte(40).Or(invalid_scl).focal_max(radius=20, units="meters")
    ndvi = image.normalizedDifference(["B8", "B4"]).rename("NDVI")
    return (ndvi.updateMask(invalid.Not()).copyProperties(image, ["system:time_start", "CLOUDY_PIXEL_PERCENTAGE"])
            .set("date", image.date().format("YYYY-MM-dd")))


def reduce_collection(collection: ee.ImageCollection, fields: ee.FeatureCollection, band: str, prefix: str) -> ee.FeatureCollection:
    def reduce_one(image: ee.Image) -> ee.FeatureCollection:
        reducer = ee.Reducer.median().combine(ee.Reducer.count(), sharedInputs=True)
        reduced = image.select(band).reduceRegions(collection=fields, reducer=reducer, scale=10, crs="EPSG:32654", tileScale=4)
        return reduced.map(lambda f: f.set({
            "date": image.date().format("YYYY-MM-dd"),
            "scene_cloud_percent": image.get("CLOUDY_PIXEL_PERCENTAGE"),
            "relative_orbit": image.get("relativeOrbitNumber_start"),
            "orbit_pass": image.get("orbitProperties_pass"),
            "value_name": prefix,
            "valid_ratio": ee.Number(f.get(f"{band}_count")).divide(ee.Number(f.get("area_m2")).divide(100)).min(1),
        }))
    return collection.map(reduce_one).flatten()


def start_exports(project: str, folder: str, fields_path: Path) -> None:
    try:
        ee.Initialize(project=project)
    except Exception as exc:
        raise SystemExit("Earth Engine認証後に再実行してください: earthengine authenticate") from exc
    fields = fields_from_geojson(fields_path)
    roi = ee.Geometry.Rectangle(ROI)
    orbit = choose_orbit(roi)
    s1 = (ee.ImageCollection("COPERNICUS/S1_GRD").filterBounds(roi).filterDate(START, END)
          .filter(ee.Filter.eq("instrumentMode", "IW")).filter(ee.Filter.eq("orbitProperties_pass", ORBIT_PASS))
          .filter(ee.Filter.eq("relativeOrbitNumber_start", orbit)).select("VH"))
    s2_sr = (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED").filterBounds(roi).filterDate(START, END)
             .filter(ee.Filter.lte("CLOUDY_PIXEL_PERCENTAGE", 30)))
    s2_cp = ee.ImageCollection("COPERNICUS/S2_CLOUD_PROBABILITY").filterBounds(roi).filterDate(START, END)
    joined = ee.ImageCollection(ee.Join.saveFirst("cloud_probability").apply(
        primary=s2_sr, secondary=s2_cp, condition=ee.Filter.equals(leftField="system:index", rightField="system:index")
    )).map(add_s2_mask)
    exports = [
        (reduce_collection(s1, fields, "VH", "vh_db"), "soramamori_s1_vh_2024_2025"),
        (reduce_collection(joined, fields, "NDVI", "ndvi"), "soramamori_s2_ndvi_2024_2025"),
    ]
    print(f"選択軌道: {orbit} ({ORBIT_PASS})")
    for table, name in exports:
        task = ee.batch.Export.table.toDrive(collection=table, description=name, folder=folder, fileFormat="CSV")
        task.start()
        print(f"開始: {name} / task={task.id}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True, help="Earth EngineのGoogle Cloud project ID")
    parser.add_argument("--folder", default="soramamori-earth-engine")
    parser.add_argument("--fields", type=Path, default=Path("public/data/field-results.geojson"))
    args = parser.parse_args()
    start_exports(args.project, args.folder, args.fields)
