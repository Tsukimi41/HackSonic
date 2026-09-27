"""配信用成果データが要件定義の品質ゲートを満たすか検証する。"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from shapely.geometry import shape

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "public" / "data"
STATUSES = {"cultivation_signal", "fallow_candidate", "review_required", "insufficient_observation"}
SUBTYPES = {"paddy_signal", "upland_crop_signal", "mixed_or_unknown", "not_evaluated"}


def validate() -> None:
    manifest = json.loads((DATA / "manifest.json").read_text(encoding="utf-8"))
    collection = json.loads((DATA / "field-results.geojson").read_text(encoding="utf-8"))
    timeseries = json.loads((DATA / "field-timeseries.json").read_text(encoding="utf-8"))["fields"]
    features = collection["features"]
    assert manifest["fieldCount"] == len(features) > 0
    ids = [f["properties"]["field_id"] for f in features]
    assert len(ids) == len(set(ids)) and all(ids)
    for feature in features:
        p = feature["properties"]
        geom = shape(feature["geometry"])
        assert geom.is_valid and not geom.is_empty
        assert p["area_ha"] > 0 and 37 <= p["centroid_lat"] <= 38 and 140 <= p["centroid_lon"] <= 142
        assert p["status"] in STATUSES and p["baseline_status"] in STATUSES
        assert p["cultivation_subtype"] in SUBTYPES and p["baseline_subtype"] in SUBTYPES
        assert p["reason_codes"]
        assert p["confidence"] is None or 0 <= p["confidence"] <= 1
        assert 0 <= p["observation_quality"] <= 1
        assert p["declaration_source"] == "synthetic_demo" and p["is_synthetic_declaration"] is True
        assert p["polygon_vintage"] == 2026 and "BOUNDARY_VINTAGE_DIFFERENCE" in p["quality_flags"]
        assert 0 <= p["priority_score"] <= 100
        assert round(sum(p["priority_components"].values()), 2) == p["priority_score"]
        if p["status"] == "insufficient_observation":
            assert p["cultivation_subtype"] == "not_evaluated" and p["confidence"] is None
        if p["area_ha"] < .05:
            assert "SMALL_FIELD_SEVERE" in p["quality_flags"]
            if p["confidence"] is not None:
                assert p["confidence"] <= .69
        assert p["field_id"] in timeseries and set(timeseries[p["field_id"]]) == {"2024", "2025"}
        for year in ("2024", "2025"):
            rows = timeseries[p["field_id"]][year]["observations"]
            assert rows and all(r["vh_db"] is None or r["vh_db"] < 0 for r in rows)
            assert all(r["ndvi"] is None or -1 <= r["ndvi"] <= 1 for r in rows)
    expected = manifest["declarationScenarioCounts"]
    actual = Counter(f["properties"]["declaration_match"] for f in features)
    assert actual == Counter(expected)
    print(json.dumps({"result": "PASS", "fields": len(features), "statuses": Counter(f["properties"]["status"] for f in features), "auto_candidates": sum(f["properties"]["auto_candidate"] for f in features)}, ensure_ascii=False, default=dict))


if __name__ == "__main__":
    validate()
