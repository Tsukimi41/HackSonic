# GitHub 入門ガイド — Astro Camp 2026

---

## 1. Git / GitHub とは

| 用語 | 説明 |
|------|------|
| **Git** | ファイルの変更履歴を管理するバージョン管理システム。誰が・いつ・何を変更したかを記録できる。 |
| **GitHub** | Git で管理したリポジトリをインターネット上で共有・共同編集するためのプラットフォーム。 |

このゼミでは **演習課題の提出** と **チームプロジェクトの共有** に GitHub を使う。

---

## 2. GitHub アカウント作成

1. [GitHub](https://github.com/) にアクセスする
2. 「Sign up」をクリックする
3. メールアドレス・パスワード・ユーザー名を入力する
4. 確認メールのリンクをクリックして認証を完了する

**ユーザー名の注意:** 後で使うので、英数字とハイフンのみのシンプルな名前にすると扱いやすい。

---

## 3. このリポジトリの構成

### ディレクトリ構成

```
astrocamp-2026-sia/
├── exercises/         演習テンプレート（読み取り専用）
├── submissions/       演習課題の提出先
│   ├── individual/    個人演習の提出 ← 自分のファイルをここに置く
│   │   └── _example/  提出フォーマットの見本
│   ├── prelim/        事前学習のチーム演習
│   └── camp/          合宿プロジェクト
├── project/           プロジェクト資料
├── resources/         資料類
└── README.md          コース概要
```

### ブランチ構成

| ブランチ | 期間 | 役割 | 触れる人 |
|----------|------|------|---------|
| `main` | 通期 | 教材 | メンターのみ |
| `submissions` | 通期 | 個人演習の提出 | 参加者全員 |
| `prelim-a` | 事前学習 | チームAの共同作業 | チームAのメンバー |
| `prelim-b` | 事前学習 | チームBの共同作業 | チームBのメンバー |
| `camp-alpha` | 合宿 | チームalphaのプロジェクト | チームalphaのメンバー |
| `camp-beta` | 合宿 | チームbetaのプロジェクト | チームbetaのメンバー |
| `camp-gamma` | 合宿 | チームgammaのプロジェクト | チームgammaのメンバー |

### 活動ごとのブランチ使い分け

| 活動 | 使うブランチ | 作業ディレクトリ |
|------|-------------|----------------|
| 個人演習（毎週の課題） | `submissions` | `submissions/individual/自分の名前/` |
| 事前学習チーム演習 | `prelim-a` または `prelim-b` | `submissions/prelim/team-a/` |
| 合宿プロジェクト | `camp-alpha` / `beta` / `gamma` | `submissions/camp/team-alpha/` |

---

## 4. VSCode で始める（推奨）

### 4-1. Git のインストール

| OS | インストール方法 |
|----|-----------------|
| macOS | ターミナルで `brew install git`、または https://git-scm.com からインストーラをダウンロード |
| Windows | https://git-scm.com からインストーラをダウンロードして実行。インストール時のオプションはデフォルトで良い |

インストール後、ターミナルで以下を実行して自分の情報を設定する。

```bash
git config --global user.name "自分のGitHubユーザー名"
git config --global user.email "登録したメールアドレス"
```

### 4-2. VSCode でリポジトリをクローンする

1. VSCode を開く
2. `Ctrl+Shift+P`（macOS: `Cmd+Shift+P`）でコマンドパレットを開く
3. `Git: Clone` と入力して選択する
4. リポジトリのURL `https://github.com/astrocamp-2026-siaPpts/astrocamp-2026-sia.git` を入力する
5. 保存先フォルダを選択する
6. 「Open」をクリックしてクローンしたリポジトリを開く

**初回のみ:** GitHub へのログインを求められたらブラウザが開くので「Continue」→「Authorize」で認証する。以降は自動で認証される。

### 4-3. submissions ブランチに切り替える（初回のみ）

クローン直後は `main` ブランチが選択されている。左下のブランチ名（`main`）をクリックし、`submissions` を選択して切り替える。またはターミナルで以下を実行する。

```bash
git switch submissions
```

### 4-4. pre-push hook を有効化する（初回のみ）

`main` への誤 push を未然に防ぐフックを有効にする。ターミナルで以下を実行する。

```bash
git config core.hooksPath .githooks
```

以降、`git push origin main` を実行すると自動的にブロックされる。

### 4-5. 教材の最新版を取得する（毎週のはじめに）

メンターが `main` ブランチに新しい教材を追加したら、以下の操作で自分の作業環境に取り込む。

**VSCode GUI:**
Source Control タブ → `...`（メニュー）→ **Pull, Push** → **Pull from...** → `origin/main`

**ターミナル:**
```bash
git pull origin main
```

### 4-6. ファイルを編集してコミット・プッシュする

1. 左のアクティビティバーから **Source Control** タブ（三又のアイコン）をクリックする
2. 変更したファイルの横の `+` をクリックしてステージングに追加する
3. 上部の入力欄にコミットメッセージを書く
4. `✓`（チェックマーク）をクリックしてコミットする
5. `...` → **Push** で GitHub にアップロードする（自動的に `submissions` ブランチにプッシュされる）

**こまめに Push する習慣をつけること。** ローカルにだけ保存していると、PCのトラブルで作業が消えるリスクがある。

---

## 5. Colab で始める

### 5-1. Personal Access Token (PAT) を発行する

Colab から GitHub にアクセスするには、パスワードの代わりに PAT を使う。

1. GitHub の右上のアイコン → **Settings**
2. 左下の「Developer settings」→ **Personal access tokens** → **Tokens (classic)**
3. 「Generate new token」→「Generate new token (classic)」
4. 以下の設定で作成する:
   - **Note:** `astrocamp-colab`（自分でわかる名前）
   - **Expiration:** カスタムでゼミ終了日以降に設定
   - **Select scopes:** `repo` にチェックを入れる
5. 生成されたトークンをコピーして安全な場所に保存する（この画面を離れると二度と表示されない）

### 5-2. Colab でリポジトリをクローンする

```python
# Google Drive をマウントする
from google.colab import drive
drive.mount('/content/drive')

# ドライブ上に移動する
%cd /content/drive/MyDrive

# クローンする
!git clone https://github.com/astrocamp-2026-siaPpts/astrocamp-2026-sia.git

# リポジトリのディレクトリに移動する
%cd astrocamp-2026-sia

# submissions ブランチに切り替える（初回のみ）
!git switch submissions

# pre-push hook を有効化する（main への誤 push を防止）
!git config core.hooksPath .githooks
```

初回の `git clone` 時にユーザー名とパスワードを求められる。

- **Username:** 自分の GitHub ユーザー名
- **Password:** 発行した PAT（画面に文字は表示されないが入力されている）

### 5-3. 教材の最新版を取得する（毎週のはじめに）

```python
!git pull origin main
```

### 5-4. 変更を保存してプッシュする

```python
# 変更状況を確認する
!git status

# 変更したファイルをステージングに追加する
!git add submissions/自分のユーザー名/week1.md

# コミットする
!git commit -m "Week 1 の演習回答を追加"

# プッシュする（submissions ブランチにプッシュされる）
!git push origin submissions
```

一度認証すれば、同じ Colab セッション内では再入力を求められない。

### 5-5. Colab の注意点

- ランタイムは一定時間で切断される。**こまめに `git push origin submissions` すること。**
- 切断された場合は再度クローンからやり直す。Google Drive 上にクローンしておけば次回も再利用できる。
- Google Drive にクローンすると、次回は以下のコマンドだけで作業を再開できる。

```python
%cd /content/drive/MyDrive/astrocamp-2026-sia
!git pull origin main        # 最新の教材を取得
!git pull origin submissions  # 前回の続きを取得
```

---

## 6. リポジトリの更新を受け取る

このリポジトリはメンターが随時更新する。新しい教材や修正が追加されたことを知るには、以下の2つの方法がある。

### 6-1. GitHub Watch — 通知を受け取る

Watch を設定すると、リポジトリに更新があったときに GitHub 上で通知が届く。

Watch ボタンには以下の状態がある:

| 状態 | 動作 |
|------|------|
| **Participating & @mentions** | 自分が参加中またはメンションされた会話のみ通知（デフォルト） |
| **All Activity** | すべてのアクティビティを通知 |
| **Custom** | 下記のチェックボックスで通知する項目を個別に選択 |
| **Ignore** | 一切通知しない |

1. リポジトリページ（https://github.com/astrocamp-2026-siaPpts/astrocamp-2026-sia）を開く
2. 右上の **Watch** ボタンをクリックする
3. **Custom** を選択する
4. 以下のチェックボックスで必要な項目をオンにする:

   | 項目 | おすすめ | 説明 |
   |------|---------|------|
   | Issues | ✅ | 課題や質問が投稿されたときに通知 |
   | Pull Requests | ✅ | 教材の変更がPRで管理されている場合に通知される |
   | Releases | ✅ | **新しい教材の追加や大きな変更があったときに通知される** |
   | Discussions | 任意 | ディスカッションの更新 |
   | Security Alerts | — | セキュリティ関連（常にON、変更不可） |

5. **Apply** をクリックして保存する

以降、選択した種類の更新があった場合に GitHub の通知アイコン（🔔）にバッジが表示される。

### 6-2. GitHub Release — 大きな変更を確認する

GitHub Release は「バージョンアップ」や「大きな教材追加」があったときに、変更内容をまとめて公開する機能。

1. リポジトリページ上部の **Releases** リンクをクリックする（`<> Code` の横あたり）
2. リリースの一覧が表示される。各リリースには以下の情報が含まれる:
   - **タイトル**: 何が追加されたか（例: 「Week 3 教材を追加」「AIコーディングガイドを公開」）
   - **タグ**: バージョン番号（例: `v1.0.0`）
   - **公開日**: いつ公開されたか
   - **リリースノート**: 変更内容の詳細
3. 気になるリリースがあればクリックして詳細を読む

**Watch と Release の併用がおすすめ:** Watch で Release の通知をオンにしておけば、新しい Release が公開されたときに自動で知らせてくれる。

---

## 7. 活動ごとの提出フロー

### 個人演習（事前学習 毎週の課題）

**使うブランチ: `submissions`**

```
① git switch submissions          # submissions ブランチに移動
② git pull origin main            # 教材の最新版を取得
③ submissions/individual/自分の名前/weekN.md を作成
④ git add submissions/individual/自分の名前/weekN.md
⑤ git commit -m "Week N の回答"
⑥ git push origin submissions     # 提出
⑦ ブラウザで GitHub を開き submissions ブランチの内容を確認
```

### チーム演習（事前学習）

**使うブランチ: `prelim-a` または `prelim-b`**

```
① git switch prelim-a             # 自分のチームのブランチに移動
② git pull origin main            # 教材の最新版を取得
③ submissions/prelim/team-a/ にチームの成果物を作成
④ git add submissions/prelim/team-a/
⑤ git commit -m "チーム演習 X 完了"
⑥ git push origin prelim-a        # チームブランチに提出
```

### 合宿プロジェクト

**使うブランチ: `camp-alpha` / `camp-beta` / `camp-gamma`**

```
① git switch camp-alpha           # 自分のチームのブランチに移動
② git pull origin main            # 教材の最新版を取得
③ submissions/camp/team-alpha/ にプロジェクト成果物を作成
④ git add submissions/camp/team-alpha/
⑤ git commit -m "プロジェクト更新"
⑥ git push origin camp-alpha      # チームブランチに提出
```

### コミットメッセージの書き方

「何を変更したか」がひと目でわかるメッセージを書く。

| 良い例 | 悪い例 |
|--------|--------|
| `Week 1 の演習回答を追加` | `update` |
| `NDVIの計算結果の誤りを修正` | `fix` |
| `グラフのラベルを日本語に変更` | `a` |

### なぜブランチを使い分けるのか

- `main` は教材の「正本」。メンターだけが更新する。
- `submissions` は個人の演習提出用。他の参加者と競合しない。
- チームブランチ（`prelim-a` など）はチーム内で閉じた作業スペース。他のチームに影響を与えずに共同作業できる。
- pre-push hook により、`main` への誤 push は自動的にブロックされる。

---

## 8. VSCode vs Colab 操作対応表

| 操作 | VSCode（GUI） | Colab（コマンド） |
|------|--------------|-------------------|
| クローン | `Ctrl+Shift+P` → `Git: Clone` | `!git clone <URL>` |
| ブランチ切替 | 左下のブランチ名をクリック → 目的のブランチ | `!git switch <ブランチ名>` |
| 教材を取得 | `...` → Pull from → `origin/main` | `!git pull origin main` |
| 状態確認 | Source Control タブに表示 | `!git status` |
| ステージング | ファイル横の `+` | `!git add ファイル名` |
| コミット | 入力欄にメッセージ → `✓` | `!git commit -m "メッセージ"` |
| hook 有効化 | ターミナルで `git config core.hooksPath .githooks` | `!git config core.hooksPath .githooks` |
| 個人演習を提出 | `...` → Push（`submissions` ブランチの場合） | `!git push origin submissions` |
| チーム演習を提出 | `...` → Push（チームブランチの場合） | `!git push origin prelim-a` |
| 合宿成果を提出 | `...` → Push（チームブランチの場合） | `!git push origin camp-alpha` |
| 履歴確認 | 左下のブランチ名 → コミット一覧 | `!git log --oneline` |

---

## 9. 発展編: Pull Request（任意）

PR（Pull Request）は「自分の変更をリポジトリに取り込んでほしい」と依頼する機能。チームプロジェクトで使う。

### PR の流れ

1. リポジトリを自分のアカウントに **Fork**（コピー）する
2. Fork した自分のリポジトリで変更を加える
3. 元のリポジトリに戻り、「Pull requests」→「New pull request」を開く
4. 変更内容を説明するコメントを書いて作成する
5. メンターやチームメンバーがレビューする
6. 問題なければ「Merge pull request」をクリックして変更を取り込む

---

## 10. よくあるトラブルと解決法

| 症状 | 原因と対処 |
|------|-----------|
| `git push` で認証エラーが出る | PAT が正しいか確認する。再発行して再試行する。 |
| `git clone` でエラーが出る | URL を確認する。`https://github.com/ユーザー名/リポジトリ名.git` の形式になっているか。 |
| `git push` が rejected になる | 間違ったブランチに push しようとしていないか確認する。個人演習なら `submissions`、チーム演習なら `prelim-a` など正しいブランチを指定する。 |
| `prelim-a` などのブランチが見つからない | `git fetch origin` でリモートのブランチ情報を取得してから `git switch prelim-a` を実行する。 |
| チームメイトの変更が見えない | `git pull origin <ブランチ名>` で最新の状態を取得する。 |
| 「ファイルが最新じゃない」と表示される | `git pull` で最新状態にしてから再度 push する。 |
| 間違えてコミットした | 該当ファイルを修正して再度コミット・プッシュすれば上書きされる。 |
| 教材（exercises/）が古い | `git pull origin main` を実行して最新の教材を取り込む。 |
| コンフリクト（競合）が起きた | 同じファイルの同じ行を複数人が同時に編集すると発生する。`git pull` で相手の変更を取り込み、両方の変更を残すよう手動で編集してからコミットする。 |
| トークンを忘れた | GitHub Settings → Developer settings → Personal access tokens で再発行する。 |
| 自分のフォルダがない | `submissions/` の下に自分のユーザー名のディレクトリを作成してから作業する。 |

---

## Appendices

### 主要 Git コマンド一覧

| コマンド | 意味 |
|----------|------|
| `git status` | 現在の変更状況を表示する |
| `git switch submissions` | `submissions` ブランチに切り替える |
| `git config core.hooksPath .githooks` | pre-push hook を有効化する（初回のみ） |
| `git pull origin main` | `main` ブランチの最新教材を取得する |
| `git add ファイル名` | 変更をステージングに追加する |
| `git commit -m "メッセージ"` | 変更をコミットする |
| `git push origin submissions` | 個人演習を `submissions` ブランチに提出する |
| `git push origin prelim-a` | チーム演習を `prelim-a` ブランチに提出する |
| `git push origin camp-alpha` | 合宿成果を `camp-alpha` ブランチに提出する |
| `git pull origin <ブランチ名>` | 指定したブランチの最新を取得する |
| `git fetch origin` | リモートの全ブランチ情報を取得する |
| `git log --oneline` | コミット履歴を1行ずつ表示する |

### 参考リンク

- [GitHub Docs: アカウント作成](https://docs.github.com/ja/get-started/start-your-journey/creating-an-account-on-github)
- [GitHub Docs: Personal Access Token](https://docs.github.com/ja/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens)
- [GitHub Docs: Pull Request](https://docs.github.com/ja/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/about-pull-requests)
- [GitHub Docs: Watching リポジトリ](https://docs.github.com/ja/account-and-profile/managing-subscriptions-and-notifications-on-github/setting-up-notifications/configuring-notifications#about-watching-a-repository)
- [GitHub Docs: Release について](https://docs.github.com/ja/repositories/releasing-projects-on-github/about-releases)
