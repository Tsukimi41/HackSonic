"""筆ポリゴン・Sentinel-2画像を folium 地図で確認する（探索用、パイプライン本体には不要）。

Colab上では display(m) でインライン表示、ローカルでは HTML ファイルに保存する。

実行:
    python 04_visualize.py            # 筆ポリゴンの地図のみ
    python 04_visualize.py --s2       # + Sentinel-2 RGB画像を重ねた地図(GEE認証が必要)
"""
from __future__ import annotations

import argparse

import folium
import geopandas as gpd
import pandas as pd
from shapely import wkt

from gee_env import in_colab, init_gee

INPUT_PARCELS_CSV = "parcels_wgs84.csv"
S2_TIME_START = "2025-04-01"
S2_TIME_END = "2025-07-15"


def _show_or_save(m: folium.Map, out_path: str) -> None:
    if in_colab():
        from IPython.display import display

        display(m)
    else:
        m.save(out_path)
        print(f"地図を {out_path} に保存しました。ブラウザで開いて確認してください。")


def load_parcels_gdf(csv_path: str = INPUT_PARCELS_CSV) -> gpd.GeoDataFrame:
    df = pd.read_csv(csv_path)
    df["geometry"] = df["geometry_wkt"].apply(wkt.loads)
    return gpd.GeoDataFrame(df, geometry="geometry", crs="EPSG:4326")


def build_parcel_map(gdf: gpd.GeoDataFrame) -> folium.Map:
    center_lat = gdf["centroid_lat"].mean()
    center_lon = gdf["centroid_lon"].mean()

    m = folium.Map(location=[center_lat, center_lon], zoom_start=13)
    folium.GeoJson(
        gdf,
        name="農地ポリゴン",
        style_function=lambda feature: {
            "fillColor": "blue",
            "color": "blue",
            "weight": 2,
            "fillOpacity": 0.4,
        },
        tooltip=folium.GeoJsonTooltip(fields=["parcel_id", "area_m2"], aliases=["筆ID:", "面積(m2):"]),
    ).add_to(m)
    return m


def _add_ee_layer(self: folium.Map, ee_image_object, vis_params: dict, name: str) -> None:
    map_id_dict = ee_image_object.getMapId(vis_params)
    folium.raster_layers.TileLayer(
        tiles=map_id_dict["tile_fetcher"].url_format,
        attr='Map Data &copy; <a href="https://earthengine.google.com/">Google Earth Engine</a>',
        name=name,
        overlay=True,
        control=True,
    ).add_to(self)


folium.Map.add_ee_layer = _add_ee_layer


def build_sentinel2_map(gdf: gpd.GeoDataFrame) -> folium.Map:
    """筆ポリゴンに Sentinel-2 の真色RGB画像を重ねた地図を作る(GEE初期化済みであること)。"""
    import ee

    bounds = gdf.total_bounds  # [minx, miny, maxx, maxy]
    ee_roi = ee.Geometry.Rectangle([bounds[0], bounds[1], bounds[2], bounds[3]])

    s2_collection = (
        ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
        .filterBounds(ee_roi)
        .filterDate(S2_TIME_START, S2_TIME_END)
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 20))
    )
    s2_image = s2_collection.median()

    center_lat = gdf["centroid_lat"].mean()
    center_lon = gdf["centroid_lon"].mean()
    m = folium.Map(location=[center_lat, center_lon], zoom_start=13)

    vis_params = {"bands": ["B4", "B3", "B2"], "min": 0, "max": 3000, "gamma": 1.4}
    m.add_ee_layer(s2_image, vis_params, "Sentinel-2 RGB (True Color)")

    folium.GeoJson(
        gdf,
        name="農地ポリゴン",
        style_function=lambda feature: {"fillColor": "none", "color": "red", "weight": 1.5},
        tooltip=folium.GeoJsonTooltip(fields=["parcel_id", "area_m2"], aliases=["筆ID:", "面積(m2):"]),
    ).add_to(m)
    m.add_child(folium.LayerControl())
    return m


def main(with_s2: bool) -> None:
    gdf = load_parcels_gdf()

    m = build_parcel_map(gdf)
    _show_or_save(m, "parcels_map.html")

    if with_s2:
        init_gee()
        try:
            m_rgb = build_sentinel2_map(gdf)
            _show_or_save(m_rgb, "sentinel2_map.html")
        except Exception as e:
            print(f"画像の取得または表示中にエラーが発生しました: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--s2", action="store_true", help="Sentinel-2 RGB画像を重ねた地図も作成する")
    args = parser.parse_args()
    main(with_s2=args.s2)
