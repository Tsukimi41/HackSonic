# 参加者ワークフロー

## 前提環境

このワークフローを進めるには、以下のいずれかの環境が必要です。

### A. Google Colab（推奨・準備不要）
ブラウザだけで動作します。Google アカウントがあればすぐに始められます。
Colab の開き方は [resources/github-guide.md](resources/github-guide.md) セクション5を参照。

### B. ローカル環境（VSCode など）
ローカルで作業する場合は、ターミナルで `git` コマンドが使える必要があります。
- **macOS:** 標準で `git` がインストールされています。ターミナル.app を使います。
- **Windows:** Git Bash（[git-scm.com](https://git-scm.com) からインストール）を使います。コマンドプロンプトや PowerShell ではなく **Git Bash** を使用してください。
- **Linux:** 標準で `git` が使えます。

> git のインストール方法や基本操作は [resources/github-guide.md](resources/github-guide.md) セクション4を参照。

## ブランチ構成

| ブランチ | 期間 | 役割 | 触れる人 |
|----------|------|------|---------|
| `main` | 通期 | 教材（演習テンプレート・プロジェクト資料） | メンターのみ |
| `submissions` | 通期 | 個人演習の提出 | 参加者全員 |
| `prelim-a` | 事前学習 | チームAの共同作業 | チームAのメンバー |
| `prelim-b` | 事前学習 | チームBの共同作業 | チームBのメンバー |
| `camp-alpha` | 合宿 | チームalphaのプロジェクト | チームalphaのメンバー |
| `camp-beta` | 合宿 | チームbetaのプロジェクト | チームbetaのメンバー |
| `camp-gamma` | 合宿 | チームgammaのプロジェクト | チームgammaのメンバー |

## ディレクトリ構成（全てのブランチ共通）

```
submissions/
├── individual/          ← 個人演習（submissions ブランチ）
│   └── _example/
│       └── week1.md
├── prelim/              ← 事前学習のチーム演習（prelim-* ブランチ）
│   ├── team-a/
│   └── team-b/
└── camp/                ← 合宿プロジェクト（camp-* ブランチ）
    ├── team-alpha/
    ├── team-beta/
    └── team-gamma/
```

---

## 個人演習（事前学習 毎週の課題）

**使うブランチ: `submissions`**

```bash
git switch submissions          # submissions ブランチに移動
git pull origin main            # 教材の最新版を取得
# submissions/individual/自分の名前/weekN.md を作成して回答を書く
git add submissions/individual/自分の名前/weekN.md
git commit -m "Week N の回答"
git push origin submissions     # submissions ブランチに提出
```

### Google Colab / Google Docs で提出する場合

演習ノートブック（Colab）やドキュメントで作成した場合は、**オリジナルのファイルをコピー**してから編集し、完成したファイルやリンクを Discord `#weekly-task` チャンネルに共有してください。

```python
# Colab でノートブックをコピーするには
# 1. 「ファイル」→「ドライブにコピーを保存」を選択
# 2. コピーしたファイルを編集する
```

> GitHub の用語がわからない場合は [resources/github-guide.md](resources/github-guide.md) を参照。

### 演習ノートブックの更新に対応する

教材の `exercises/week*_exercise.ipynb` が更新された場合、以下の手順で自分のブランチに取り込みます。すでにそのファイルを編集して回答を書き込んでいる場合は、競合（コンフリクト）が発生する可能性があります。

#### 事前準備：現在の変更をコミットする

```bash
git add exercises/week1_exercise.ipynb
git commit -m "提出用の回答を記入"
```

#### 手順

**1. 最新を取得**

```bash
git fetch origin
```

**2. main を自分のブランチにマージ**

```bash
git merge origin/main
```

競合がなければ自動で完了します。競合があると以下のメッセージが表示されます：

```
Auto-merging exercises/week1_exercise.ipynb
CONFLICT (content): Merge conflict in exercises/week1_exercise.ipynb
```

**3. 競合を解決する**

Notebook (.ipynb) は JSON 形式のため、目視での編集は困難です。以下のいずれかの方法で解決します。

**方法A: nbdime を使う（推奨）**

```bash
pip install nbdime
nbdime mergetool exercises/week1_exercise.ipynb
```

ブラウザが開き、左右に「自分の変更」と「main の変更」が比較表示されるので、どちらを採用するか選択します。

**方法B: 手動で解決する**

競合したファイルには以下のようなマーカーが挿入されます：

```
（自分の回答を書いたセル）
```

**基本方針：**
- 問題文や説明文が更新されている → `main` 側を採用
- 自分の回答（`???` を埋めた部分）はそのまま残す → `HEAD` 側を採用

不要なマーカー行（`<<<<<<<`, `=======`, `>>>>>>>`）を削除します。

**4. 解決したらコミット**

```bash
git add exercises/week1_exercise.ipynb
git merge --continue
```

エディタが開くので、そのまま保存して閉じます。

#### 一番簡単な方法（競合解決が難しい場合）

```bash
# 1. 今の回答をバックアップ
cp exercises/week1_exercise.ipynb exercises/week1_answers_backup.ipynb

# 2. 最新ファイルで上書き
git checkout origin/main -- exercises/week1_exercise.ipynb

# 3. バックアップを見ながら回答を新しいファイルに書き写す
```

この方法なら JSON の競合に悩まず、確実に回答を引き継げます。

---

## チーム演習（事前学習）

**使うブランチ: `prelim-a` または `prelim-b`**

チームメンバー全員が同じブランチで作業する。

```bash
git switch prelim-a             # 自分のチームのブランチに移動
git pull origin main            # 教材の最新版を取得
# submissions/prelim/team-a/ にチームの成果物を作成
git add submissions/prelim/team-a/
git commit -m "チーム演習 X 完了"
git push origin prelim-a        # チームブランチに提出
```

---

## 合宿プロジェクト

**使うブランチ: `camp-alpha` / `camp-beta` / `camp-gamma`**

```bash
git switch camp-alpha           # 自分のチームのブランチに移動
git pull origin main            # 教材の最新版を取得
# submissions/camp/team-alpha/ にプロジェクトの成果物を作成
git add submissions/camp/team-alpha/
git commit -m "プロジェクト更新"
git push origin camp-alpha      # チームブランチに提出
```

---

## 初回セットアップ（VSCode）

```bash
git clone https://github.com/astrocamp-2026-siaPpts/astrocamp-2026-sia.git
cd astrocamp-2026-sia
git config core.hooksPath .githooks       # 誤 push 防止フック

# 個人演習用: submissions ブランチに切り替え
git switch submissions
mkdir -p submissions/individual/自分の名前

# チーム演習用: 自分のチームのブランチに切り替え
# git switch prelim-a
```

## 初回セットアップ（Colab）

```python
from google.colab import drive
drive.mount('/content/drive')
%cd /content/drive/MyDrive
!git clone https://github.com/astrocamp-2026-siaPpts/astrocamp-2026-sia.git
%cd astrocamp-2026-sia
!git config core.hooksPath .githooks

# 個人演習用
!git switch submissions
!mkdir -p submissions/individual/自分の名前

# チーム演習用（切り替え）
# !git switch prelim-a
```

---

## 注意点

- **`main` には決して push しないこと。** pre-push hook が自動的にブロックする。
- 活動ごとに使うブランチが異なる。作業を始める前に `git switch` で正しいブランチにいるか確認する。
- チームブランチでは、同じチームのメンバーとファイルを共有する。他のチームのファイルを編集しないこと。
- `git pull origin main` は教材を取り込むだけで、自分の提出ファイルには影響しない。
