# -*- coding: utf-8 -*-
"""
env.py — Colab / ローカルの両対応ヘルパー（tutorials 共通）
=============================================================
衛星データ解析ゼミのノートブックが **Google Colab でも、自分のパソコン（VSCode /
JupyterLab など）でも**同じように動くようにするための共通関数群です。

使い方（各ノートブックのセットアップセル）
-----------------------------------------
```python
from env import gee_setup, setup_font, data_dir, polygon_path

gee_setup()          # GEE の認証・初期化（既存認証があればブラウザは開かない）
setup_font()         # matplotlib の日本語フォントを OS 別に自動設定
DATA_DIR = data_dir()            # データ置き場（Colab=Drive / ローカル=tutorials/data）
POLY_PATH = polygon_path()       # 筆ポリゴンへのパス（環境変数で上書き可）
```

注意
----
- **Colab で使う場合**: このファイル（`env.py`）をノートと同じランタイム
  （`/content`）へ「ファイル → アップロード」で追加してください。
  （`satellite_utils.py` と同じ扱いです）
- **ローカルで使う場合**: `tutorials/` に置いたまま使えます。追加作業は不要です。
- パスは環境変数 `ASTROCAMP_DATA_DIR` / `ASTROCAMP_POLYGON_PATH` で上書きできます。
"""

import os
import sys
import getpass


def in_colab():
    """Google Colab 上で動いているかどうか。"""
    return 'google.colab' in sys.modules


def is_local():
    """ローカル環境（Colab 以外）で動いているかどうか。"""
    return not in_colab()


def repo_root():
    """このファイル（tutorials/env.py）から見たリポジトリルート。"""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def data_dir():
    """データ・成果物のルートディレクトリ。

    - Colab: `/content/drive/MyDrive/astrocamp-2026`（Google Drive マウント先）
    - ローカル: 環境変数 `ASTROCAMP_DATA_DIR` → なければ `tutorials/data/`
    """
    if in_colab():
        return '/content/drive/MyDrive/astrocamp-2026'
    d = os.environ.get('ASTROCAMP_DATA_DIR')
    if d:
        return d
    return os.path.join(repo_root(), 'tutorials', 'data')


def ensure_dir(path):
    os.makedirs(path, exist_ok=True)
    return path


def polygon_path(filename='fukushima_polygons.geojson'):
    """筆ポリゴンのパス。環境変数 `ASTROCAMP_POLYGON_PATH` で上書き可能。

    - Colab: `/content/drive/MyDrive/astrocamp-2026/export/farmland/...`
    - ローカル: `tutorials/data/fukushima_polygons.geojson`（動作確認用サンプル）
    """
    env = os.environ.get('ASTROCAMP_POLYGON_PATH')
    if env:
        return env
    if in_colab():
        return os.path.join(data_dir(), 'export', 'farmland', filename)
    return os.path.join(data_dir(), filename)


def gee_setup():
    """GEE の認証と初期化（Colab / ローカル両対応）。

    - 既に認証済み（`ee.Initialize()` が成功する）ならブラウザを開かずにそのまま使う
    - 未認証なら `ee.Authenticate()` で認証し、プロジェクトIDで初期化する
    """
    import ee

    GEE_PROJECT = os.environ.get('GEE_PROJECT')

    # ① まず既存の認証で初期化を試す（ローカルで認証済みの人はこれで通る）
    try:
        if GEE_PROJECT:
            ee.Initialize(project=GEE_PROJECT)
        else:
            ee.Initialize()
        print('GEE 初期化成功（既存の認証を利用）')
        return ee
    except Exception:
        pass

    # ② プロジェクトIDを確認（環境変数 → 手入力）
    if not GEE_PROJECT:
        try:
            GEE_PROJECT = getpass.getpass(
                'GEE プロジェクトIDを入力してください (例: ee-yourproject): ')
        except Exception:
            GEE_PROJECT = 'ee-yourproject'

    # ③ ブラウザ認証（初回のみ）→ 初期化
    print('GEE 認証を開始します（ブラウザが開きます。初回のみ）...')
    ee.Authenticate()
    try:
        ee.Initialize(project=GEE_PROJECT or None)
        print('GEE 初期化成功')
    except Exception as e:
        print(f'GEE 初期化エラー: {e}')
        print('プロジェクトIDが正しいか確認してください。')
    return ee


def setup_font():
    """matplotlib の日本語フォントを OS 別に自動設定する。

    - Colab: `fonts-noto-cjk` を導入
    - ローカル: macOS=Hiragino Sans / Windows=Yu Gothic / Linux=Noto Sans CJK JP
    """
    import platform
    import matplotlib
    import matplotlib.pyplot as plt
    import matplotlib.font_manager as _fm

    if in_colab():
        import subprocess
        subprocess.run(['apt-get', 'install', '-y', 'fonts-noto-cjk'],
                       capture_output=True)
        _fm._load_fontmanager(try_read_cache=False)

    _system = platform.system()
    _jp_candidates = {
        'Darwin': ['Hiragino Sans', 'AppleGothic'],
        'Windows': ['Yu Gothic', 'MS Gothic'],
    }.get(_system, ['Noto Sans CJK JP', 'IPAexGothic'])

    _found = [f for f in _jp_candidates
              if f in [x.name for x in _fm.fontManager.ttflist]]
    if _found:
        plt.rcParams['font.sans-serif'] = _found
    else:
        _alt = sorted(set(x.name for x in _fm.fontManager.ttflist
                          if any(c in x.name
                                 for c in ['Noto', 'IPA', 'Gothic', 'Yu', 'Hiragino'])))
        if _alt:
            plt.rcParams['font.sans-serif'] = _alt
    plt.rcParams['font.family'] = 'sans-serif'
    plt.rcParams['axes.unicode_minus'] = False

    _env = 'Google Colab' if in_colab() else 'VSCode / ローカル'
    print(f'実行環境: {_env} ／ 日本語フォント: {plt.rcParams["font.sans-serif"]}')


if __name__ == '__main__':
    print('in_colab :', in_colab())
    print('data_dir :', data_dir())
    print('polygon  :', polygon_path())
