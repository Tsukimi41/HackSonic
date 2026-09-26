# 環境構築手順

## 必要環境

- **OS**: Linux / macOS / Windows いずれでも可
- **ブラウザ**: Google Chrome 推奨（Firefox / Edge でも可）
- **Googleアカウント**: 必須（GEE・Colab・Google Driveを使用するため）

## 使用ツール一覧

| ツール | 用途 | インストール |
|--------|------|-------------|
| Copernicus Browser | Sentinelデータ（S1・S2等）のブラウザ上での閲覧・ダウンロード | 不要（ブラウザ経由）※アカウント登録のみ |
| Google Earth Engine | 衛星データの取得・解析（Code Editor / Python API） | 不要（ブラウザ経由）※アカウント登録のみ |
| Google Colab | 実行環境（Python） | 不要（ブラウザ経由） |
| GitHub | 演習課題の提出・共有 | 不要（ブラウザ経由）※アカウント登録のみ |
| VSCode（任意） | ローカル編集（レポート・コード） | 推奨（任意） |
| QGIS（任意） | 画像の重ね合わせ表示 | 推奨（任意） |

## Copernicus Browser の登録と使い方

### アカウント登録

Copernicus Browser は ESA（欧州宇宙機関）の衛星データ（Sentinel-1・2・3等）をブラウザ上で閲覧・ダウンロードできるツールである。

