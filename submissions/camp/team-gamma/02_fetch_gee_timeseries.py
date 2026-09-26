"""Part 2A: Earth Engine で筆ごとの VV(SAR)・MNDWI(光学) 時系列を取得する。

01_parcel_polygons_to_csv.py の出力(parcels_wgs84.csv)を読み込み、GEE上で
筆ごとに時系列をサンプリングして sar_vv_timeseries.csv / mndwi_timeseries.csv
に書き出す。実行には GEE の認証・ネットワークが必要（gee_env.init_gee() で
事前に初期化しておくこと）。

ポイント:
- 軌道は解析計画書Step4-1で確認済みの46番(DESCENDING)に固定
- 筆ポリゴンは内側に3m縮小(negative buffer)してから reduceRegions でサンプリング
- reduceRegions を画像ごとにmapする書き方にすることで、筆数×観測回数が
  多くてもサーバー側でバッチ処理できる（筆ごとにクライアント側でループする
  方式は数百筆規模になると遅い・タイムアウトしやすいので避ける）
- MNDWIは (Green-SWIR)/(Green+SWIR) = (B3-B11)/(B3+B11) で算出。SWIR(B11)は
  20m解像度なのでGreen(B3, 10m)と解像度が異なる点に注意（小さい筆では
  隣接筆の混入リスクがあるため、scaleパラメータの取り扱いは要検証）
- 雲マスクはシーン単位の雲量ではなく、SCLバンドによるピクセル単位のマスクを
  使用（シーン全体の雲量%だけでは対象筆が実際にクリアかどうか分からないため）
"""
from __future__ import annotations

import ee
import pandas as pd
import shapely.wkt
from shapely.geometry import mapping

from gee_env import init_gee

INPUT_PARCELS_CSV = "parcels_wgs84.csv"

NEG_BUFFER_M = -3
TIME_START = "2025-04-01"
TIME_END = "2025-12-15"
ORBIT_PASS = "DESCENDING"
RELATIVE_ORBIT = 46  # 解析計画書Step4-1で確認済みの軌道番号

OUTPUT_SAR_CSV = "sar_vv_timeseries.csv"
OUTPUT_MNDWI_CSV = "mndwi_timeseries.csv"


def build_parcels_fc(parcels_df: pd.DataFrame, neg_buffer_m: float = NEG_BUFFER_M) -> ee.FeatureCollection:
    """parcels_wgs84.csv の各行を、内側に縮小した ee.Feature に変換する。"""
    features = []
    for _, row in parcels_df.iterrows():
        geom = shapely.wkt.loads(row["geometry_wkt"])
        ee_geom = ee.Geometry(mapping(geom)).buffer(neg_buffer_m)
        features.append(ee.Feature(ee_geom, {"parcel_id": row["parcel_id"]}))
    return ee.FeatureCollection(features)


def _add_date(img: ee.Image) -> ee.Image:
    return img.set("date_str", img.date().format("YYYY-MM-dd"))


def fetch_sar_vv(parcels_fc: ee.FeatureCollection, roi: ee.Geometry) -> pd.DataFrame:
    """Sentinel-1 VV(軌道固定)を筆ごとに平均して時系列テーブルを作る。"""
    s1 = (
        ee.ImageCollection("COPERNICUS/S1_GRD")
        .filterBounds(roi)
        .filterDate(TIME_START, TIME_END)
        .filter(ee.Filter.eq("instrumentMode", "IW"))
        .filter(ee.Filter.eq("orbitProperties_pass", ORBIT_PASS))
        .filter(ee.Filter.eq("relativeOrbitNumber_start", RELATIVE_ORBIT))
        .select("VV")
        .map(_add_date)
    )

    def reduce_s1_image(img: ee.Image) -> ee.FeatureCollection:
        date_str = img.get("date_str")
        reduced = img.reduceRegions(collection=parcels_fc, reducer=ee.Reducer.mean(), scale=10)
        return reduced.map(lambda f: f.set("date", date_str))

    s1_table = s1.map(reduce_s1_image).flatten()
    s1_df = pd.DataFrame([f["properties"] for f in s1_table.getInfo()["features"]])
    s1_df.rename(columns={"mean": "VV_mean"}, inplace=True)
    return s1_df


def _mask_s2_clouds(img: ee.Image) -> ee.Image:
    scl = img.select("SCL")
    # 3=cloud shadow, 8=cloud medium prob, 9=cloud high prob, 10=cirrus
    mask = scl.neq(3).And(scl.neq(8)).And(scl.neq(9)).And(scl.neq(10))
    return img.updateMask(mask)


def _add_mndwi(img: ee.Image) -> ee.Image:
    green = img.select("B3").divide(10000)
    swir = img.select("B11").divide(10000)
    mndwi = green.subtract(swir).divide(green.add(swir)).rename("MNDWI")
    ndvi = img.normalizedDifference(["B8", "B4"]).rename("NDVI")  # 参考情報として保持
    return img.addBands([mndwi, ndvi]).copyProperties(img, ["system:time_start"])


def fetch_mndwi(parcels_fc: ee.FeatureCollection, roi: ee.Geometry) -> pd.DataFrame:
    """Sentinel-2 L2A から筆ごとのMNDWI/NDVI時系列を作る(ピクセル単位の雲マスク適用済み)。"""
    s2 = (
        ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
        .filterBounds(roi)
        .filterDate(TIME_START, TIME_END)
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 20))
        .map(_mask_s2_clouds)
        .map(_add_mndwi)
        .map(_add_date)
    )

    def reduce_s2_image(img: ee.Image) -> ee.FeatureCollection:
        date_str = img.get("date_str")
        reduced = img.select(["MNDWI", "NDVI"]).reduceRegions(
            collection=parcels_fc, reducer=ee.Reducer.mean(), scale=10
        )
        return reduced.map(lambda f: f.set("date", date_str))

    s2_table = s2.map(reduce_s2_image).flatten()
    return pd.DataFrame([f["properties"] for f in s2_table.getInfo()["features"]])


def main() -> None:
    init_gee()

    parcels_df = pd.read_csv(INPUT_PARCELS_CSV)
    parcels_fc = build_parcels_fc(parcels_df)
    roi = parcels_fc.geometry().bounds()

    # 件数が多い場合は getInfo() がタイムアウトするため、
    # ee.batch.Export.table.toDrive(collection=..., ...) によるバッチ
    # エクスポートに切り替えること(筆数 x 観測回数が数百筆規模になると危険)。
    sar_df = fetch_sar_vv(parcels_fc, roi)
    sar_df.to_csv(OUTPUT_SAR_CSV, index=False)

    mndwi_df = fetch_mndwi(parcels_fc, roi)
    mndwi_df.to_csv(OUTPUT_MNDWI_CSV, index=False)

    print(f"SAR: {len(sar_df)} 行, MNDWI: {len(mndwi_df)} 行を書き出しました。")


if __name__ == "__main__":
    main()
