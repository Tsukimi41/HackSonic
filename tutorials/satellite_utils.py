# -*- coding: utf-8 -*-
"""衛星データ前処理の「物理ガード」関数集.

W4「AIデバッグ・スカベンジャーハント」で学んだ、AI 生成コードの物理的ハルシネーション
（エラーなく動くが見かけ上破綻している）を、コードから未然に防ぐためのチェック関数です。

- ``assert_no_double_db``    : S1_GRD は既に dB。もう一度 log 変換（二重変換）していないか検査
- ``assert_ndvi_bands``      : NDVI は NIR(B8) − Red(B4)。RedEdge(B5) を NIR と誤用していないか検査
- ``check_orbit_uniform``    : 時系列の軌道方向（ASC/DESC）を統一しているか検査
- ``check_crs_consistency``  : 複数レイヤの CRS（EPSG）が揃っているか検査
- ``s2_cloud_mask``          : Sentinel-2 の雲マスク処理（GEE 用）
- ``speckle_filter``         : SAR スペックル低減の平滑化（GEE 用）

Colab での使い方（ノートと同じ階層に置き、ノートから import）::

    from satellite_utils import (
        assert_no_double_db, assert_ndvi_bands,
        check_orbit_uniform, check_crs_consistency,
        s2_cloud_mask, speckle_filter,
    )

注: GEE を必要とする関数は、呼び出した時点で ``ee`` が import できなければ
    メッセージを返すだけで安全に動作します（import 自体は軽量）。
"""

from __future__ import annotations

import numpy as np


# ── 1. dB 二重変換の防止 ────────────────────────────────────────────────
def assert_no_double_db(vh, name="VH", lo=-40, hi=0):
    """SAR の後方散乱強度が「dB のまま」であることを検査する.

    Sentinel-1 GRD（COPERNICUS/S1_GRD）は既に dB 変換済みです。典型値は
    およそ -30〜0 dB。もし値が「線形パワー」（0〜数万）のまま入ってきたら
    二重変換・未変換の事故を疑います。

    Parameters
    ----------
    vh : array-like
        対象の VH（または VV）の値列。
    name : str
        検査対象のバンド名（エラーメッセージ用）。
    lo, hi : float
        dB として妥当な下限・上限。

    Returns
    -------
    bool
        妥当な dB の範囲に収まっていれば True。
    """
    arr = np.asarray(vh, dtype=float)
    arr = arr[np.isfinite(arr)]
    if arr.size == 0:
        print(f"[guard] {name}: 値が空のため検査をスキップします。")
        return True
    within = (arr >= lo).all() and (arr <= hi).all()
    if not within:
        print(
            f"[guard][警告] {name} の値域が {arr.min():.2f}〜{arr.max():.2f} です。"
            "dB(-30〜0) の範囲外 = 線形パワーのまま、または二重変換の恐れがあります。"
        )
        return False
    print(f"[guard] OK: {name} は dB のまま（範囲 {lo}〜{hi}）。")
    return True


# ── 2. NDVI バンド指定の検査 ────────────────────────────────────────────
def assert_ndvi_bands(bands, nir="B8", red="B4"):
    """NDVI 計算に使うバンド指定が (NIR, Red) であることを検査する.

    NDVI = (NIR − Red) / (NIR + Red)。Sentinel-2 では NIR=B8, Red=B4。
    よくある誤り: RedEdge(B5) を NIR と誤用すると NDVI が過小評価される。

    Parameters
    ----------
    bands : list[str]
        コード内で NDVI に使われているバンドのリスト（例: ['B8', 'B4']）。
    nir, red : str
        正しい NIR / Red バンド名。

    Returns
    -------
    bool
        指定が (nir, red) に一致すれば True。
    """
    if list(bands) == [nir, red]:
        print(f"[guard] OK: NDVI バンド = {nir}, {red}（正しい組み合わせ）。")
        return True
    if red in bands and nir in bands and bands[0] != nir:
        print(f"[guard] OK: {nir}/{red} を含みます（順序のみ修正推奨）。")
        return True
    print(
        f"[guard][警告] NDVI バンドが {bands} です。"
        f"NIR={nir}, Red={red} を指定してください（RedEdge(B5) を NIR に使うと NDVI 過小）。"
    )
    return False