1. [Copernicus Data Space](https://dataspace.copernicus.eu/) にアクセスする
2. 右上の「Login」→「Sign up」をクリックする
3. メールアドレス・氏名等を入力してアカウントを作成する
4. 確認メールのリンクをクリックして認証を完了する
5. [Copernicus Browser](https://dataspace.copernicus.eu/browser/) にアクセスし、ログインする

### 基本操作

1. 左上の検索バーに地点名（例: `Fukushima`）を入力して移動する
2. 右側のレイヤ一覧から可視化したいデータを選択する:
   - **Sentinel-2 L2A**: 光学画像（雲の少ないものを選ぶ）
   - **Sentinel-1 GRD**: SAR画像（偏波・観測方向を選べる）
3. 日付範囲は下部のタイムラインで調整する
4. 画像の上で右クリック → 「Show footprint info」でメタデータを確認できる
5. ダウンロードしたい領域をドラッグ選択し、「Download」ボタンから画像を取得する

### このゼミでの使いどころ

- 解析対象エリアの光学・SAR画像を目視で確認する
- 演習で使うデータを選定する際の事前調査
- GEE で取得したデータの見え方をブラウザ上の画像と比較する

## GEE の登録と使い方

### アカウント登録

1. [Google Earth Engine](https://earthengine.google.com/) にアクセスする
2. 右上の「Sign Up」からGoogleアカウントで登録する
3. 利用目的を入力する（「Education / Research」で可）
4. 承認メールが届くまで数時間〜1日程度かかる場合があるため、事前に余裕を持って登録すること

### Code Editor の基本操作

GEE にはブラウザ上でコードを書いて実行できる **Code Editor** がある。

1. [Code Editor](https://code.earthengine.google.com/) にアクセスする
2. 左側の **Search places or datasets** で地点またはデータセットを検索できる
3. 中央のエディタに JavaScript コードを書いて実行する（`Ctrl+Enter`）
4. 右側の **Inspector** タブで地図上のピクセル値をクリックして確認できる

**Code Editor の画面構成:**

```
┌─────────────────────────────────────────────┐
│  検索バー（データセット・地点）              │
├──────────┬──────────────────┬────────────────┤
│  Scripts │  コードエディタ   │  地図表示      │
│  （保存  │  （JavaScript）  │  （結果の      │
│   した   │                  │   可視化）     │
│   スク   │                  │               │
│   リプ   │                  │  Inspector     │
│   ト）   │                  │  Console       │
├──────────┴──────────────────┴────────────────┤
│  コンソール（出力・エラー表示）               │
└─────────────────────────────────────────────┘
```

### データカタログの使い方

1. Code Editor 左側の **Search** バーにデータセット名を入力する
   - 例: `Sentinel-2`、`USGS Landsat`、`JAXA ALOS`
2. 候補をクリックすると、データセットの説明・利用可能期間・バンド情報が表示される
3. 「Import」をクリックするとコードにデータセットが追加される

### よく使うデータセット

| データセット | ID |
|-------------|-----|
| Sentinel-2 MSI Level-2A | `COPERNICUS/S2_SR_HARMONIZED` |
| Sentinel-1 SAR GRD | `COPERNICUS/S1_GRD` |
| JAXA ALOS DSM | `JAXA/ALOS/AW3D30_V2_2` |

### Python API の利用（Colab / ローカル）

```python
import ee

# GEE の認証と初期化（初回のみブラウザでの認証が必要）
ee.Authenticate()
ee.Initialize(project='自分のプロジェクトID')

# ImageCollection を読み込む
collection = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED') \
    .filterDate('2024-04-01', '2024-09-30') \
    .filterBounds(ee.Geometry.Point(140.5, 37.5))
```

#### ローカル環境での認証手順

ローカルPCから `earthengine-api` を使う場合、以下の Cloud Project 設定が必要（Colab の場合は多くの設定が事前完了済みのためスキップ可）。

**Step 1: Cloud Project を Earth Engine 利用登録する**

Earth Engine を利用するプロジェクトを Cloud Console で登録する。

1. [Earth Engine Configuration](https://console.cloud.google.com/earth-engine/configuration?project=ee-astro2026-mk) にアクセスする（`ee-astro2026-mk` は実際のプロジェクトIDに置き換える）
2. 「Earth Engine の利用登録」または「Register Project」をクリック
3. 利用規約に同意する
4. プロジェクトが `Registered` 状態になるまで数分待つ

**Step 2: OAuth 同意画面を設定する**

1. [Google Cloud Console → OAuth 同意画面](https://console.cloud.google.com/apis/credentials/consent) にアクセスする
2. User Type は **「外部」** を選択し「作成」をクリック
3. 以下の項目を入力する：
   - アプリ名: `Astro Camp 2026`（任意）
   - サポートメール: 自分のメールアドレス
   - デベロッパー連絡先情報: 自分のメールアドレス
4. スコープ画面では「スコープを追加」→ `.../auth/earthengine` を選択して保存
5. テストユーザーに自分のメールアドレスを追加する

**Step 3: OAuth クライアントIDを作成する**

1. [Google Cloud Console → 認証情報](https://console.cloud.google.com/apis/credentials) にアクセスする
2. 「認証情報を作成」→「OAuth クライアントID」をクリック
3. アプリケーションの種類: **「デスクトップアプリ」** を選択
4. 名前: `GEE Local Client`（任意）
5. 「作成」をクリック（クライアントID/シークレットのJSONは**ダウンロード不要**）

**Step 4: GEE API を有効化する**

1. [Earth Engine API](https://console.developers.google.com/apis/api/earthengine.googleapis.com/overview) にアクセスする（プロジェクトが選択されていることを確認）
2. 「有効にする」をクリック
3. 有効化後、反映まで数分かかることがある

**Step 5: 認証を実行する**

```bash
python -c "import ee; ee.Authenticate()"
```

ブラウザが開くので、Google アカウントでログインしてアクセスを許可する。許可するとローカルに認証情報ファイル（`~/.config/earthengine/credentials`）が保存され、以降は自動で読み込まれる。

**Step 6: プロジェクトIDを保存する（一度だけ・推奨）**

次のコマンドを**一度だけ**実行しておくと、以降はプロジェクトIDの指定が不要になる。

```bash
earthengine set_project ee-astro2026-mk   # 自分のプロジェクトIDに置き換え
```

これで認証情報ファイルにプロジェクトIDが保存され、**素の `ee.Initialize()` が通るようになる**。

```python
import ee
ee.Initialize()      # project= を書かなくてよい
```

ノートブック・スクリプト・ターミナルのどこから実行しても効くので、
毎回プロジェクトIDを入力する手間がなくなる。**この方法を推奨する。**

> `gcloud` のインストールは不要。`earthengine` コマンドは
> `pip install earthengine-api` で一緒に入っている。

#### 方法B: コードに直接書く

```python
import ee
ee.Initialize(project='ee-astro2026-mk')  # 実際のプロジェクトIDに置き換え
```

#### 方法C: 環境変数で指定する

`tutorials/env.py` の `gee_setup()` はこの環境変数を読む。

```bash
export GEE_PROJECT=ee-astro2026-mk
```

設定後、コード側で環境変数を読み込む：

```python
import os
import ee

ee.Authenticate()
ee.Initialize(project=os.environ.get('GEE_PROJECT', ''))
```

#### トラブルシューティング

| エラー | 原因 | 対処 |
|--------|------|------|
| `project ... is not registered to use Earth Engine` | Cloud Project が Earth Engine 利用登録されていない | Step 1 の「Earth Engine Configuration」からプロジェクトを登録する |
| `Earth Engine API has not been used in project ...` | Earth Engine API が有効化されていない | Step 4 のリンクから API を有効化する |
| `ee_to_numpy() got multiple values for argument 'region'` | `geemap.ee_to_numpy()` の引数順が間違っている | `bands=` をキーワード引数で渡す（例: `geemap.ee_to_numpy(img, region=roi, bands=['B4', 'B3', 'B2'])`） |
| `no project found` | プロジェクトIDが指定されていない | **`earthengine set_project ee-xxx` を一度実行する**（推奨）。または `ee.Initialize(project='ee-xxx')` と書く |
| ブラウザ認証が毎回求められる | 保存された認証情報が期限切れ | `earthengine authenticate --force` で認証をやり直す（そのあと `earthengine set_project` を再実行する） |
| `set_project` したのに `no project found` | 認証をやり直して設定が消えた | `earthengine authenticate --force` の**あとに** `earthengine set_project` を実行する（順番が逆だと消える） |

**注意:** Colab 環境では多くの場合これらの設定が事前完了しているため、`ee.Authenticate()` と `ee.Initialize()` だけで動作する。ローカル環境でのみ上記手順が必要。

## JAXA Earth API（参考）

[JAXA Earth API for Python](https://data.earth.jaxa.jp/api/python/v0.1.6/ja/) は、JAXA の衛星データ（ALOS 標高、GSMaP 降水量、MODIS NDVI 等）にアクセスできる Python ライブラリである。

### GEE との違い

| 項目 | GEE | JAXA Earth API |
|------|-----|----------------|
| 認証 | Cloud Project 登録 + OAuth 必須 | **不要** |
| 光学画像 | Sentinel-2 (10m) など高解像度 | MODIS (250m〜1km) 中心 |
| 強み | データ種類が豊富、高解像度光学 | 日本の衛星データ（ALOS, GSMaP）に特化 |
| 構文 | `ee.ImageCollection().filter()` チェイン | `je.ImageCollection().filter()` チェイン |

### インストール

```bash
pip install jaxa-earth
```

GEE のような事前のプロジェクト登録や認証は不要。

### 最小限の使用例

```python
from jaxa.earth import je

# ALOS 標高データの取得
bbox = [140.5, 37.2, 141.2, 37.8]
data = je.ImageCollection("JAXA.EORC_ALOS.PRISM_AW3D30.v3.2_global") \
         .filter_date(["2021-01-01T00:00:00", "2021-01-01T00:00:00"]) \
         .filter_resolution(ppu=360) \
         .filter_bounds(bbox=bbox) \
         .select("DSM") \
         .get_images()

# 画像の表示
img = je.ImageProcess(data).show_images()
```

**補足:** SSL エラーが発生する場合は `ssl_verify=False` を設定する。詳細は `tutorials/jaxa_intro.ipynb` を参照。

## Colab の基本操作

1. [Google Colab](https://colab.research.google.com/) にアクセス
2. Googleアカウントでログイン
3. 「ファイル」→「ノートブックを新規作成」で新しいノートブックを作成
4. コードセルにPythonコードを記述し、実行ボタン（▶）をクリック

### Private GitHub リポジトリからノートブックを開く

このゼミのリポジトリは Private 設定のため、バッジからの直接開封ができない場合がある。
以下の手順で Colab から開くこと。

1. [Google Colab](https://colab.research.google.com/) にアクセス
2. 「ファイル」→「ノートブックを開く」→「GitHub」タブを選択
3. 「プライベート リポジトリを含める」にチェックを入れる
4. 初回のみ GitHub 認証が表示されるので「Sign in with GitHub」から許可
5. リポジトリ `astrocamp-2026-siaPpts/astrocamp-2026-sia` を選択
6. 開きたいノートブック（例: `exercises/week1_exercise.ipynb`）をクリック

### Google Drive のマウント

Colab から Google Drive 上のファイルを読み書きするには以下のコードを実行する。

```python
from google.colab import drive
drive.mount('/content/drive')
```

初回は認証リンクが表示されるので、Google アカウントでログインして認証コードをコピー・貼り付けする。マウント後は `/content/drive/MyDrive/` 以下にアクセスできる。

```python
# マウント確認
!ls /content/drive/MyDrive/
```

データの保存と管理の詳細は [データ準備ガイド](data-guide.md) を参照すること。

**注意:** Colabのランタイムは一定時間操作がないと切断される。長時間の解析はGEEのエクスポート機能を使ってGeoTIFFとして保存すること（保存先は Google Drive 推奨）。

## GitHubの設定

1. [GitHub](https://github.com/) にアカウント登録
2. リポジトリURLが共有されたら、各自クローンまたはブラウザからアクセス
3. 演習課題の提出方法は **WORKFLOW.md** を参照すること

## ローカル環境構築（任意）

Colab を使わず、自分の PC で Python コードを実行したい場合は `uv` を使って環境を構築できる。

### uv のインストール

**macOS（Homebrew）:**
```bash
brew install uv
```

**上記以外:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 環境構築

リポジトリのルートディレクトリで以下を実行する。

```bash
uv sync
```

`uv sync` は以下の処理を自動で行う。
- `.venv/` ディレクトリに仮想環境を作成
- `pyproject.toml` に書かれた依存パッケージをすべてインストール
- バージョンを `uv.lock` に固定する

### VSCode で仮想環境を使う

1. VSCode でリポジトリを開く
2. `Cmd+Shift+P`（macOS）/ `Ctrl+Shift+P`（Windows）でコマンドパレットを開く
3. `Python: Select Interpreter` を選択
4. `.venv/bin/python`（macOS）または `.venv/Scripts/python.exe`（Windows）を選ぶ

以降、ターミナルや Python ファイルの実行はすべてこの仮想環境が使われる。

### Colab との使い分け

- 基本的な解析コード（numpy, pandas, matplotlib, earthengine-api, geemap）はローカル環境でも動く
- `google.colab` を import するコード（Google Drive のマウントなど）は Colab 専用なので注意する
- GEE の認証はローカルでは `ee.Authenticate()` を一度実行すればよい

## 推奨ブラウザ拡張

- **uBlock Origin**: Colabの広告を非表示にできる（任意）

## トラブルシューティング

| 症状 | 対処 |
|------|------|
| Copernicus Browser にログインできない | アカウント登録が完了しているか確認する。登録から認証メールが届くまでに時間がかかる場合がある |
| Copernicus Browser でデータが表示されない | 日付範囲とクラウドカバレッジのフィルタを確認する。該当期間にデータがない場合は範囲を広げる |
| GEEにログインできない | Googleアカウントの連携を確認。登録から承認に時間がかかる場合は講師に連絡 |
| GEE Code Editor でエラーが出る | 右側の Console タブにエラー詳細が表示される。データセットIDや日付範囲が正しいか確認する |
| GEE Python API で `ee.Initialize()` が通らない | Cloud Project の設定が必要な場合がある。`ee.Initialize(project='プロジェクトID')` を試す |
| Colabでエラーが出る | ランタイム→「ランタイムを再起動」を試す。それでも解決しない場合はDiscordで相談 |
| データがダウンロードできない | 合宿前のWeek 8までにデータキャッシュを完了する。当日の通信障害に備えてフォールバックデータセットも用意 |
