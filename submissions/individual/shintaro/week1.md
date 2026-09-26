# Week 1 Exercise Log — @shintaro

## ① 演習結果（必須）

### Q1. 7月（生育期）と10月（収穫後）のNDVI値はどう変わるか？
7月（生育期）はNDVIが高く、地図上でも濃い緑で表示され、畑に作物が豊富にあることが分かる。一方、10月（収穫後）は目視でNDVIがおよそ0.1〜0.5の範囲に落ち込んでおり、講義で説明された「収穫後農地のNDVI値0.1~0.3」と一致しているように見える。生育期から収穫後にかけてNDVIが大きく低下する変化が確認できた。

### Q2. 収穫後の農地と休耕地を光学だけで区別しようとすると、なぜ失敗するのか？
NDVIはあくまで植生の豊かさを測る指標である。そのため、雑草の量など不確定要素の多い状態の収穫後の農地と休耕地ではどちらか判断することは難しい。


## ② AI の出力と検証（使った場合のみ）
使用したAIツール：ChatGPT

プロンプト：Google Earth EngineのPython APIを使って、Sentinel-2画像からNDVIを計算するコードを書いてください

AIの出力：
<<<<<<< HEAD
<<<<<<< HEAD
```python
=======
>>>>>>> 4877919 (Week1の解答)
=======
```python
>>>>>>> b63ce18 (week1.md)
# Google Colabの場合、最初に実行
# !pip install earthengine-api geemap

import ee
import geemap

# ============================================================
# 1. Earth Engineの認証・初期化
# ============================================================

# 自分のGoogle CloudプロジェクトIDに変更してください
PROJECT_ID = "your-google-cloud-project-id"

try:
    ee.Initialize(project=PROJECT_ID)

except Exception:
    ee.Authenticate()
    ee.Initialize(project=PROJECT_ID)


# ============================================================
# 2. 解析条件
# ============================================================

# 筑波周辺の解析範囲
# [西端経度, 南端緯度, 東端経度, 北端緯度]
aoi = ee.Geometry.Rectangle([
    140.00,
    36.00,
    140.20,
    36.20
])

start_date = "2025-05-01"
end_date = "2025-06-01"

# シーン全体の雲量上限[%]
max_cloud_percentage = 30


# ============================================================
# 3. 雲・雲影の除去
# ============================================================

def preprocess_sentinel2(image):
    """
    Sentinel-2画像から雲、雲影、巻雲、雪などを除去し、
    B4、B8、NDVIを返す。
    """

    # SCL：Scene Classification Layer
    scl = image.select("SCL")

    # 除外するSCLクラス
    # 3  : 雲影
    # 7  : 未分類・低確率の雲
    # 8  : 中確率の雲
    # 9  : 高確率の雲
    # 10 : 巻雲
    # 11 : 雪・氷
    clear_mask = (
        scl.neq(3)
        .And(scl.neq(7))
        .And(scl.neq(8))
        .And(scl.neq(9))
        .And(scl.neq(10))
        .And(scl.neq(11))
    )

    # 赤バンドと近赤外バンドを選択
    # Sentinel-2の反射率は10000倍された整数値なので0.0001倍する
    reflectance = (
        image
        .select(["B4", "B8"])
        .multiply(0.0001)
        .updateMask(clear_mask)
    )

    # NDVI = (近赤外 - 赤) / (近赤外 + 赤)
    ndvi = (
        reflectance
        .normalizedDifference(["B8", "B4"])
        .rename("NDVI")
    )

    return (
        reflectance
        .addBands(ndvi)
        .copyProperties(image, ["system:time_start"])
    )


# ============================================================
# 4. Sentinel-2画像の取得
# ============================================================

sentinel2 = (
    ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
    .filterBounds(aoi)
    .filterDate(start_date, end_date)
    .filter(
        ee.Filter.lt(
            "CLOUDY_PIXEL_PERCENTAGE",
            max_cloud_percentage
        )
    )
    .map(preprocess_sentinel2)
)

print("使用画像数:", sentinel2.size().getInfo())


# ============================================================
# 5. 期間内の画像を合成
# ============================================================

# 各ピクセルの中央値を取ることで、
# 残った雲や異常値の影響を小さくする
composite = sentinel2.median().clip(aoi)

ndvi_image = composite.select("NDVI")


# ============================================================
# 6. 地図への表示
# ============================================================

map_object = geemap.Map(
    center=[36.10, 140.10],
    zoom=11
)

# Sentinel-2の自然色画像
rgb_vis = {
    "bands": ["B4", "B3", "B2"],
    "min": 0.0,
    "max": 0.3
}

# NDVI表示設定
ndvi_vis = {
    "min": -0.2,
    "max": 0.8,
    "palette": [
        "blue",
        "white",
        "yellow",
        "lightgreen",
        "green",
        "darkgreen"
    ]
}

map_object.add_layer(
    ndvi_image,
    ndvi_vis,
    "NDVI"
)

map_object.add_layer(
    aoi,
    {},
    "解析範囲"
)

map_object
<<<<<<< HEAD
<<<<<<< HEAD
```
=======


>>>>>>> 4877919 (Week1の解答)
=======
```
>>>>>>> b63ce18 (week1.md)

その検証結果：
□ バンドの指定方法が自分のコードと一致しているか
["B4", "B8"]が指定されており、一致している
□ normalizedDifference の引数順（[NIR, Red]か[Red, NIR]か）
["B8", "B4"]の順で記述されており、NDVI = (NIR - Red) / (NIR + Red) の定義を分かっている
□ 生成されたコードに ee.ImageCollection の初期化が含まれているか
含まれている

## ③ 自分の気づき・考察
STEP4で農地のNDVIを求めた。以下がRedとNIRの値である。
1. 農地: B4(Red)=0.062, B8(NIR)=0.419 NDVI=0.742 
2. 農地: B4(Red)=0.125, B8(NIR)=0.384 NDVI=0.509 1から緯度・経度をそれぞれ0.01ずつずらした
3. 農地: B4(Red)=0.117, B8(NIR)=0.184 NDVI=0.223 1から緯度・経度をそれぞれ0.005ずつずらした
この結果をみると緯度・経度の微小なズレで求めたい値が大きくずれることがわかる。
衛星データは大きなスケールでやっていることを忘れないようにすべきだと感じた。

## ⭐ 発展課題（任意）
選択した課題：①
結果と気づき：stats['NDVI_min(max)']でNDVI値の最小値と最大値を求めました。最小値は約-0.8、最大値は1.0となり、NDVIは-1〜1に収まっていることが確認できた。