# ── 3. 軌道方向（ASC/DESC）の統一チェック ────────────────────────────────
def check_orbit_uniform(collection=None, property_name="orbitProperties_pass", n=30):
    """Sentinel-1 の軌道方向（Ascending / Descending）が統一されているか検査する.

    軌道方向が混ざったコレクションは、入射角の違いによる見かけの σ⁰ 変動を
    生み、時系列解析をノイズにします。時系列では必ず ASC か DESC の一方に
    揃えてから平均・差分を取ります。

    Parameters
    ----------
    collection : ee.ImageCollection or None
        GEE の S1 コレクション。None の場合は「呼び出し位置での確認方法」を表示。
    property_name : str
        軌道方向を持つメタデータのプロパティ名。
    n : int
        検査する画像数。

    Returns
    -------
    list[str] or None
        取得できた軌道方向の一覧。混在していたら警告を表示。
    """
    if collection is None:
        print(
            "[guard] 検査対象（ee.ImageCollection）が渡されていません。"
            "自分たちのコードでは `collection.aggregate_histogram('orbitProperties_pass')` で"
            "ASC / DESC の混在を確認してください。"
        )
        return None
    try:
        import ee  # noqa: PLC0415
    except ImportError as e:  # pragma: no cover
        print(f"[guard][警告] ee が import できません: {e}")
        return None
    try:
        orbits = ee.List(collection.limit(n).aggregate_histogram(property_name).keys()).getInfo()
    except Exception as e:  # noqa: BLE001
        print(f"[guard][警告] 軌道情報の取得に失敗しました: {e}")
        return None
    if len(set(orbits)) > 1:
        print(f"[guard][警告] 軌道方向が混在しています: {orbits} → 時系列は ASC か DESC に統一してください。")
    else:
        print(f"[guard] OK: 軌道方向は統一されています（{orbits}）。")
    return orbits


# ── 4. CRS（座標系）整合チェック ────────────────────────────────────────
def check_crs_consistency(images=None, expected="EPSG:32654"):
    """複数レイヤの CRS（EPSG）が揃っているか検査する.

    光学（B8/B4）・SAR（VH/VV）・筆ポリゴンで EPSG が異なると、重ねたときに
    位置ズレ・ミクセルが発生します。日本は UTM 帯（東北は EPSG:32654）が一般的です。

    Parameters
    ----------
    images : ee.ImageCollection or None
        検査する画像群。None の場合は確認方法のみ表示。
    expected : str
        期待する CRS。

    Returns
    -------
    list[str] or None
        取得できた CRS の一覧。
    """
    if images is None:
        print(
            "[guard] 検査対象（ee.ImageCollection）が渡されていません。"
            "自分たちのコードでは `img.projection().crs().getInfo()` で各レイヤの"
            "EPSG を確認し、揃えてから重ねてください（例: " + expected + "）。"
        )
        return None
    try:
        import ee  # noqa: PLC0415
    except ImportError as e:  # pragma: no cover
        print(f"[guard][警告] ee が import できません: {e}")
        return None
    try:
        crs_list = [img.projection().crs().getInfo() for img in images.limit(5).toList(5).getInfo()]
    except Exception as e:  # noqa: BLE001
        print(f"[guard][警告] CRS の取得に失敗しました: {e}")
        return None
    uniq = set(crs_list)
    if len(uniq) > 1:
        print(f"[guard][警告] CRS が混在しています: {uniq} → 統一（例: {expected}）してください。")
    else:
        print(f"[guard] OK: CRS は統一されています（{crs_list[0] if crs_list else '?'}）。")
    return crs_list


# ── 5. Sentinel-2 雲マスク（GEE 用） ────────────────────────────────────
def s2_cloud_mask(img):
    """Sentinel-2 L2A の雲マスク処理（GEE 用）.

    S2_SR_HARMONIZED の SCL バンドで「雲 (9)・雲の影 (3)・Cirrus (10)」をマスクする。
    使う前に `img = img.updateMask(...)` で適用します。
    """
    try:
        import ee  # noqa: PLC0415
    except ImportError as e:  # pragma: no cover
        raise ImportError("s2_cloud_mask は GEE (ee) が必要です") from e
    scl = img.select("SCL")
    cloud_mask = scl.neq(9).And(scl.neq(3)).And(scl.neq(10)).And(scl.neq(8))
    return img.updateMask(cloud_mask)


# ── 6. SAR スペックルフィルタ（GEE 用） ──────────────────────────────────
def speckle_filter(img, radius=2):
    """SAR スペックルノイズ低減の平滑化フィルタ（GEE 用）.

    SAR はスペックルと呼ばれる斑点ノイズを持ちます。圃場単位で平均を取る前に、
    カーネルで軽く平滑化しておくと、分類・時系列が安定します。
    一般的な選択肢: Refined Lee / Boxcar（ここでは簡単な Boxcar 平均）。
    """
    try:
        import ee  # noqa: PLC0415
    except ImportError as e:  # pragma: no cover
        raise ImportError("speckle_filter は GEE (ee) が必要です") from e
    kernel = ee.Kernel.square(radius=radius, units="pixels")
    return img.reduceNeighborhood(
        reducer=ee.Reducer.mean(), kernel=kernel
    )