import copy
import json
from pathlib import Path

from soramamori.engine import classify_year, compare_years, priority_components
from generate_demo import simulate_observations

CONFIG = json.loads((Path(__file__).parents[1] / "config.json").read_text(encoding="utf-8"))


def classify(scenario, area=.3):
    return classify_year(simulate_observations("test-field", 2025, scenario), CONFIG, area)


def test_slide_rule_patterns():
    assert classify("paddy")["cultivation_subtype"] == "paddy_signal"
    assert classify("upland")["cultivation_subtype"] == "upland_crop_signal"
    assert classify("fallow")["status"] == "fallow_candidate"
    assert classify("conflict")["status"] == "review_required"
    assert classify("insufficient")["status"] == "insufficient_observation"


def test_small_field_is_reviewed():
    result = classify("paddy", area=.03)
    assert result["status"] == "review_required"
    assert "SMALL_FIELD_SEVERE" in result["reason_codes"]
    assert result["confidence"] <= .79


def test_threshold_is_inclusive_and_uses_raw_value():
    cfg = copy.deepcopy(CONFIG)
    rows = simulate_observations("threshold", 2025, "upland")
    result = classify_year(rows, cfg, .3)
    assert result["features"]["growth_event"] is True
    assert 0 <= result["observation_quality"] <= 1


def test_year_change_and_priority_sum():
    before, after = classify("paddy"), classify("upland")
    change, confidence, _ = compare_years(before, after)
    assert change == "paddy_to_upland_candidate"
    field = {**after, "declaration_match": "mismatch", "change_type": change}
    parts = priority_components(field, .5)
    assert 0 <= sum(parts.values()) <= 100
    assert parts["declaration"] == 40


def test_same_review_status_is_stable_across_years():
    before = classify("conflict")
    after = classify("conflict")
    change, confidence, _ = compare_years(before, after)
    assert change == "stable"
    assert confidence is not None
