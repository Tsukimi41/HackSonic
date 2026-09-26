# メンターガイド — 演習確認・教材更新・PR 運用

ゼミのメンター・企画者向け。リポジトリの運用方法と参加者の提出物の確認手順をまとめる。

---

## 1. ブランチ戦略（おさらい）

| ブランチ | 役割 | 更新者 |
|----------|------|--------|
| `main` | 教材の正本（演習テンプレート・プロジェクト資料・各種ガイド） | メンターのみ |
| `submissions` | 参加者の個人演習提出先 | 参加者全員 |
| `prelim-a` / `prelim-b` | 事前学習チーム演習 | 各チームメンバー |
| `camp-alpha` / `beta` / `gamma` | 合宿プロジェクト | 各チームメンバー |

**原則:** `main` はメンターだけが直接操作する。参加者は `submissions` または各チームブランチで作業する。

---

## 2. 教材の更新（main ブランチ）

### 演習テンプレートの更新

```bash
git switch main
git pull origin main

# exercises/week1.md などを編集
# または exercises/ に新しいファイルを追加

git add exercises/
git commit -m "Week 3 の演習テンプレートを追加"
git push origin main
```

教材を更新したら、参加者ブランチにも反映する必要がある。

```bash
# 全ブランチに main の変更をマージする
for branch in submissions prelim-a prelim-b camp-alpha camp-beta camp-gamma; do
  git switch "$branch"
  git merge main --no-edit
  git push origin "$branch"
done
git switch main
```

**注意:** `main` を更新したら速やかに全ブランチにマージすること。参加者が `git pull origin main` で最新教材を取得できるようになる。

### 下書き・正解の管理（`_private/`）

`_private/` ディレクトリは `.gitignore` で除外されており、`main` ブランチには push されない。
参加者からは見えない状態で教材の下書き・講師用正解を管理するために使う。

| ファイル | 用途 | 参加者への見せ方 |
|---------|------|----------------|
| `_private/01_kogaku.ipynb` | 演習ノートの **正解**（全コード完成版） | 参加者が自力で詰まった場合に「答え合わせ」として参照を許可する |
| `_private/week1_exercise.ipynb` | **演習用ノート**（`???` の穴埋め版） | 本番では `exercises/week1_exercise.ipynb` として参加者ブランチに配置する |
| `_private/slide-content.md` | 講義スライドのテキスト案 | スライド完成後は不要 |
| `_private/slide-images/generate_all.py` | スライド用画像の自動生成スクリプト | — |
| `_private/slide-images/slide-*.png` | 生成されたスライド画像（計8枚） | 講義スライドに組み込んで使用 |

**運用フロー:**

1. メンターが `_private/` 内で演習ノートの正解（`01_kogaku.ipynb`）を編集する
2. その正解を元に、穴埋め版の演習ノート（`week1_exercise.ipynb`）を作成する
3. 公開準備ができたら演習ノートを `exercises/` にコピーしてコミットする：
   ```bash
   cp _private/week1_exercise.ipynb exercises/week1_exercise.ipynb
   git add exercises/week1_exercise.ipynb
   git commit -m "Add Week 1 exercise notebook"
   git push origin main
   ```
4. `_private/` 自体は gitignore されているので push されない

**注意:** ローカルで `_private/` を編集しても `git status` に表示されない。必要に応じて `git status --ignored` で確認する。

### 更新してはいけないもの

- `submissions/` 内の参加者のファイル（ディレクトリ構造のみ管理する）
- `tutorials/` 内のノートブック（内容の更新は可）
- 保護フック `.githooks/pre-push`（削除・変更しない）

---

## 3. 個人演習の確認（submissions ブランチ）

### 提出状況の確認

```bash
git switch submissions
git pull origin submissions

# 参加者ごとの提出ファイルを一覧
ls submissions/individual/

# 特定の週の提出を確認
ls submissions/individual/*/week1.md
```

ブラウザでも確認できる。GitHub で `submissions` ブランチを選択し、`submissions/individual/` を開く。

### 確認のポイント

- テンプレート `exercises/template.md` の各セクションが埋められているか
- 自分自身の回答が記述されているか（最低限）
- AI を使った場合は修正点・検証結果が記録されているか
- ファイル名が正しいか（`weekN.md`）

