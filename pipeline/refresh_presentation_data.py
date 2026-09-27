"""実観測を再判定し、照合シナリオと優先度を再現可能に更新する。"""
from __future__ import annotations

import bisect
import json
import random
from pathlib import Path

from generate_demo import declaration_for, largest_remainder
from soramamori.engine import classify_year, compare_years, priority_components

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "public" / "data"


def main() -> None:
    config = json.loads((ROOT / "pipeline" / "config.json").read_text(encoding="utf-8"))
    collection = json.loads((DATA / "field-results.geojson").read_text(encoding="utf-8"))
    timeseries = json.loads((DATA / "field-timeseries.json").read_text(encoding="utf-8"))["fields"]
    features = collection["features"]

    for feature in features:
        p = feature["properties"]
        yearly = {
            year: classify_year(timeseries[p["field_id"]][str(year)]["observations"], config, p["area_ha"])
            for year in (config["baseline_year"], config["target_year"])
        }
        baseline, target = yearly[config["baseline_year"]], yearly[config["target_year"]]
        change, change_confidence, change_reasons = compare_years(baseline, target)
        p.update({
            "baseline_status": baseline["status"], "status": target["status"],
            "baseline_confidence": baseline["confidence"], "confidence": target["confidence"],
            "reason_codes": target["reason_codes"], "baseline_subtype": baseline["cultivation_subtype"],
            "cultivation_subtype": target["cultivation_subtype"], "subtype_confidence": target["subtype_confidence"],
            "subtype_reason_codes": target["subtype_reason_codes"], "change_type": change,
            "change_confidence": change_confidence, "change_reason_codes": change_reasons,
        })

    order = list(range(len(features)))
    random.Random(config["synthetic_declaration_seed"]).shuffle(order)
    counts = largest_remainder(len(features))
    cursor = 0
    for relation in ("match", "mismatch", "unavailable", "not_comparable"):
        for index in order[cursor:cursor + counts[relation]]:
            p = features[index]["properties"]
            p["declaration_match"] = relation
            p["declared_crop"], p["declared_status"] = declaration_for(
                relation, p["status"], p["cultivation_subtype"]
            )
        cursor += counts[relation]

    areas = sorted(f["properties"]["area_ha"] for f in features)
    for feature in features:
        p = feature["properties"]
        area_rank = bisect.bisect_left(areas, p["area_ha"]) / (len(areas) - 1)
        parts = priority_components(p, area_rank)
        p["priority_components"] = parts
        p["priority_score"] = round(sum(parts.values()), 2)
        p["auto_candidate"] = (
            p["declaration_match"] == "mismatch"
            or p["status"] in {"fallow_candidate", "review_required", "insufficient_observation"}
            or p["change_type"] != "stable"
        )

    manifest_path = DATA / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["datasetVersion"] = config["dataset_version"]
    manifest["methodVersion"] = config["method_version"]
    manifest["declarationScenarioCounts"] = counts
    manifest["notices"] = [
        "圃場境界は農林水産省2026年筆ポリゴンをROI切り出し・加工",
        "営農申告は照合機能確認用の参考入力データ",
        "衛星観測に基づく現地確認支援情報",
    ]

    (DATA / "field-results.geojson").write_text(
        json.dumps(collection, ensure_ascii=False, separators=(",", ":")), encoding="utf-8"
    )
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
