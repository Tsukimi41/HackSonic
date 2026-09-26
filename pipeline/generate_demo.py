"""公式筆ポリゴンと再現可能な模擬観測から静的デモ成果を生成する。

模擬観測はUI・アルゴリズム再現用で、実在圃場の状態や精度を表さない。
本番では同じ observation schema に Earth Engine の集計値を渡す。
"""
from __future__ import annotations

import argparse
import bisect
import copy
import hashlib
import json
import math
import random
from collections import Counter
from pathlib import Path

import geopandas as gpd
from shapely.geometry import box, mapping

from soramamori.engine import classify_year, compare_years, priority_components

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FGB = ROOT / "tmp" / "maff-2026" / "extracted" / "MB0001_2026_2025_07.fgb"
DEFAULT_OUT = ROOT / "public" / "data"
DATES = ["03-10", "04-12", "05-05", "05-25", "06-12", "07-12", "08-12", "09-12", "10-12", "11-12"]


def stable_noise(field_id: str, year: int, index: int, scale: float) -> float:
    digest = hashlib.sha256(f"{field_id}|{year}|{index}".encode()).digest()
    return ((int.from_bytes(digest[:4], "big") / (2**32 - 1)) * 2 - 1) * scale


def scenario_for(field_id: str, year: int) -> str:
    value = int(hashlib.sha256(f"scenario|{field_id}|{year}".encode()).hexdigest()[:8], 16) % 100
    if value < 37: return "paddy"
    if value < 68: return "upland"
    if value < 84: return "fallow"
    if value < 92: return "conflict"
    return "insufficient"


def simulate_observations(field_id: str, year: int, scenario: str) -> list[dict]:
    ndvi_profiles = {
        "paddy": [0.25, 0.24, 0.23, 0.27, 0.46, 0.68, 0.74, 0.61, 0.36, 0.27],
        "upland": [0.27, 0.28, 0.25, 0.28, 0.43, 0.59, 0.67, 0.56, 0.34, 0.28],
        "fallow": [0.27, 0.28, 0.29, 0.28, 0.31, 0.32, 0.33, 0.31, 0.29, 0.28],
        "conflict": [0.26, 0.27, 0.28, 0.27, 0.31, 0.33, 0.34, 0.31, 0.29, 0.27],
        "insufficient": [0.26, 0.27, 0.25, 0.27, 0.45, 0.60, 0.67, 0.55, 0.34, 0.28],
    }
    vh_profiles = {
        "paddy": [-10.8, -10.5, -22.4, -21.9, -16.0, -13.5, -12.4, -11.8, -11.5, -11.2],
        "upland": [-10.8, -10.5, -11.8, -11.4, -10.9, -10.3, -10.0, -10.2, -10.6, -10.8],
        "fallow": [-10.9, -10.6, -11.3, -11.1, -10.8, -10.6, -10.5, -10.6, -10.8, -10.9],
        "conflict": [-10.8, -10.5, -20.2, -19.8, -15.7, -13.4, -12.5, -11.8, -11.4, -11.1],
        "insufficient": [-10.8, -10.5, -12.0, -11.5, -11.0, -10.5, -10.2, -10.3, -10.6, -10.8],
    }
    rows = []
    for i, md in enumerate(DATES):
        invalid = scenario == "insufficient" and i in {2, 3, 4, 5, 6, 7}
        rows.append({
            "date": f"{year}-{md}",
            "ndvi": None if invalid else round(ndvi_profiles[scenario][i] + stable_noise(field_id, year, i, 0.012), 4),
            "vh_db": None if (scenario == "insufficient" and i in {0, 1, 2, 3}) else round(vh_profiles[scenario][i] + stable_noise(field_id, year, i + 20, 0.25), 3),
            "vv_db": None if invalid else round(vh_profiles[scenario][i] + 5.2 + stable_noise(field_id, year, i + 40, 0.3), 3),
            "valid_s2": not invalid, "valid_s1": not (scenario == "insufficient" and i in {0, 1, 2, 3}),
            "valid_pixel_count": 8 if not invalid else 0,
            "expected_pixel_count": 10, "valid_ratio": 0.8 if not invalid else 0.0,
        })
    return rows


def largest_remainder(total: int) -> dict[str, int]:
    shares = {"match": .50, "mismatch": .25, "unavailable": .15, "not_comparable": .10}
    base = {k: math.floor(total * v) for k, v in shares.items()}
    for key, _ in sorted(shares.items(), key=lambda kv: (-(total * kv[1] - base[kv[0]]), kv[0]))[: total - sum(base.values())]:
        base[key] += 1
    return base


