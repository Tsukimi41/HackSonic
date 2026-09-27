"""Sentinel-1 VH / Sentinel-2 NDVI の季節イベントによるルール判定。

丸め前の値でイベントを判定し、各中間値を返す。confidence は正解確率ではなく、
今回のルールを支える証拠の強さである。
"""
from __future__ import annotations

from datetime import date
from statistics import median
from typing import Any


def _month(row: dict[str, Any]) -> int:
    return date.fromisoformat(row["date"]).month


def _valid(rows: list[dict[str, Any]], sensor: str, months: set[int]) -> list[dict[str, Any]]:
    key = f"valid_{sensor}"
    return [r for r in rows if _month(r) in months and r.get(key) is True and r.get("ndvi" if sensor == "s2" else "vh_db") is not None]


def _med(rows: list[dict[str, Any]], key: str) -> float | None:
    values = [float(r[key]) for r in rows if r.get(key) is not None]
    return median(values) if values else None


def _quality(rows: list[dict[str, Any]], counts: dict[str, int], required: dict[str, int]) -> tuple[float, float, float]:
    temporal = median([
        min(counts["sar_pre"] / required["sar_pre"], 1),
        min(counts["sar_flood"] / required["sar_flood"], 1),
        min(counts["ndvi_may"] / required["ndvi_may"], 1),
        min(counts["ndvi_growing"] / required["ndvi_growing"], 1),
    ])
    ratios = [float(r["valid_ratio"]) for r in rows if (r.get("valid_s1") or r.get("valid_s2")) and r.get("valid_ratio") is not None]
    spatial = median(ratios) if ratios else 0.0
    return temporal, spatial, 0.6 * temporal + 0.4 * spatial


