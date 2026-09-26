"""Part 2B/2C: 湛水イベントの検出と分類（後処理・GEE不要）

02_fetch_gee_timeseries.py が書き出した生の時系列CSV
(sar_vv_timeseries.csv / mndwi_timeseries.csv) を読み込み、筆ごとに
「湛水イベント」を検出して分類する。GEEを使わない純粋なpandas処理なので、
GEEの認証なしでそのまま動作確認できる。

閾値は固定dB値ではなく、筆ごとのベースライン（季節初期の観測の平均・標準偏差）
からの相対的な変化で判定する方式にしている。SAR_K_SIGMA / SAR_MIN_DROP_DB /
MNDWI_ABS_THRESHOLD / MNDWI_MIN_RISE は調整用パラメータなので、実データで
検証しながらチューニングすること。

分類:
- 水田(高信頼)    : SARとMNDWIの両方でイベント検出（独立した2つの物理原理が一致）
- 要確認(SARのみ)  : SARのみ検出（降雨・風などの誤検知の可能性）
- 要確認(光学のみ) : 光学のみ検出（SARが観測間隔の隙間で湛水ピークを逃した可能性）
- 未検出          : どちらも未検出（休耕地・畑作、またはデータ不足の可能性。
                     次段階の収穫・NDVI量による判定でさらに区別する）

実行:
    python 03_classify_water_events.py              # 実データを分類
    python 03_classify_water_events.py --self-test   # ロジックの自己テストのみ実行
"""
from __future__ import annotations

import argparse

import pandas as pd

# --- 対象期間・軌道 (02_fetch_gee_timeseries.py と揃える) ---
TIME_START = "2025-04-01"
TIME_END = "2025-12-15"
RELATIVE_ORBIT = 46  # 解析計画書Step4-1で確認済みの軌道番号
ORBIT_PASS = "DESCENDING"

# --- 筆ポリゴンの縮小(混合画素対策) ---
NEG_BUFFER_M = -3  # 内側に3m縮小してからサンプリング

# --- SAR(VV)側の湛水イベント判定パラメータ ---
# ベースラインは「対象期間の最初のN観測」の平均・標準偏差から算出する。
SAR_BASELINE_N_OBS = 2
SAR_K_SIGMA = 2.0  # baseline_mean - K*std を下回ったら候補
SAR_MIN_DROP_DB = 3.0  # 加えて、最低でもこのdB以上の落ち込みを要求
                        # (stdが小さい筆でノイズを拾わないための下限)

# --- MNDWI(光学)側の湛水イベント判定パラメータ ---
MNDWI_ABS_THRESHOLD = 0.0  # MNDWIがこの値を超えたら「水面的」とみなす目安
MNDWI_MIN_RISE = 0.15  # ベースラインからの最低上昇幅

# --- 入出力 ---
INPUT_SAR_CSV = "sar_vv_timeseries.csv"  # 02_fetch_gee_timeseries.py の出力
INPUT_MNDWI_CSV = "mndwi_timeseries.csv"  # 02_fetch_gee_timeseries.py の出力
OUTPUT_CLASSIFICATION_CSV = "water_classification.csv"


def detect_sar_event(
    group: pd.DataFrame,
    value_col: str = "VV_mean",
    baseline_n: int = SAR_BASELINE_N_OBS,
    k_sigma: float = SAR_K_SIGMA,
    min_drop_db: float = SAR_MIN_DROP_DB,
) -> pd.Series:
    """1筆分のVV時系列(日付昇順)から湛水イベント(急落)を検出する。

    固定dB閾値ではなく、筆ごとのベースライン(季節初期のN観測)の平均・標準偏差
    からの相対的な落ち込みで判定する(筆ごとの絶対値のばらつきに頑健にするため)。
    あわせて最低落ち込み幅(min_drop_db)も要求し、ベースラインの分散が小さい筆で
    ノイズを拾わないようにする。
    """
    group = group.sort_values("date").reset_index(drop=True)
    if len(group) <= baseline_n:
        return pd.Series(
            {"sar_event": False, "sar_event_date": None, "sar_margin_db": None}
        )

    baseline = group[value_col].iloc[:baseline_n]
    baseline_mean = baseline.mean()
    baseline_std = baseline.std(ddof=0) if len(baseline) > 1 else 0.0

    candidates = group.iloc[baseline_n:]
    threshold_sigma = baseline_mean - k_sigma * baseline_std
    threshold_abs = baseline_mean - min_drop_db
    # 「相対的にも大きく落ちている」かつ「最低でもmin_drop_db落ちている」の両方を要求
    threshold = min(threshold_sigma, threshold_abs)

    below = candidates[candidates[value_col] <= threshold]
    if below.empty:
        return pd.Series(
            {"sar_event": False, "sar_event_date": None, "sar_margin_db": None}
        )

    event_row = below.loc[below[value_col].idxmin()]
    margin = baseline_mean - event_row[value_col]
    return pd.Series(
        {
            "sar_event": True,
            "sar_event_date": event_row["date"],
            "sar_margin_db": round(margin, 2),
        }
    )


