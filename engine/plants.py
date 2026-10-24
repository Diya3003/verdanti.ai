"""Plant palettes.

A palette is a list of plant dicts:
  {botanical, common, sun: [..], types: [..], coverage_sqft, native_ca,
   rebate_status: 'exact' | 'genus' | 'none', water: 'low' | 'moderate'}

Two sources:
  - the built-in Valley Water starter palette (data/default_palette.json)
  - a custom palette the user uploads (e.g. an HOA's approved list), which is
    automatically cross-referenced against the Valley Water qualifying list.
"""
import json, re
from functools import lru_cache
from pathlib import Path
from .config import DEFAULT_COVERAGE

DATA = Path(__file__).resolve().parent.parent / "data"
SUNS = ["Full Sun", "Partial Sun", "Full Shade"]

# Genera that need moderate water (WUCOLS "M") when a custom palette doesn't say.
MODERATE_WATER_GENERA = {"Polystichum", "Woodwardia", "Hydrangea", "Camellia", "Rhododendron",
                         "Pieris", "Clivia", "Asarum", "Weigela", "Tibouchina", "Abelia",
                         "Photinia", "Physocarpus", "Fuchsia", "Heuchera", "Iris", "Ribes"}


@lru_cache
def load_valley_water() -> list:
    return json.loads((DATA / "valley_water.json").read_text())["valley_water"]


@lru_cache
def default_palette() -> tuple:
    return tuple(json.loads((DATA / "default_palette.json").read_text())["palette"])


def _norm(s: str) -> str:
    s = re.sub(r"[‘’'\"]", "'", s or "").lower()
    return re.sub(r"\s+", " ", s).strip()


def match_valley_water(botanical: str) -> tuple[str, dict | None]:
    """Cross-reference one plant name against the Valley Water list.
    Returns ('exact' | 'genus' | 'none', matched VW record).
      exact = same species (cultivar may differ)   genus = only the genus is listed
    Valley Water lists some plants as 'Genus Spp.', which qualifies the whole genus."""
    n = _norm(botanical)
    words = n.replace("'", " ").split()
    if not words:
        return "none", None
    genus, species = words[0], " ".join(words[:2])
    vw = load_valley_water()
    for p in vw:
        if _norm(p["scientific"]) == n:
            return "exact", p
    for p in vw:
        pw = _norm(p["scientific"]).replace("'", " ").split()
        if len(words) > 1 and len(pw) > 1 and " ".join(pw[:2]) == species and words[1] not in ("x",):
            return "exact", p
    for p in vw:
        pw = _norm(p["scientific"]).split()
        if pw and pw[0] == genus and len(pw) > 1 and pw[1].startswith("spp"):
            return "exact", p
    for p in vw:
        if _norm(p["scientific"]).split()[0] == genus:
            return "genus", p
    return "none", None


def custom_palette_from_table(df) -> tuple[list, list]:
    """Build a palette from an uploaded table. Needs a plant-name column; a sun column
    is optional (values containing 'sun', 'part', 'shade'). Returns (palette, warnings)."""
    cols = {c.lower().strip(): c for c in df.columns}
    name_col = next((cols[c] for c in cols if any(k in c for k in ("botanical", "scientific", "plant", "name"))), None)
    if name_col is None:
        return [], ["No plant-name column found (expected a column like 'Botanical name')."]
    sun_col = next((cols[c] for c in cols if "sun" in c or "exposure" in c or "light" in c), None)
    common_col = next((cols[c] for c in cols if "common" in c), None)
    defaults = {_norm(p["botanical"]): p for p in default_palette()}
    out, warn = [], []
    for _, row in df.iterrows():
        name = str(row[name_col]).strip()
        if not name or name.lower() == "nan":
            continue
        sun = []
        if sun_col is not None:
            v = str(row[sun_col]).lower()
            if "full sun" in v or v.strip() == "sun": sun.append("Full Sun")
            if "part" in v or "half" in v: sun.append("Partial Sun")
            if "shade" in v and "part" not in v: sun.append("Full Shade")
        status, vw = match_valley_water(name)
        if not sun:
            sun = defaults.get(_norm(name), {}).get("sun") or list(SUNS)
            if sun_col is None or str(row[sun_col]).strip().lower() in ("", "nan"):
                warn.append(f"{name}: no sun info, allowed in all exposures")
        genus = name.split()[0].capitalize()
        out.append({
            "botanical": name,
            "common": (str(row[common_col]).strip() if common_col is not None else None)
                      or (vw or {}).get("common") or "",
            "sun": sun,
            "types": (vw or {}).get("types", []),
            "coverage_sqft": (vw or {}).get("coverage_sqft") if status != "none" else None,
            "native_ca": bool((vw or {}).get("native_ca")) if status != "none" else False,
            "rebate_status": status,
            "water": "moderate" if genus in MODERATE_WATER_GENERA else "low",
        })
    return out, warn


def coverage_of(plant: dict) -> float:
    """Mature coverage in sq ft: Valley Water value if known, else a conservative default."""
    if plant.get("coverage_sqft"):
        return float(plant["coverage_sqft"])
    genus = plant["botanical"].split()[0]
    if genus in ("Polystichum", "Woodwardia", "Asparagus", "Dryopteris"):
        return DEFAULT_COVERAGE["Fern"]
    for t in plant.get("types", []):
        if t in DEFAULT_COVERAGE:
            return DEFAULT_COVERAGE[t]
    return DEFAULT_COVERAGE["default"]


def candidates_for(palette: list, sun: str) -> list:
    """Palette plants that tolerate this sun exposure, rebate-qualifying first."""
    order = {"exact": 0, "genus": 1, "none": 2}
    return sorted([p for p in palette if sun in p["sun"]],
                  key=lambda p: (order[p["rebate_status"]], p["botanical"]))


def by_name(palette: list, botanical: str) -> dict | None:
    return next((p for p in palette if p["botanical"] == botanical), None)


def search_valley_water(query: str, limit: int = 50) -> list:
    q = query.lower().strip()
    if not q:
        return []
    return [p for p in load_valley_water()
            if q in (p["scientific"] or "").lower() or q in (p["common"] or "").lower()][:limit]
