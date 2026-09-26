# OpenStreetMap ガイド — 水域・森林の座標取得

OpenStreetMap（OSM）の **Overpass API** を使って、対象地域の水域（河川・ため池・潟湖）や森林の座標を取得する方法を説明する。

## 基本方針

| 項目 | 内容 |
|------|------|
| **用途** | 解析対象エリアの地理的文脈（水・森林・農地）の参照座標を得る |
| **利点** | 無料・アカウント不要・名前付きの地物（例「松川浦」「宇多川」）を座標付きで取得できる |
| **位置づけ** | 衛星データ（Sentinel-2 等）の**補助・背景**として使う。作付判別の主役は衛星データ |
| **要確認** | OSM はボランティアデータのため精度・更新時期は不均一。座標は Sentinel-2 で最終確認する |

---

## いつ使うか

| 状況 | おすすめ |
|------|---------|
| 地域の河川・ため池・樹林の位置を座標付きで知りたい | **OSM Overpass API** |
| 水域・植生を「決まった基準で全域」に分類したい | GEE + 土地被覆データ（JAXA ALOS / ESA WorldCover） |
| 特定時点の水面・緑の広がりを確認したい | GEE で Sentinel-2 NDWI（水）／NDVI（緑）を計算 |
| 農地の区画を特定したい | 農水省 農地ポリゴン / eMAFF 農地ナビ |

OSM は「ここに○○がある」という**名前付きの点・面**を素早く得るのに向く。面的な一貫分類は GEE の土地被覆データを使う。

---

## 方法1：overpass-turbo（ブラウザで手軽に）

1. [overpass-turbo.eu](https://overpass-turbo.eu/) を開く
2. 左ペインにクエリを貼り付けて「Run」
3. 右上の「Export」→「GPX / GeoJSON / CSV」で保存

```ql
[out:json][timeout:90];
(
  nwr["natural"="water"](37.77,140.90,37.83,141.01);   /* ため池・湖沼 */
  nwr["waterway"="river"](37.77,140.90,37.83,141.01);  /* 河川 */
  nwr["natural"="wood"](37.77,140.90,37.83,141.01);    /* 樹林 */
  nwr["landuse"="forest"](37.77,140.90,37.83,141.01);  /* 森林 */
);
out center;
```

引数の順序は `(south, west, north, east)`。座標系は WGS84（EPSG:4326）。

---

## 方法2：Python（再現可能・複数エリア一括）

本リポジトリに再現用スクリプトがある。

| ファイル | 内容 |
|---------|------|
| `resources/osm_coordinate.py` | Overpass API から水域・森林を取得しCSVに出力 |
| `resources/osm_coordinates_results.csv` | 相馬市・南相馬市の取得結果（600件）|

### 実行方法

```bash
uv run python resources/osm_coordinate.py
```

スクリプト冒頭の `areas` リストで bbox を変更すれば、どの地域でも取得できる。

```python
areas = [
    ("soma", "相馬市 (ROI+松川浦+西丘陵)", (37.77, 140.90, 37.83, 141.01)),
    ("minamisoma", "南相馬市 東側クラスタ (ROI+新田川河口+海岸)", (37.60, 140.99, 37.66, 141.04)),
]
```

### 主要な処理（要点）

```python
import urllib.parse
import urllib.request

OVERPASS = "https://overpass-api.de/api/interpreter"

q = f"""
[out:json][timeout:90];
(
  nwr["natural"="water"]({south},{west},{north},{east});
  nwr["waterway"="river"]({south},{west},{north},{east});
  nwr["natural"="wood"]({south},{west},{north},{east});
  nwr["landuse"="forest"]({south},{west},{north},{east});
);
out center;
"""
data = urllib.parse.urlencode({"data": q}).encode()
req = urllib.request.Request(OVERPASS, data=data,
                             headers={"User-Agent": "astrocamp-research/1.0"})
result = json.load(urllib.request.urlopen(req, timeout=90))
```

- `nwr` は node / way / relation をまとめて検索する記法
- `out center;` で面の地物（way/relation）の中心座標を返す
- `urlencode({"data": q})` は POST 形式でクエリを送る（長いクエリも可）

---

## OSM のタグと意味

| タグ | 意味 | 取得で注意 |
|------|------|-----------|
| `natural=water` | 湖沼・ため池・池 | `water=reservoir` は溜池（ため池）を表す |
| `waterway=river` | 河川 | 面として `water=river` でマップされる場合もある |
| `waterway=stream` | 小河川・水路 | **数が非常に多い**ので別カテゴリに分けると集計しやすい |
| `natural=wood` | 樹林 | 丘陵林・海岸林 |
| `landuse=forest` | 森林（植林地） | 上と合わせて「森林」として扱う |

参考: `resources/osm_coordinate.py` では stream を除外・別分類して集計している。

---

## 取得結果の活用例（相馬市・南相馬市）

候補エリア選定ドキュメント `resources/候補エリア選定_相馬南相馬.md` に、以下のような参照座標を反映済み。

**相馬市 ROI 内:**
- 宇多川河道: (37.8008, 140.9385)
- 東側樹林: (37.7967, 140.9675)
- 参照: 松川浦 (37.8000, 140.9780)、松川浦沿岸クロマツ林 (37.8074, 140.9690)

**南相馬市 東側クラスタ ROI 内:**
- ため池（調整池）: (37.6120, 141.0083)、(37.6124, 141.0078)
- 樹林: (37.6157, 141.0143)
- 参照: 新田川河口 (37.6412, 141.0200)※要GEE確定

---

## 注意事項

- **季節的水面** — OSM で `water=river` とマップされた面の一部は**水田湛水（作付け期の水面）**を表すことがある。通年水面とは限らないため Sentinel-2 で確認する。
- **精度** — 座標の精度は地域により不均一。衛星画像・公的データと突き合わせて最終確認する。
- **対象外の除外** — 山間部の `natural=wood` は無数にある。ROI を絞ってクエリし、海岸平野の対象エリアに合う地物を選ぶ。
- **利用規約** — OSM データは ODbL ライセンス。公開成果物で使う場合は出典表示（© OpenStreetMap contributors）が必要。

---

## 参考リンク

- [Overpass API](https://overpass-api.de/) — クエリの公式仕様
- [overpass-turbo](https://overpass-turbo.eu/) — ブラウザで試す
- [OSM Wiki — Map features](https://wiki.openstreetmap.org/wiki/Map_features) — タグの一覧
- [データ準備ガイド](data-guide.md) — 衛星データ（GEE / JAXA Earth API）の取得方法
- [AIコーディングガイド](ai-coding-guide.md) — コード生成のプロンプト集
