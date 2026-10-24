"""Build data/valley_water.json from Valley Water's qualifying plant list spreadsheet
(Santa Clara Valley Water District Landscape Rebate Program, ~2,700 plants).

    python scripts/build_plant_db.py Valley_Water_Qualifying_Plant_Full_List.xlsx
Then run scripts/build_default_palette.py to refresh the starter palette.
"""
import json, sys, re
import pandas as pd

def clean(v):
    if pd.isna(v): return None
    s = str(v).strip()
    return None if s in ("", "-", "-") else s

def load_valley_water(path):
    df = pd.read_excel(path, sheet_name="Full List", header=None, skiprows=3)
    df = df.iloc[:, :8]
    df.columns = ["sort", "scientific", "common", "coverage", "native", "genetic_concern", "invasive", "types"]
    out = []
    for r in df.itertuples(index=False):
        if not clean(r.scientific): continue
        out.append({
            "scientific": clean(r.scientific),
            "common": clean(r.common),
            "coverage_sqft": float(r.coverage) if str(r.coverage).replace('.','',1).isdigit() else None,
            "native_ca": clean(r.native) == "Yes",
            "invasive": clean(r.invasive) == "Yes",
            "types": [t.strip() for t in (clean(r.types) or "").split(",") if t.strip()],
        })
    return out

if __name__ == "__main__":
    vw = load_valley_water(sys.argv[1])
    json.dump({"valley_water": vw}, open("data/valley_water.json", "w"), indent=1)
    print(f"Valley Water plants: {len(vw)}")