def classify_year(rows: list[dict[str, Any]], config: dict[str, Any], area_ha: float) -> dict[str, Any]:
    """1筆・1年を分類する。入力は日付順でなくてもよい。"""
    rows = sorted(rows, key=lambda r: r["date"])
    th = config["thresholds"]
    req = config["required_observations"]
    agg = config["field_aggregation"]

    sar_pre = _valid(rows, "s1", {3, 4})
    sar_flood = _valid(rows, "s1", {5, 6})
    ndvi_may_rows = _valid(rows, "s2", {5})
    ndvi_growing = _valid(rows, "s2", {6, 7, 8, 9})

    counts = {
        "sar_pre": len(sar_pre), "sar_flood": len(sar_flood),
        "ndvi_may": len(ndvi_may_rows), "ndvi_growing": len(ndvi_growing),
    }
    growing_months = len({_month(r) for r in ndvi_growing})
    vh_pre = _med(sar_pre, "vh_db") if len(sar_pre) >= req["sar_pre"] else None
    vh_flood = _med(sar_flood, "vh_db") if len(sar_flood) >= req["sar_flood"] else None
    flood_drop = vh_pre - vh_flood if vh_pre is not None and vh_flood is not None else None
    flood_event = flood_drop >= th["sar_flood_drop_db"] if flood_drop is not None else None

    ndvi_may = _med(ndvi_may_rows, "ndvi") if len(ndvi_may_rows) >= req["ndvi_may"] else None
    monthly = {}
    if len(ndvi_growing) >= req["ndvi_growing"] and growing_months >= req["ndvi_growing_months"]:
        for month in sorted({_month(r) for r in ndvi_growing}):
            monthly[month] = _med([r for r in ndvi_growing if _month(r) == month], "ndvi")
    peak_month = min(monthly, key=lambda m: (-monthly[m], m)) if monthly else None
    ndvi_peak = monthly.get(peak_month) if peak_month is not None else None
    growth_rise = ndvi_peak - ndvi_may if ndvi_peak is not None and ndvi_may is not None else None
    growth_event = growth_rise >= th["ndvi_growth_rise"] if growth_rise is not None else None
    peak_event = ndvi_peak >= th["ndvi_peak"] if ndvi_peak is not None else None

    post_rows = []
    if peak_month is not None and peak_month < 10:
        post_rows = [r for r in _valid(rows, "s2", {9, 10, 11}) if _month(r) > peak_month]
    ndvi_post = _med(post_rows, "ndvi") if len(post_rows) >= req["ndvi_post_peak"] else None
    harvest_drop = ndvi_peak - ndvi_post if ndvi_peak is not None and ndvi_post is not None else None
    harvest_event = harvest_drop >= th["ndvi_harvest_drop"] if harvest_drop is not None else None

    temporal, spatial, observation_quality = _quality(rows, counts, req)
    quality_flags = ["BOUNDARY_VINTAGE_DIFFERENCE"]
    if area_ha < agg["small_field_severe_ha"]:
        quality_flags += ["SMALL_FIELD_SEVERE", "SMALL_FIELD_MIXED_PIXEL"]
    elif area_ha < agg["small_field_warning_ha"]:
        quality_flags += ["SMALL_FIELD_WARNING", "SMALL_FIELD_MIXED_PIXEL"]

    # 生育前基準が欠けても、十分に高い生育期ピークがあれば作付兆候は評価できる。
    # ピーク自体が不明、または低いピークで上昇量も不明な場合だけ観測不足とする。
    s2_unknown = peak_event is None or (peak_event is False and growth_event is None)
    # 作付兆候は「5月からの上昇＋高いピーク」を最も強い証拠とするが、
    # 5月時点ですでに繁茂している作型を落とさないよう、高いピーク単独も採用する。
    vegetation = True if peak_event is True else False if growth_event is False and peak_event is False else "partial"
    vegetation_reasons = (["NDVI_GROWTH_RISE"] if growth_event is True else []) + (["NDVI_PEAK_REACHED"] if peak_event is True else [])
    if s2_unknown:
        status, subtype = "insufficient_observation", "not_evaluated"
        reasons = ["INSUFFICIENT_OPTICAL_OBSERVATIONS"]
    elif flood_event is True and vegetation is True:
        status, subtype = "cultivation_signal", "paddy_signal"
        reasons = ["SAR_FLOOD_DROP", *vegetation_reasons]
    elif flood_event is False and vegetation is True:
        status, subtype = "cultivation_signal", "upland_crop_signal"
        reasons = [*vegetation_reasons, "NO_SAR_FLOOD_SIGNAL"]
    elif flood_event is False and vegetation is False:
        status, subtype = "fallow_candidate", "mixed_or_unknown"
        reasons = ["NO_SAR_FLOOD_SIGNAL", "NDVI_PEAK_LOW", "NDVI_AMPLITUDE_LOW"]
    elif flood_event is None and vegetation is True:
        status, subtype = "cultivation_signal", "not_evaluated"
        reasons = [*vegetation_reasons, "INSUFFICIENT_SAR_OBSERVATIONS"]
    elif flood_event is None:
        status, subtype = "insufficient_observation", "not_evaluated"
        reasons = ["INSUFFICIENT_SAR_OBSERVATIONS"]
    else:
        status, subtype = "review_required", "mixed_or_unknown"
        reasons = ["SIGNAL_CONFLICT"]

    if harvest_event is True:
        reasons.append("NDVI_HARVEST_DROP")
    elif harvest_event is None:
        quality_flags.append("HARVEST_WINDOW_INCOMPLETE")

    margins = []
    for value, threshold, scale in (
        (flood_drop, th["sar_flood_drop_db"], 3.0),
        (growth_rise, th["ndvi_growth_rise"], 0.10),
        (ndvi_peak, th["ndvi_peak"], 0.10),
        (harvest_drop, th["ndvi_harvest_drop"], 0.10),
    ):
        if value is not None:
            margins.append(min(abs(value - threshold) / scale, 1.0))
    event_margin = sum(margins) / len(margins) if margins else 0.0
    agreement = 1.0 if ((flood_event is True and vegetation is True) or (flood_event is False and vegetation in (True, False))) else 0.5 if (flood_event is None and vegetation is True) else 0.0
    confidence = None if status == "insufficient_observation" else 0.5 * event_margin + 0.3 * observation_quality + 0.2 * agreement

    near_threshold = any([
        flood_drop is not None and abs(flood_drop - th["sar_flood_drop_db"]) <= th["near_sar_db"],
        growth_rise is not None and abs(growth_rise - th["ndvi_growth_rise"]) <= th["near_ndvi"],
        ndvi_peak is not None and abs(ndvi_peak - th["ndvi_peak"]) <= th["near_ndvi"],
        harvest_drop is not None and abs(harvest_drop - th["ndvi_harvest_drop"]) <= th["near_ndvi"],
    ])
    if near_threshold and status != "insufficient_observation":
        reasons.append("NEAR_THRESHOLD")
        confidence = min(confidence, 0.79) if confidence is not None else None
    if area_ha < agg["small_field_severe_ha"] and status != "insufficient_observation":
        reasons.append("SMALL_FIELD_SEVERE")
        confidence = min(confidence, 0.69) if confidence is not None else None
    if confidence is not None and confidence < 0.60:
        status, subtype = "review_required", "mixed_or_unknown"
        reasons.append("LOW_CONFIDENCE")
    if confidence is not None and (area_ha < agg["small_field_warning_ha"] or "CLOUD_LIMITED" in quality_flags):
        confidence = min(confidence, 0.79)

    valid_s1_count = sum(1 for r in rows if r.get("valid_s1"))
    valid_s2_count = sum(1 for r in rows if r.get("valid_s2"))
    ndvi_values = [float(r["ndvi"]) for r in rows if r.get("valid_s2") and r.get("ndvi") is not None]
    ndvi_aug = _med([r for r in rows if _month(r) == 8 and r.get("valid_s2")], "ndvi")
    vh_may = _med([r for r in rows if _month(r) == 5 and r.get("valid_s1")], "vh_db")
    vh_aug = _med([r for r in rows if _month(r) == 8 and r.get("valid_s1")], "vh_db")
    sar_quality = min(min(counts["sar_pre"] / req["sar_pre"], 1), min(counts["sar_flood"] / req["sar_flood"], 1))
    subtype_confidence = min(confidence, min(abs(flood_drop - th["sar_flood_drop_db"]) / 3, 1), sar_quality) if confidence is not None and status == "cultivation_signal" and flood_event is not None else None

    return {
        "status": status, "confidence": round(confidence, 4) if confidence is not None else None,
        "reason_codes": list(dict.fromkeys(reasons)), "cultivation_subtype": subtype,
        "subtype_confidence": round(subtype_confidence, 4) if subtype_confidence is not None else None,
        "subtype_reason_codes": [r for r in reasons if r in {"SAR_FLOOD_DROP", "NO_SAR_FLOOD_SIGNAL", "NDVI_GROWTH_RISE", "NDVI_PEAK_REACHED"}],
        "observation_quality": round(observation_quality, 4), "quality_flags": list(dict.fromkeys(quality_flags)),
        "valid_s1_count": valid_s1_count, "valid_s2_count": valid_s2_count,
        "ndvi_max": max(ndvi_values) if ndvi_values else None,
        "ndvi_amplitude": max(ndvi_values) - min(ndvi_values) if ndvi_values else None,
        "ndvi_may": ndvi_may, "ndvi_aug": ndvi_aug, "vh_may_db": vh_may, "vh_aug_db": vh_aug,
        "features": {"vh_pre_median_db": vh_pre, "vh_flood_median_db": vh_flood, "sar_flood_drop_db": flood_drop,
                     "ndvi_growth_rise": growth_rise, "ndvi_peak": ndvi_peak, "ndvi_peak_month": peak_month,
                     "ndvi_post_peak": ndvi_post, "ndvi_harvest_drop": harvest_drop,
                     "flood_event": flood_event, "growth_event": growth_event, "peak_event": peak_event, "harvest_event": harvest_event,
                     "temporal_quality": temporal, "spatial_quality": spatial}
    }


