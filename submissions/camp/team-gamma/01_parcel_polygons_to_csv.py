"""Part 1: 農地筆ポリゴン -> CSV化（座標系をWGS84に統一）

農林水産省の「筆ポリゴンデータ」は都道府県ごとに日本測地系2011(JGD2011)の
平面直角座標系（福島県は9系 = EPSG:6677、メートル単位）で配布される。
Google Earth Engineは緯度経度(WGS84, EPSG:4326)を前提に動作するため、
ここで明示的に再投影する。

ファイルに埋め込まれたCRS情報を自動検出して変換するので、仮にすでに緯度経度で
提供されているデータが来ても正しく動く（SOURCE_CRS_FALLBACK はCRS情報が全く
無い場合の保険）。

事前準備: 筆ポリゴン公開サイト (https://open.fude.maff.go.jp/) から相馬市・
南相馬市のデータをダウンロードして解凍し、INPUT_PATH にファイルパスを設定する。
"""
from __future__ import annotations

import os
from pathlib import Path

import geopandas as gpd
import pandas as pd
from shapely.geometry import Point

from gee_env import in_colab

# ==========================================================================
# 設定
# ==========================================================================

# ダウンロードした筆ポリゴンファイルのパス (.shp または .geojson / .fgb)。
# ローカルで動かす場合は環境変数 PARCEL_INPUT_PATH で個人のパスに上書きできる。
INPUT_PATH = os.environ.get(
    "PARCEL_INPUT_PATH", "/content/drive/MyDrive/astrocamp/MB0001_2026_2025_07.fgb"
)

# 元データに座標系(CRS)情報が全く無い場合のみ使うフォールバック。
# 福島県 = 平面直角座標系9系 (JGD2011) = EPSG:6677
# (JGD2000系の古いデータの場合は EPSG:2451 に読み替えること)
SOURCE_CRS_FALLBACK = "EPSG:6677"

# 出力CSVパス
OUTPUT_CSV = "parcels_wgs84.csv"

# 解析計画書 Step3 記載の候補エリア重心(起点)。ここからの半径内の筆だけに絞り込む。
# 全筆を対象にしたい場合は ROI_BUFFER_M = None にする。
CANDIDATE_POINTS = {
    # "soma_nishi": (140.9367, 37.7948),      # 相馬市西
    # "soma_higashi": (140.9644, 37.8041),    # 相馬市東
    "minamisoma_higashi": (141.0189, 37.6140),  # 南相馬市東側クラスタ
}
ROI_BUFFER_M = 500  # 各起点からのバッファ半径(m)

# 面積・重心の計算に使う投影座標系(メートル単位)。
# 福島県内であれば EPSG:6677 のままでよい(緯度経度上で直接centroid/areaを
# 計算すると歪みが出るため、必ず投影座標系上で計算してからWGS84に戻す)。
METRIC_CRS = "EPSG:6677"


# ==========================================================================
# 処理本体
# ==========================================================================

def mount_drive_if_colab() -> None:
    """Colab上でのみ Google Drive をマウントする。"""
    if in_colab():
        from google.colab import drive

        drive.mount("/content/drive")


def load_parcels(path: str, fallback_crs: str | None = None) -> gpd.GeoDataFrame:
    """筆ポリゴンを読み込み、CRSが無ければfallback_crsを付与する。"""
    gdf = gpd.read_file(path)
    if gdf.crs is None:
        if fallback_crs is None:
            raise ValueError(
                "元データに座標系(CRS)情報がありません。SOURCE_CRS_FALLBACK を指定してください。"
            )
        print(f"[警告] 元データに座標系情報がないため、{fallback_crs} とみなして処理します。")
        gdf = gdf.set_crs(fallback_crs)
    else:
        print(f"元データの座標系を検出しました: {gdf.crs}")
    return gdf


def filter_by_candidates(
    gdf_metric: gpd.GeoDataFrame,
    points: dict[str, tuple[float, float]],
    buffer_m: float | None,
    metric_crs: str,
) -> gpd.GeoDataFrame:
    """候補エリア(起点)からbuffer_m以内の筆だけに絞り込む(投影座標系上で実施)。"""
    if buffer_m is None:
        return gdf_metric

    pts_wgs84 = gpd.GeoSeries(
        [Point(lon, lat) for lon, lat in points.values()], crs="EPSG:4326"
    )
    pts_metric = pts_wgs84.to_crs(metric_crs)
    roi_union = pts_metric.buffer(buffer_m).union_all()

    mask = gdf_metric.geometry.intersects(roi_union)
    filtered = gdf_metric[mask]
    print(f"候補エリア(半径{buffer_m}m)で絞り込み: {len(gdf_metric)} 筆 -> {len(filtered)} 筆")
    return filtered


def build_output_table(
    gdf_metric: gpd.GeoDataFrame,
    metric_crs: str,
    id_col_candidates=("polygon_uu", "PolygonUUID", "polygon_uuid", "fude_id", "id"),
) -> pd.DataFrame:
    """重心(WGS84)・面積(m2)・ジオメトリ(WKT, WGS84)を含むテーブルを作る。

    重心と面積は必ず投影座標系(metric_crs)上で計算してからWGS84に変換する
    (緯度経度のまま計算すると高緯度・広域で歪みが出るため)。
    """
    gdf_metric = gdf_metric.reset_index(drop=True)

    id_col = next((c for c in id_col_candidates if c in gdf_metric.columns), None)
    if id_col is None:
        parcel_id = "P" + gdf_metric.index.astype(str).str.zfill(6)
        print("[警告] 既知のID列が見つからなかったため、連番のparcel_idを生成しました。")
    else:
        parcel_id = gdf_metric[id_col].astype(str)

    centroid_metric = gdf_metric.geometry.centroid
    centroid_wgs84 = gpd.GeoSeries(centroid_metric, crs=metric_crs).to_crs(epsg=4326)
    area_m2 = gdf_metric.geometry.area

    geom_wgs84 = gdf_metric.set_geometry(gdf_metric.geometry).set_crs(metric_crs).to_crs(epsg=4326)

    out = pd.DataFrame(
        {
            "parcel_id": parcel_id,
            "centroid_lon": centroid_wgs84.x.values,
            "centroid_lat": centroid_wgs84.y.values,
            "area_m2": area_m2.values,
            "geometry_wkt": geom_wgs84.geometry.to_wkt().values,
        }
    )
    return out


def main() -> None:
    mount_drive_if_colab()

    gdf = load_parcels(INPUT_PATH, SOURCE_CRS_FALLBACK)
    gdf_metric = gdf.to_crs(METRIC_CRS)
    gdf_metric = filter_by_candidates(gdf_metric, CANDIDATE_POINTS, ROI_BUFFER_M, METRIC_CRS)

    out = build_output_table(gdf_metric, METRIC_CRS)

    Path(OUTPUT_CSV).parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUTPUT_CSV, index=False)
    print(f"{len(out)} 筆を {OUTPUT_CSV} に出力しました。")
    print(out.head())


if __name__ == "__main__":
    main()
