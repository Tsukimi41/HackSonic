# Tutorials — ハンズオンノートブック

Colab で開いてそのまま実行できるノートブックを用意している。

## 一覧

| # | タイトル | 内容 | 開く |
|---|---------|------|------|
| 00 | GEE からのデータ読み込みと可視化 | GEE 認証・Sentinel-2 の読み込み・NDVI 計算・地図表示 | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/astrocamp-2026-siaPpts/astrocamp-2026-sia/blob/main/tutorials/00_example_gee.ipynb) |
| 01 | JAXA Earth API で学ぶ衛星データ | JAXA Earth API を使って衛星データを検索・取得・可視化するハンズオン | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/astrocamp-2026-siaPpts/astrocamp-2026-sia/blob/main/tutorials/jaxa_intro.ipynb) |
| — | 生成AIでGISコードを書く — 実践ワークフロー | AIをコーディングパートナーに使ってGEE・JAXA Earth APIのコードを生成・検証・デバッグする一連の流れを体験 | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/astrocamp-2026-siaPpts/astrocamp-2026-sia/blob/main/tutorials/00_ai_assisted_gis.ipynb) |
| 02 | 公共データの取得と前処理（S2/S1+e-Stat） | 最終課題向け: 相馬・南相馬のROI設定・サンプル農地ポリゴン作成・NDVI/VH時系列抽出・耕地面積統計でのクロスチェック | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/astrocamp-2026-siaPpts/astrocamp-2026-sia/blob/main/tutorials/02_public_data_gee.ipynb) |
| 03 | 機械学習で作付／休耕を判別（scikit-learn） | 時系列→特徴量行列・疑似ラベル×RandomForest・KMeansクラスタリング・IsolationForest異常検知・疑似ラベルの循環の罠・派生特徴量・精度評価（F1/P/R/IoU＋目視検証セット）・閾値感度分析・ピクセルvs一筆・確信度/グレーゾーン・**正解データの設計と時空間リーク（field_id分割）・誤分類の物理診断** | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/astrocamp-2026-siaPpts/astrocamp-2026-sia/blob/main/tutorials/03_machine_learning.ipynb) |
| 04 | 一筆解析パイプラインを組み立てる（W6） | 農水省筆ポリゴンを読み込み → GEE（reduceRegions）で一筆ごとにS2/S1の月別平均を集計 → 波形特徴量14種を計算 → `field_features.csv`／`fields.geojson` を保存（次の05へ渡す） | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/astrocamp-2026-siaPpts/astrocamp-2026-sia/blob/main/tutorials/04_field_pipeline.ipynb) |
| 05 | 結果を地図に落とす（W8） | 04の成果物を判別 → 緑=作付／赤=休耕疑い／灰=要確認の判別マップ・確信度マップ・要確認優先リスト（CSV）・GeoPackage/Shapefile 出力・再現性ヘッダ設定ブロック例 | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/astrocamp-2026-siaPpts/astrocamp-2026-sia/blob/main/tutorials/05_result_map.ipynb) |

## 再現性のための規約

解析の前提をコードに残し、「誰が実行しても同じ結果になる」ことを確保する。

1. **ノートは番号付きで順に実行できる構成にする**
   `01_download → 02_preprocess → 03_feature_engineering → 04_classification → 05_validation`
2. **解析前提はノート冒頭の「再現性ヘッダ設定ブロック」に1か所にまとめる**
   使用期間・AOI・衛星/コレクション・軌道方向・偏波・雲閾値・バンド・ルール閾値・圃場ポリゴン・検証データ・乱数seed・出力ファイル名（実例は `05_result_map.ipynb` を参照）
3. **中間成果物はファイルに保存し、次工程に渡す**
   例: `field_features.csv`／`fields.geojson`／`validation_labels.csv`（04 → 05 の受け渡し）
4. **乱数には固定seedを使い、ランダム要素は再現可能にする**

## 共通モジュール: `satellite_utils.py`

前処理の「物理ガード」関数集。03 ノートで import して使う。

Colab で使うには、このファイルをノートと同じランタイム（`/content`）へ
「ファイル → アップロード」で追加してから、ノート内のセルで

```python
from satellite_utils import assert_no_double_db, assert_ndvi_bands, ...
```

| 関数 | 検査・処理 |
|---|---|
| `assert_no_double_db(vh)` | S1_GRD の VH が dB（-40〜0）のままか（二重変換の防止） |
| `assert_ndvi_bands(bands)` | NDVI のバンドが NIR(B8)/Red(B4) か（RedEdge(B5) の誤用検出） |
| `check_orbit_uniform(collection)` | S1 の軌道方向（ASC/DESC）が時系列で統一されているか |
| `check_crs_consistency(images)` | 光学・SAR・ポリゴンの CRS（EPSG）が揃っているか |
| `s2_cloud_mask(img)` | Sentinel-2 の雲マスク（GEE 用） |
| `speckle_filter(img)` | SAR スペックル低減の平滑化（GEE 用） |

## 共通モジュール: `env.py`（Colab / ローカル両対応）

ノートブックが **Google Colab でも、自分のパソコン（VSCode / JupyterLab）でも**
同じように動くようにするためのヘルパーです。

- **Colab で使う場合**: `env.py` をノートと同じランタイム（`/content`）へアップロードして使う（`satellite_utils.py` と同じ扱い）
- **ローカルで使う場合**: `tutorials/env.py` に置いたまま使える（追加作業なし）
- **パスは環境変数で上書き可能**: `ASTROCAMP_DATA_DIR`（データ置き場）・`ASTROCAMP_POLYGON_PATH`（筆ポリゴン）・`GEE_PROJECT`（GEE プロジェクトID）

| 関数 | 動作 |
|---|---|
| `gee_setup()` | GEE の認証・初期化。既存の認証があればブラウザを開かない |
| `setup_font()` | matplotlib の日本語フォントを OS 別に自動設定 |
| `data_dir()` | データ・成果物のルート（Colab=Drive / ローカル=`tutorials/data/`） |
| `polygon_path()` | 筆ポリゴンのパス（ローカルは `tutorials/data/fukushima_polygons.geojson`） |

## ローカルで動かす場合

Colab を開けなくても、自分のパソコンでノートを動かせます。

1. **環境**: Python 3.10+ と Jupyter（VSCode の Jupyter 拡張 ／ JupyterLab）を準備
2. **依存**: 各ノート先頭の `!pip install ...` セルをそのまま実行（Jupyter なら `!pip` が動く）
3. **GEE 認証**: `env.gee_setup()` が処理。初回のみブラウザで認証、2回目以降は既存の認証を使う
4. **データの場所**: ローカルでは `tutorials/data/` を使う。筆ポリゴンのサンプル
   （`tutorials/data/fukushima_polygons.geojson`）を同梱しているので、04 は Drive なしでも試せる
5. **日本語フォント**: `env.setup_font()` が macOS（Hiragino）/ Windows（Yu Gothic）/ Linux（Noto）を自動選択

> ノート実行で生成される成果物（`field_features.csv`・`fukushima_field_results.*` など）は
> コミット対象外（`.gitignore` に登録済み）。チームの成果物は `submissions/camp-*` ブランチへ提出。

## 使い方

各ノートブックの **Open in Colab** バッジをクリックすると、Google Colab 上で直接開く。あとはセルを上から順に実行するだけで良い。ローカルで動かす場合は上の「ローカルで動かす場合」を参照。
