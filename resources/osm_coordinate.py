import csv
import json
import time
import urllib.parse
import urllib.request

OVERPASS = "https://overpass-api.de/api/interpreter"
OUT = "/Users/maykanda/astrocamp-2026-sia/resources/osm_coordinates_results"


def query_overpass(bbox, label):
    south, west, north, east = bbox
    print(f"===== {label}  bbox=[{west},{south},{east},{north}] =====")
    q = f"""
    [out:json][timeout:90];
    (
      nwr["natural"="water"]({south},{west},{north},{east});
      nwr["waterway"="river"]({south},{west},{north},{east});
      nwr["waterway"="stream"]({south},{west},{north},{east});
      nwr["natural"="wood"]({south},{west},{north},{east});
      nwr["landuse"="forest"]({south},{west},{north},{east});
      nwr["landuse"="residential"]({south},{west},{north},{east});
      nwr["leisure"="nature_reserve"]({south},{west},{north},{east});
    );
    out center;
    """
    data = urllib.parse.urlencode({"data": q}).encode()
    req = urllib.request.Request(OVERPASS, data=data,
                                 headers={"User-Agent": "astrocamp-research/1.0"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                return json.load(r)
        except Exception as e:
            print(f"  attempt {attempt+1} failed: {e}")
            time.sleep(3)
    return None


def center_of(el):
    c = el.get("center")
    if c:
        return c["lat"], c["lon"]
    if el["type"] == "node":
        return el["lat"], el["lon"]
    return None


def categorize(tags):
    waterway = tags.get("waterway")
    natural = tags.get("natural")
    landuse = tags.get("landuse")
    water = tags.get("water")
    if waterway in ("stream", "drain", "ditch"):
        return "stream"
    if waterway == "river":
        return "river"
    if natural == "water" or water:
        return "pond_lake"
    if natural == "wetland" or landuse == "reservoir":
        return "wetland_reservoir"
    if natural == "wood" or landuse == "forest":
        return "forest"
    if landuse == "residential":
        return "residential"
    return "other"


def name_of(tags):
    name = tags.get("name")
    if name:
        return name
    if tags.get("water"):
        return f"[water={tags['water']}]"
    if tags.get("waterway"):
        return f"[waterway={tags['waterway']}]"
    if tags.get("natural"):
        return f"[natural={tags['natural']}]"
    if tags.get("landuse"):
        return f"[landuse={tags['landuse']}]"
    return "[unnamed]"


def main():
    areas = [
        ("soma", "相馬市 (ROI+松川浦+西丘陵)", (37.77, 140.90, 37.83, 141.01)),
        ("minamisoma", "南相馬市 東側クラスタ (ROI+新田川河口+海岸)", (37.60, 140.99, 37.66, 141.04)),
    ]
    all_rows = []
    for key, label, bbox in areas:
        data = query_overpass(bbox, label)
        if not data or "elements" not in data:
            print("  no data")
            continue
        for el in data["elements"]:
            if el.get("tags") is None:
                continue
            c = center_of(el)
            if not c:
                continue
            tags = el.get("tags", {})
            all_rows.append({
                "area": key,
                "category": categorize(tags),
                "name": name_of(tags),
                "lat": round(c[0], 5),
                "lon": round(c[1], 5),
                "osm_type": el["type"],
            })
        print(f"  {label}: {sum(1 for r in all_rows if r['area']==key)} elements")

    with open(OUT + ".csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["area", "category", "name", "lat", "lon", "osm_type"])
        w.writeheader()
        w.writerows(all_rows)

    print("\n===== SUMMARY =====")
    for cat in ("pond_lake", "river", "stream", "wetland_reservoir", "forest", "residential"):
        rows = [r for r in all_rows if r["category"] == cat]
        if not rows:
            continue
        print(f"\n[{cat}] count={len(rows)}")
        for r in sorted(rows, key=lambda x: x["name"]):
            print(f"  {r['area']:10s} ({r['lat']}, {r['lon']})  {r['name']}  [{r['osm_type']}]")

    print(f"\nFull CSV: {OUT}.csv")


if __name__ == "__main__":
    main()
