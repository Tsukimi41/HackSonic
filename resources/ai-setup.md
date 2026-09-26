# 無料生成AIのセットアップ手順

このガイドでは、衛星データ解析のコーディングに使える無料の生成AIツールのセットアップ方法を解説する。

---

## 目次

- [Option A（推奨）: Google Colab + Gemini](#option-a推奨-google-colab--gemini)
- [Option B: VS Code + GitHub Copilot Free](#option-b-vs-code--github-copilot-free)
- [Option C: ブラウザAI + Colab の併用](#option-cブラウザai--colab-の併用)
- [Option D: opencode（ターミナル完結型）](#option-d-opencodeターミナル完結型)
- [JAXA Earth API のセットアップ](#jaxa-earth-api-のセットアップ)
- [VEGA Navigator の使い方](#vega-navigator-の使い方)
- [トラブルシューティング](#トラブルシューティング)

---

## Option A（推奨）: Google Colab + Gemini

**費用**: 無料
**環境構築**: 不要（ブラウザのみ）
**おすすめ度**: ⭐⭐⭐⭐⭐

Colab上でコードを書きながら、右側のGeminiパネルでAIに質問・コード生成を依頼できる。環境構築ゼロで最も手軽。

### セットアップ手順

1. [Google Colab](https://colab.research.google.com/) にアクセスする
2. Googleアカウントでログインする
3. 「ファイル」→「ノートブックを新規作成」をクリック
4. 右上の **Geminiアイコン（✨）** をクリックしてサイドパネルを開く
5. 「Gemini in Colab を試す」の案内が出たら「続行」をクリック

### 使い方の流れ

```
1. Geminiパネルに「Sentinel-2のNDVIを計算するコードを書いて」と入力
2. Geminiがコードを生成 → 「コードを挿入」ボタンでセルに追加
3. セルを実行して結果を確認
4. エラーが出たらエラーメッセージをGeminiに貼って修正を依頼
```

### 画面イメージ

```
┌──────────────────────────────────────┬──────────────┐
│                                      │  ✨ Gemini   │
│  コードエリア                        │              │
│                                      │ 「Sentinel-2│
│  [セル1] pip install geemap          │  のNDVIを   │
│  [セル2] import ee                   │  計算する   │
│  [セル3] ee.Authenticate()           │  コードを   │
│                                      │  書いて」   │
│                                      │              │
│                                      │ ↓            │
│                                      │              │
│                                      │ コード生成   │
│                                      │ [コードを    │
│                                      │  挿入]       │
└──────────────────────────────────────┴──────────────┘
```

---

## Option B: VS Code + GitHub Copilot Free

**費用**: 無料（GitHub Copilot Free プラン）
**環境構築**: VS Code + Python 環境が必要
**おすすめ度**: ⭐⭐⭐⭐

ローカルで開発したい場合におすすめ。コード補完（Tab補完）とチャット機能が使える。

### セットアップ手順

#### 1. VS Code のインストール

まだの場合は [code.visualstudio.com](https://code.visualstudio.com/) からダウンロードしてインストールする。

#### 2. Python 環境のセットアップ

リポジトリのルートディレクトリで以下を実行する。

```bash
# uv のインストール（まだの場合）
# macOS:
brew install uv
# その他:
curl -LsSf https://astral.sh/uv/install.sh | sh

# 仮想環境の作成とパッケージインストール
uv sync
```

#### 3. GitHub Copilot Free の有効化

1. VS Code を開く
2. 左側の拡張機能アイコン（🧩）をクリック
3. 「GitHub Copilot」を検索してインストール
4. インストール後、右下にGitHubログインを促すポップアップが表示されるので「Sign in to GitHub」をクリック
5. ブラウザが開くのでGitHubアカウントでログイン
6. 「Authorize Visual Studio Code」をクリック
7. VS Codeに戻る

**無料プランの確認:**
- GitHub Copilot Free は月2000回のコード補完 + 50回のチャットリクエスト
- 足りなくなったらChatGPT/Geminiと併用する

#### 4. 使い方

| 機能 | 操作方法 |
|------|---------|
| **コード補完** | コードを書き始めると灰色で候補が表示 → `Tab` キーで確定 |
| **チャット** | `Ctrl+Shift+I`（macOS: `Cmd+Shift+I`）でチャットパネルを開く |
| **インライン編集** | コードを選択して `Ctrl+I`（macOS: `Cmd+I`）でその場で修正依頼 |

---

## Option C: ブラウザAI + Colab の併用

**費用**: 無料
**環境構築**: 不要
**おすすめ度**: ⭐⭐⭐

別タブでAI（Gemini / ChatGPT）を開き、生成されたコードをColabにコピー＆ペーストする方式。一番シンプル。

### おすすめのAIツール

| AI | URL | 特徴 |
|----|-----|------|
| **Google Gemini** | gemini.google.com | 1Mコンテキスト。長いコードも扱える。 |
| **ChatGPT Free** | chat.openai.com | GPT-4o mini。使い慣れている人向け。 |
| **Bing Copilot** | copilot.microsoft.com | GPT-4ベースが完全無料。 |

### 効率化のコツ

1. **AI用タブを常に1つ開いておく** → Gemini/ChatGPTを常駐させる
2. **プロンプトは保存しておく** → うまくいったプロンプトはメモ帳などに残す
3. **コード生成 → Colabに貼り付け → 実行 → エラーをAIに貼り付け** のサイクルを回す

```
┌─────────────────┐     ┌─────────────────┐
│  Geminiタブ      │     │  Colabタブ       │
│                  │     │                  │
│ 「NDVIコードを  │ ──→ │ [セルに貼り付け] │
│   書いて」       │     │  ▶ 実行          │
│                  │ ←── │  エラー発生！    │
│ 「エラー原因は？」│     │                  │
└─────────────────┘     └─────────────────┘
```

---

## Option D: opencode（ターミナル完結型）

**費用**: 無料・OSS
**環境構築**: pip または brew でインストール
**おすすめ度**: ⭐⭐⭐⭐

opencode はターミナル上で動作するAIコーディングエージェント。コード生成からファイル編集、実行、デバッグまでを一貫して行える。VS Codeの統合ターミナル内で使うと効率的。

### セットアップ手順

```bash
# pip でインストール
pip install opencode

# または Homebrew（macOS）
brew install opencode
```

### 使い方の流れ

```bash
# ターミナルで自然言語で指示する
opencode "Sentinel-2のNDVIを計算するGEEのPythonコードを書いて"

# opencode がコードを生成・ファイルを作成・実行まで行う
# エラーが出たら自動的に修正を試みる
```

### このゼミでの活用シーン

| シーン | 使い方 |
|--------|--------|
| コード生成から実行までを一気に行いたい | ターミナルで `opencode "..."` と指示するだけで完結 |
| ファイル検索・grepと組み合わせたい | `opencode` 内で `glob`, `grep` を使って関連ファイルを探索しながらコードを書ける |
| VS Codeでの開発中に | 統合ターミナル（Ctrl+`）で opencode を起動し、編集とAI支援をシームレスに行う |

### 注意点

- 初回起動時に使用するAIモデルの設定が必要（環境変数または設定ファイル）
- 無料のAPI（Gemini API等）を使う場合は `OPENAI_API_KEY` や `GEMINI_API_KEY` の設定が必要
- 詳細は [opencode.ai](https://opencode.ai) を参照

---

## JAXA Earth API のセットアップ

JAXA Earth API はJAXAが提供する無料の衛星データアクセスAPI。Pythonライブラリ `jaxa-earth` で使える。

### インストール

```bash
pip install jaxa-earth
```

Colabの場合はコードセルに以下を書いて実行する。

```python
!pip install jaxa-earth
```

### 認証について

**JAXA Earth API はAPIキー不要（2026年現在）**。インストールするだけですぐに使える。

### 動作確認

```python
import jaxa_earth as je

catalog = je.Catalog()
print(catalog.list_collections())
```

### 対応データセット（主なもの）

| データセット | Collection ID | 内容 |
|-------------|---------------|------|
| ALOS AW3D30 DSM | `ALOS PRISM AW3D30 v3.2` | デジタル標高モデル（30m） |
| ALOS-2 PALSAR-2 FNF | `ALOS-2 PALSAR-2 FNF v2.1.0` | 森林/非森林マップ |
| GCOM-C SGLI NDVI（月次） | `GCOM-C SGLI NDVI v3 monthly` | 植生指数 |
| GCOM-C SGLI LST（日次） | `GCOM-C SGLI LST v3 daily` | 陸域表面温度 |
| GSMaP 降水量（日次） | `GSMaP Gauge v6 daily` | 降水量 |
| MODIS NDVI（月次） | `JASMES MODIS NDVI v811` | 植生指数（MODIS） |

### 注意点

- 一度に取得できる範囲に上限がある（広すぎるとエラーになる）
- データによって利用可能な期間が異なる
- COG（Cloud Optimized GeoTIFF）形式で提供される

---

## VEGA Navigator の使い方

VEGA Navigator はRESTECが提供する **ChatGPTのカスタムGPT**。VEGAの操作方法について質問できる。

### アクセス手順

1. 以下のURLにアクセスする: [VEGA Navigator](https://chatgpt.com/g/g-681ae85dd9608191b398629f9f4adb12-vega-navigator)
2. OpenAIのアカウントでログインする（無料アカウントでOK）
3. チャット画面が開くので、VEGAの使い方に関する質問を入力する

### 質問例

| 質問 | 補足 |
|------|------|
| 「VEGAで福島の農地を表示したい」 | 地点の指定方法やズームレベルも教えてくれる |
| 「NDVIのカラー合成設定を教えて」 | バンド選択やカラーパレットの設定手順 |
| 「SAR画像を表示するには？」 | VEGAでSARを扱う場合の制約など |
| 「2時期の差分を見たい」 | 日付範囲の設定とReducerの選び方 |

### 制約

- **VEGA Navigator はVEGAの使い方専用**（GEEのコード生成はできない）
- 回答は ChatGPT によって生成されるため、**常に正確とは限らない**
- VEGA自体は **無料・ブラウザのみで利用可能**（アカウント登録不要）

---

## トラブルシューティング

### Colab + Gemini

| 症状 | 対処 |
|------|------|
| Geminiアイコンが出ない | Colabのランタイムを再起動する。それでも出なければColabのリージョン設定を確認 |
| Geminiがコードを生成しない | プロンプトをもう少し具体的にする。「コードを書いて」より「PythonでGEEのコードを書いて」のほうが通りやすい |
| 「利用できません」と出る | 時間をおいて再度試す。無料枠の制限に達した可能性 |

### GitHub Copilot Free

| 症状 | 対処 |
|------|------|
| 補完が出ない | VS Codeの右下にCopilotアイコンがあるか確認。「×」ならクリックして再有効化 |
| 「Free プランの制限に達しました」 | 月2000回の補完を使い切った。残りはChatGPT/Geminiで補う |
| サインインできない | GitHubアカウントで一度ブラウザログインしてから再試行 |

### JAXA Earth API

| 症状 | 対処 |
|------|------|
| `pip install jaxa-earth` が失敗する | Python 3.9以上が必要。`python --version` で確認 |
| データが取得できない | 範囲が広すぎる可能性。ROIを狭めて再試行 |
| どのデータセットがあるか知りたい | `je.Catalog().list_collections()` で一覧表示 |

### VEGA Navigator

| 症状 | 対処 |
|------|------|
| ログインできない | OpenAIアカウントを持っていない場合は [chatgpt.com](https://chatgpt.com/) で無料登録 |
| 回答が不正確に感じる | クリティカルな情報は利用マニュアルでも確認する |
| VEGA自体の使い方がわからない | [利用マニュアル(PDF)](https://rs-training.jp/from2022/wp-content/uploads/2025/05/VEGA2.2_Manual_Jp.pdf) も併読する |