def detect_mndwi_event(
    group: pd.DataFrame,
    value_col: str = "MNDWI",
    baseline_n: int = SAR_BASELINE_N_OBS,
    abs_threshold: float = MNDWI_ABS_THRESHOLD,
    min_rise: float = MNDWI_MIN_RISE,
) -> pd.Series:
    """1筆分のMNDWI時系列(日付昇順)から湛水イベント(急上昇)を検出する。"""
    group = group.sort_values("date").reset_index(drop=True)
    if len(group) <= baseline_n:
        return pd.Series(
            {"mndwi_event": False, "mndwi_event_date": None, "mndwi_value": None}
        )

    baseline_mean = group[value_col].iloc[:baseline_n].mean()
    candidates = group.iloc[baseline_n:]

    hit = candidates[
        (candidates[value_col] >= abs_threshold)
        & (candidates[value_col] - baseline_mean >= min_rise)
    ]
    if hit.empty:
        return pd.Series(
            {"mndwi_event": False, "mndwi_event_date": None, "mndwi_value": None}
        )

    event_row = hit.loc[hit[value_col].idxmax()]
    return pd.Series(
        {
            "mndwi_event": True,
            "mndwi_event_date": event_row["date"],
            "mndwi_value": round(event_row[value_col], 3),
        }
    )


def _label(row: pd.Series) -> str:
    if row["sar_event"] and row["mndwi_event"]:
        return "水田(高信頼)"
    if row["sar_event"] and not row["mndwi_event"]:
        return "要確認(SARのみ)"
    if not row["sar_event"] and row["mndwi_event"]:
        return "要確認(光学のみ)"
    return "未検出(次段階で畑/休耕地を判定)"


def classify_parcels(sar_raw: pd.DataFrame, mndwi_raw: pd.DataFrame) -> pd.DataFrame:
    """SARとMNDWIの検出結果を突き合わせ、筆ごとの分類を行う。

    分類:
      水田(高信頼)   : SARとMNDWIの両方でイベント検出 (独立した2つの物理原理が一致)
      要確認(SARのみ) : SARのみ検出。降雨・風などの誤検知の可能性もあるため要確認。
      要確認(光学のみ): 光学のみ検出。観測間隔の隙間でSARが湛水ピークを逃した可能性。
      未検出          : どちらも検出なし。休耕地・畑作、あるいはデータ不足の可能性。
                        次段階(収穫・NDVI量による判定)で畑/休耕地をさらに区別する。
    """
    sar_events = sar_raw.groupby("parcel_id", group_keys=False).apply(
        detect_sar_event, include_groups=False
    )
    mndwi_events = mndwi_raw.groupby("parcel_id", group_keys=False).apply(
        detect_mndwi_event, include_groups=False
    )

    result = sar_events.join(mndwi_events, how="outer")
    result.index.name = "parcel_id"
    result = result.reset_index()
    result["classification"] = result.apply(_label, axis=1)
    return result