def declaration_for(relation: str, status: str, subtype: str) -> tuple[str, str]:
    if relation == "unavailable": return "not_declared", "not_submitted"
    if relation == "not_comparable": return "unknown", "unknown"
    if relation == "mismatch":
        return ("upland_crop", "planned_cultivation") if subtype == "paddy_signal" else ("paddy_rice", "planned_cultivation") if status == "cultivation_signal" else ("paddy_rice", "planned_cultivation")
    if status == "fallow_candidate": return "other_crop", "planned_fallow"
    if subtype == "paddy_signal": return "paddy_rice", "planned_cultivation"
    if subtype == "upland_crop_signal": return "upland_crop", "planned_cultivation"
    return "unknown", "unknown"


def sensitivity_table(records: list[tuple[list[dict], float]], config: dict) -> list[dict]:
    variants = [("基準", None, None)]
    for key, values in (("sar_flood_drop_db", [7, 11]), ("ndvi_growth_rise", [.15, .25]),
                        ("ndvi_peak", [.45, .55]), ("ndvi_harvest_drop", [.20, .30])):
        variants += [(key, key, value) for value in values]
    table = []
    base_status = [classify_year(rows, config, area)["status"] for rows, area in records]
    for label, key, value in variants:
        cfg = copy.deepcopy(config)
        if key: cfg["thresholds"][key] = value
        statuses = [classify_year(rows, cfg, area)["status"] for rows, area in records]
        table.append({"parameter": label, "value": value, "changed_fields": sum(a != b for a, b in zip(base_status, statuses)), "status_counts": dict(Counter(statuses))})
    return table