def compare_years(baseline: dict[str, Any], target: dict[str, Any]) -> tuple[str, float | None, list[str]]:
    if baseline["status"] == "insufficient_observation" or target["status"] == "insufficient_observation":
        return "change_uncertain", None, ["OBSERVATION_LIMITS_YEAR_COMPARISON"]
    b, t = baseline["status"], target["status"]
    bs, ts = baseline["cultivation_subtype"], target["cultivation_subtype"]
    if b == "cultivation_signal" and t == "fallow_candidate":
        kind = "cultivated_to_fallow_candidate"
    elif b == "fallow_candidate" and t == "cultivation_signal":
        kind = "fallow_to_cultivated_candidate"
    elif bs == "paddy_signal" and ts == "upland_crop_signal":
        kind = "paddy_to_upland_candidate"
    elif bs == "upland_crop_signal" and ts == "paddy_signal":
        kind = "upland_to_paddy_candidate"
    elif b == t:
        kind = "stable"
    elif b == "review_required" or t == "review_required":
        # 「要確認」は年次比較の欠測ではない。観測値は揃っているため、
        # 明確な作付⇔休耕遷移がない限り「大きな変化なし」とする。
        kind = "stable"
    else:
        kind = "stable"
    confidence = min(v for v in [baseline["confidence"], target["confidence"], baseline["observation_quality"], target["observation_quality"]] if v is not None)
    return kind, round(confidence, 4), ["YEAR_STATUS_COMPARISON", "BOUNDARY_VINTAGE_DIFFERENCE"]


def priority_components(field: dict[str, Any], area_percentile: float) -> dict[str, float]:
    relation = {"mismatch": 40, "not_comparable": 20}.get(field["declaration_match"], 0)
    status = {"fallow_candidate": 25, "review_required": 23, "insufficient_observation": 20}.get(field["status"], 0)
    change = {"cultivated_to_fallow_candidate": 15, "paddy_to_upland_candidate": 11,
              "upland_to_paddy_candidate": 11, "change_uncertain": 9,
              "fallow_to_cultivated_candidate": 6}.get(field["change_type"], 0)
    confidence = field["confidence"] if field["confidence"] is not None else 0.0
    uncertainty = (10 * confidence if field["status"] == "fallow_candidate" else
                   10 * (1 - confidence) if field["status"] == "review_required" else
                   10 * (1 - field["observation_quality"]) if field["status"] == "insufficient_observation" else 0)
    return {"declaration": relation, "status": status, "change": change,
            "evidence_uncertainty": round(uncertainty, 4), "area": round(10 * area_percentile, 4)}