def run_pipeline(
    sar_csv: str = INPUT_SAR_CSV,
    mndwi_csv: str = INPUT_MNDWI_CSV,
    out_csv: str = OUTPUT_CLASSIFICATION_CSV,
) -> pd.DataFrame:
    sar_raw = pd.read_csv(sar_csv)
    mndwi_raw = pd.read_csv(mndwi_csv)
    result = classify_parcels(sar_raw, mndwi_raw)
    result.to_csv(out_csv, index=False)
    print(f"{len(result)} 筆を分類し、{out_csv} に出力しました。")
    print(result["classification"].value_counts())
    return result


def self_test() -> None:
    """解析計画書Step5に記載の実測値（南相馬市の明瞭なV字、相馬市西でSARが
    湛水を見逃した実例）を模した簡易データで、classify_parcels のロジックが
    正しく動くかを確認する。

    期待される結果:
    - 南相馬市 -> SAR・光学の両方で検出 -> 「水田(高信頼)」
    - 相馬市西 -> SARでは検出されず、光学のみで検出 -> 「要確認(光学のみ)」
      （実際に計画書が報告している結論と一致）
    """
    sar_raw = pd.DataFrame(
        [
            # 南相馬市(minamisoma_higashi): ベースライン -> 急落 -> 回復
            {"parcel_id": "minamisoma_higashi", "date": "2025-04-05", "VV_mean": -9.5},
            {"parcel_id": "minamisoma_higashi", "date": "2025-04-17", "VV_mean": -9.0},
            {"parcel_id": "minamisoma_higashi", "date": "2025-06-05", "VV_mean": -22.23},
            {"parcel_id": "minamisoma_higashi", "date": "2025-06-17", "VV_mean": -12.40},
            # 相馬市西(soma_nishi): 谷が見えないパターン(観測間隔の隙間で湛水ピークを逃す)
            {"parcel_id": "soma_nishi", "date": "2025-04-05", "VV_mean": -9.2},
            {"parcel_id": "soma_nishi", "date": "2025-04-17", "VV_mean": -8.8},
            {"parcel_id": "soma_nishi", "date": "2025-06-05", "VV_mean": -10.8},
            {"parcel_id": "soma_nishi", "date": "2025-06-17", "VV_mean": -5.67},
        ]
    )
    mndwi_raw = pd.DataFrame(
        [
            # 南相馬市: 光学でも湛水期にMNDWIが上昇する想定
            {"parcel_id": "minamisoma_higashi", "date": "2025-04-05", "MNDWI": -0.35},
            {"parcel_id": "minamisoma_higashi", "date": "2025-04-17", "MNDWI": -0.32},
            {"parcel_id": "minamisoma_higashi", "date": "2025-06-05", "MNDWI": 0.20},
            {"parcel_id": "minamisoma_higashi", "date": "2025-06-17", "MNDWI": 0.05},
            # 相馬市西: 5/18(茶色)->6/20(緑化)の変化が光学で明確に確認された実例
            {"parcel_id": "soma_nishi", "date": "2025-04-05", "MNDWI": -0.30},
            {"parcel_id": "soma_nishi", "date": "2025-04-17", "MNDWI": -0.28},
            {"parcel_id": "soma_nishi", "date": "2025-06-05", "MNDWI": 0.02},
            {"parcel_id": "soma_nishi", "date": "2025-06-17", "MNDWI": 0.15},
        ]
    )

    result = classify_parcels(sar_raw, mndwi_raw)
    print(result[["parcel_id", "sar_event", "mndwi_event", "classification"]])

    r_minamisoma = result.set_index("parcel_id").loc["minamisoma_higashi"]
    assert r_minamisoma["sar_event"] == True
    assert r_minamisoma["mndwi_event"] == True
    assert r_minamisoma["classification"] == "水田(高信頼)"

    r_somanishi = result.set_index("parcel_id").loc["soma_nishi"]
    assert r_somanishi["sar_event"] == False
    assert r_somanishi["mndwi_event"] == True
    assert r_somanishi["classification"] == "要確認(光学のみ)"

    print(
        "\n自己テストOK: 南相馬市=水田(高信頼)、相馬市西=要確認(光学のみ) "
        "-> 解析計画書Step5の実際の結論と一致することを確認しました。"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="実データの代わりに解析計画書Step5の実測値を模したデータでロジックを検証する",
    )
    args = parser.parse_args()

    if args.self_test:
        self_test()
    else:
        run_pipeline()