def build(fgb: Path, out_dir: Path) -> None:
    config = json.loads((ROOT / "pipeline" / "config.json").read_text(encoding="utf-8"))
    roi = config["roi"]
    gdf = gpd.read_file(fgb, bbox=tuple(roi)).to_crs(4326)
    gdf = gdf[gdf.intersects(box(*roi))].copy().sort_values("polygon_uuid").reset_index(drop=True)
    metric = gdf.to_crs(32654)
    areas = (metric.area / 10_000).tolist()
    centroids = metric.centroid.to_crs(4326)

    items, timeseries, target_records = [], {}, []
    for idx, row in gdf.iterrows():
        field_id = f"maff-2026-{row.polygon_uuid}"
        yearly = {}
        timeseries[field_id] = {}
        for year in (config["baseline_year"], config["target_year"]):
            scenario = scenario_for(field_id, year)
            obs = simulate_observations(field_id, year, scenario)
            result = classify_year(obs, config, areas[idx])
            yearly[year] = result
            timeseries[field_id][str(year)] = {"observations": obs, "features": result["features"]}
            if year == config["target_year"]: target_records.append((obs, areas[idx]))
        change_type, change_confidence, change_reasons = compare_years(yearly[2024], yearly[2025])
        target = yearly[2025]
        item = {
            "field_id": field_id, "source_polygon_id": row.polygon_uuid, "field_id_method": "source_id",
            "municipality": config["municipality"], "area_ha": round(areas[idx], 6),
            "source_land_type": int(row.land_type), "declaration_source": "synthetic_demo", "is_synthetic_declaration": True,
            "baseline_year": 2024, "target_year": 2025,
            "baseline_status": yearly[2024]["status"], "status": target["status"],
            "baseline_confidence": yearly[2024]["confidence"], "confidence": target["confidence"],
            "reason_codes": target["reason_codes"], "baseline_subtype": yearly[2024]["cultivation_subtype"],
            "cultivation_subtype": target["cultivation_subtype"], "subtype_confidence": target["subtype_confidence"],
            "subtype_reason_codes": target["subtype_reason_codes"], "change_type": change_type,
            "change_confidence": change_confidence, "change_reason_codes": change_reasons,
            "reference_label": None, "evidence_strength": None, "evidence_sources": [], "evidence_dates": [], "review_status": "not_reviewed",
            "polygon_vintage": 2026, "valid_s2_count": target["valid_s2_count"], "valid_s1_count": target["valid_s1_count"],
            "observation_quality": target["observation_quality"], "quality_flags": target["quality_flags"],
            "ndvi_max": target["ndvi_max"], "ndvi_amplitude": target["ndvi_amplitude"], "ndvi_may": target["ndvi_may"],
            "ndvi_aug": target["ndvi_aug"], "vh_may_db": target["vh_may_db"], "vh_aug_db": target["vh_aug_db"],
            "centroid_lat": round(centroids.iloc[idx].y, 7), "centroid_lon": round(centroids.iloc[idx].x, 7),
        }
        items.append(item)

    rng = random.Random(config["synthetic_declaration_seed"])
    order = list(range(len(items))); rng.shuffle(order)
    counts = largest_remainder(len(items)); cursor = 0
    for relation in ("match", "mismatch", "unavailable", "not_comparable"):
        for idx in order[cursor:cursor + counts[relation]]:
            item = items[idx]
            item["declaration_match"] = relation
            item["declared_crop"], item["declared_status"] = declaration_for(relation, item["status"], item["cultivation_subtype"])
        cursor += counts[relation]

    sorted_areas = sorted(areas)
    for item in items:
        rank = (bisect.bisect_left(sorted_areas, item["area_ha"]) / (len(items) - 1)) if len(items) > 1 else 0
        parts = priority_components(item, rank)
        item["priority_components"] = parts
        item["priority_score"] = round(sum(parts.values()), 2)
        item["auto_candidate"] = item["declaration_match"] == "mismatch" or item["status"] in {"fallow_candidate", "review_required", "insufficient_observation"} or item["change_type"] != "stable"

    features = [{"type": "Feature", "geometry": mapping(row.geometry), "properties": items[idx]} for idx, row in gdf.iterrows()]
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "field-results.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": features}, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    (out_dir / "field-timeseries.json").write_text(json.dumps({"fields": timeseries}, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    manifest = {
        "datasetVersion": config["dataset_version"], "generatedAt": "2026-09-27T00:00:00+09:00",
        "region": config["region"], "regionLabel": "南相馬市東部（確定ROI）", "roi": roi,
        "baselineYear": 2024, "targetYear": 2025, "observationYears": [2024, 2025],
        "polygonVintage": 2026, "crs": "EPSG:4326", "fieldCount": len(items), "methodVersion": config["method_version"],
        "relativeOrbitNumberStart": config["relative_orbit"], "orbitPass": config["orbit_pass"],
        "syntheticDeclarationSeed": config["synthetic_declaration_seed"],
        "thresholds": {"sarFloodDropDb": 9.0, "ndviGrowthRise": .20, "ndviPeak": .50, "ndviHarvestDrop": .25},
        "cloudMask": {"sceneCloudPercent": 20, "fallbackSceneCloudPercent": 30, "cloudProbabilityMax": 40, "maskBufferMeters": 20},
        "sourceObservationRange": {"start": "2024-01-01", "end": "2025-12-31"},
        "dataMode": "official_polygons_reproducible_simulated_observations",
        "notices": ["圃場境界は農林水産省2026年筆ポリゴンをROI切り出し・加工", "衛星時系列と営農申告はアルゴリズム・UI実演用の再現可能な模擬データ", "実在圃場の作付・休耕や行政判断を示さない"],
        "declarationScenarioCounts": counts,
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    methodology = {
        "thresholds": config["thresholds"], "requiredObservations": config["required_observations"],
        "fieldAggregation": config["field_aggregation"], "sensitivity": sensitivity_table(target_records, config),
        "reasonLabels": {
            "SAR_FLOOD_DROP": "湛水期にVHが基準期間から9 dB以上低下しました",
            "NO_SAR_FLOOD_SIGNAL": "9 dB以上の湛水低下は確認されませんでした",
            "NDVI_GROWTH_RISE": "生育前からNDVIが0.20以上上昇しました",
            "NDVI_PEAK_REACHED": "生育期NDVIが0.50以上に達しました",
            "NDVI_HARVEST_DROP": "ピーク後にNDVIが0.25以上低下しました",
            "NDVI_PEAK_LOW": "生育期の植生ピークが低い状態です",
            "NDVI_AMPLITUDE_LOW": "季節による植生変化が小さい状態です",
            "SIGNAL_CONFLICT": "SARと光学の指標が一致していません",
            "NEAR_THRESHOLD": "判定値が閾値付近です",
            "SMALL_FIELD_SEVERE": "0.05 ha未満の小区画のため混合画素の影響を確認します",
            "LOW_CONFIDENCE": "ルールを支える証拠が弱いため確認が必要です",
            "INSUFFICIENT_OPTICAL_OBSERVATIONS": "光学観測が必要数に達していません",
            "INSUFFICIENT_SAR_OBSERVATIONS": "SAR観測が必要数に達していません"
        }
    }
    (out_dir / "methodology.json").write_text(json.dumps(methodology, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"fields": len(items), "status": Counter(i["status"] for i in items), "declarations": counts}, ensure_ascii=False, default=dict))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--fgb", type=Path, default=DEFAULT_FGB)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    build(args.fgb, args.out)
