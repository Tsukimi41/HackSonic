"""Colab / GEE 実行環境の共通セットアップ。

他のスクリプト（01〜04）から import して使う。
"""
from __future__ import annotations

import os
import platform
import sys
from getpass import getpass


def in_colab() -> bool:
    return "google.colab" in sys.modules


def configure_japanese_font() -> None:
    """matplotlib で日本語が文字化けしないようフォントを設定する。"""
    import matplotlib.font_manager as fm
    import matplotlib.pyplot as plt

    if in_colab():
        import subprocess

        subprocess.run(["apt-get", "install", "-y", "fonts-noto-cjk"], capture_output=True)
        fm._load_fontmanager(try_read_cache=False)

    jp_candidates = {
        "Darwin": ["Hiragino Sans", "AppleGothic"],
        "Windows": ["Yu Gothic", "MS Gothic"],
    }.get(platform.system(), ["Noto Sans CJK JP", "IPAexGothic"])

    installed = {f.name for f in fm.fontManager.ttflist}
    found = [f for f in jp_candidates if f in installed]
    if found:
        plt.rcParams["font.sans-serif"] = found
    else:
        alt = sorted(
            {
                f.name
                for f in fm.fontManager.ttflist
                if any(c in f.name for c in ["Noto", "IPA", "Gothic", "Yu", "Hiragino"])
            }
        )
        if alt:
            plt.rcParams["font.sans-serif"] = alt
    plt.rcParams["font.family"] = "sans-serif"
    plt.rcParams["axes.unicode_minus"] = False


def init_gee(project: str | None = None) -> str:
    """Earth Engine を認証・初期化する。

    プロジェクトIDは引数 > 環境変数 GEE_PROJECT > 対話入力 の順で決定する。
    """
    import ee

    project = project or os.environ.get("GEE_PROJECT") or getpass("Earth Engine project ID: ")
    print(f"実行環境: {'Google Colab' if in_colab() else 'VSCode / ローカル'}")
    print(f"GEE project: {project}")
    ee.Authenticate()
    print("GEE 初期化中...")
    ee.Initialize(project=project)
    print("GEE 初期化成功")
    return project