### フィードバックの方法

提出物に対するコメントは以下の方法で行う。

**方法1: GitHub 上で直接コメント（おすすめ）**
1. GitHub で該当ファイルを開く
2. 行番号をクリックして「Add a comment」
3. レビューコメントを書く

**方法2: 別途チャット（Discord 等）で伝える**
口頭やチャットで伝える。リポジトリ外のコミュニケーション。

---

## 4. チーム演習の確認（prelim-* ブランチ）

```bash
git switch prelim-a
git pull origin prelim-a

# チームの成果物を確認
ls submissions/prelim/team-a/
```

事前学習のチーム演習は各チームブランチで行われる。必要に応じてブランチを切り替えて確認する。

---

## 5. 合宿プロジェクトの確認（camp-* ブランチ）

```bash
git switch camp-alpha
git pull origin camp-alpha

# プロジェクト成果物を確認
ls submissions/camp/team-alpha/
```

合宿中は各チームが `camp-*` ブランチで作業する。リアルタイムでの確認が必要な場合は、適宜ブランチを pull して最新状態を追う。

---

## 6. Pull Request の運用（任意）

このゼミでは必須ではないが、以下のケースで PR を使うと便利である。

### 使うと便利なケース

- **チームメンバー間のコードレビュー:** 合宿プロジェクトで、メンバー同士で変更を確認したいとき
- **メンターへの提出:** 成果物をメンターがレビューしてからマージしたいとき
- **教材の修正提案:** 企画者以外が `main` の教材を修正したいとき

### PR の流れ（メンター視点）

1. 参加者またはメンターが PR を作成する
2. PR の「Files changed」タブで差分を確認する
3. 問題なければ「Review changes」→「Approve」
4. 「Merge pull request」でマージする

### 気をつけること

- `main` への PR は参加者からは作成できない（ブランチ保護ルールがある場合は除く）
- チームブランチ（`prelim-*` / `camp-*`）への PR はチーム内で自由に行える

---

## 7. submissions → main のマージ（任意）

定期的に `submissions` ブランチの変更を `main` に取り込むと、提出物が `main` からも参照できるようになる。

```bash
git switch main
git pull origin main
git merge submissions --no-edit
git push origin main
```

**タイミングの目安:** 週1回、演習の締切後。または合宿終了後。

---

## 8. チェックリスト

### 各週の演習確認

- [ ] `submissions/individual/` に参加者全員のファイルがあるか
- [ ] ファイル名が `weekN.md` になっているか
- [ ] テンプレートの全セクションが記入されているか
- [ ] AI を使った場合、検証・修正点が記録されているか
- [ ] 物理的に誤った記述がないか（NDVI の値域・バンド番号など）

### 教材更新時

- [ ] `main` の変更を全ブランチにマージしたか
- [ ] 参加者が `git pull origin main` で取得できる状態か
- [ ] 新しい演習ファイルは `exercises/` に配置したか

### 合宿前

- [ ] 全ブランチが `main` の最新状態を反映しているか
- [ ] `camp-*` ブランチが存在し、各チームに割り当て済みか
- [ ] 参加者が自分のチームブランチを認識しているか

---

## 9. よくある質問

**Q. 参加者が `main` に push しようとしてエラーになったと言ってきたら？**
A. 正常な動作である。`git push origin submissions` または適切なチームブランチを使うよう伝える。

**Q. 参加者の提出ファイルが見つからない。**
A. `submissions` ブランチが選択されているか確認する。`main` ブランチには提出ファイルは存在しない。

**Q. 教材を更新したのに参加者に反映されない。**
A. `main` の変更を全ブランチにマージしたか確認する。参加者は `git pull origin main` で取得する。

**Q. submissions ブランチのファイルを直接修正しても良いか。**
A. 必要最小限にとどめる。どうしても修正が必要な場合、ファイルのオーナー（提出した参加者）に連絡してから行う。

**Q. 誤って参加者のファイルを削除してしまった。**
A. `git checkout <前のコミットハッシュ> -- ファイルパス` で復元できる。わからなければ講師に連絡する。
