"""Deterministic math: rebate eligibility, coverage auto-fix, water savings, AB 1572.

The AI never computes these numbers. It picks plants; this module checks the
picks against Valley Water's rules and does all arithmetic.
"""
import math
from datetime import date
from . import config as C
from .plants import by_name, coverage_of, candidates_for


def gallons(sqft: float, kc: float, eff: float, city: str) -> float:
    """MWELO: ETo (in/yr) x plant factor x area x 0.62 / irrigation efficiency."""
    eto = C.ETO_INCHES.get(city, C.ETO_INCHES["default"])
    return eto * kc * sqft * 0.62 / eff


def evaluate_design(design: dict, palette: list, zone_sqft: float, city: str,
                    property_type: str) -> dict:
    """Score a design: plant coverage, rebate eligibility, water and $ savings."""
    rows, total_cov, qual_cov, mod_cov = [], 0.0, 0.0, 0.0
    for item in design["plants"]:
        p = by_name(palette, item["botanical"])
        if p is None:
            continue
        cov_each = coverage_of(p)
        cov = cov_each * item["count"]
        total_cov += cov
        if p["rebate_status"] != "none":
            qual_cov += cov
        if p.get("water") == "moderate":
            mod_cov += cov
        rows.append({**item, "common": p["common"], "coverage_each": cov_each,
                     "coverage_total": cov, "rebate_status": p["rebate_status"],
                     "native_ca": p["native_ca"], "water": p.get("water", "low")})

    qual_pct = qual_cov / zone_sqft if zone_sqft else 0
    eligible = qual_pct >= C.MIN_PLANT_COVERAGE
    rebate = zone_sqft * C.REBATE_PER_SQFT if eligible else 0   # cap applied per property

    before = gallons(zone_sqft, C.KC_TURF, C.EFFICIENCY_SPRAY, city)
    mod_share = min(mod_cov / total_cov, 1) if total_cov else 0
    kc_after = C.KC_LOW_WATER * (1 - mod_share) + C.KC_MODERATE * mod_share
    after = gallons(zone_sqft, kc_after, C.EFFICIENCY_DRIP, city)

    return {
        "rows": rows,
        "plant_count": sum(r["count"] for r in rows),
        "coverage_pct": total_cov / zone_sqft if zone_sqft else 0,
        "qualifying_coverage_pct": qual_pct,
        "rebate_eligible": eligible,
        "rebate_usd": rebate,
        "gallons_before": before,
        "gallons_after": after,
        "gallons_saved": before - after,
        "pct_saved": (before - after) / before if before else 0,
        "native_count": sum(r["count"] for r in rows if r["native_ca"]),
    }


def capped_rebate(total: float, property_type: str) -> float:
    return min(total, C.REBATE_CAP[property_type])


MAX_SCALE = 1.5   # never more than +50% of what the designer chose


def _qual_cov(design, palette):
    return sum(coverage_of(p) * i["count"] for i in design["plants"]
               if (p := by_name(palette, i["botanical"])) and p["rebate_status"] != "none")


def fix_coverage(design: dict, palette: list, zone_sqft: float, sun: str,
                 target: float = 0.60) -> tuple[dict, list]:
    """Make a design rebate-eligible (>=50% qualifying coverage), aiming for `target`.

    Step 1: scale up qualifying plants already in the design (at most MAX_SCALE x),
            keeping the designer's composition.
    Step 2: if still short, add the qualifying shrub with the largest coverage for
            this sun exposure (one big shrub covers what ~20 small perennials do).
    Returns (design, human-readable change log)."""
    log = []
    if _qual_cov(design, palette) >= C.MIN_PLANT_COVERAGE * zone_sqft:
        return design, log
    need = target * zone_sqft

    q_items = [i for i in design["plants"]
               if (p := by_name(palette, i["botanical"])) and p["rebate_status"] != "none"]
    have = _qual_cov(design, palette)
    if q_items and have:
        factor = min(need / have, MAX_SCALE)
        for i in q_items:
            new = math.ceil(i["count"] * factor)
            if new != i["count"]:
                log.append(f"{i['botanical']}: {i['count']} → {new}")
                i["count"] = new

    gap = need - _qual_cov(design, palette)
    if gap > 0:
        shrubs = [p for p in candidates_for(palette, sun)
                  if p["rebate_status"] != "none" and "Shrub" in p.get("types", [])
                  and "Tree" not in p.get("types", []) and coverage_of(p) <= 130]
        if shrubs:
            best = max(shrubs, key=coverage_of)
            n = math.ceil(gap / coverage_of(best))
            existing = next((i for i in design["plants"] if i["botanical"] == best["botanical"]), None)
            if existing:
                existing["count"] += n
            else:
                design["plants"].append({"botanical": best["botanical"], "count": n, "layer": "back",
                                         "placement": "background structure along the far edge",
                                         "look": f"{best['common']}, mature rounded shrub",
                                         "why": "added to meet Valley Water 50% coverage"})
            log.append(f"added {n} × {best['botanical']} ({best['common']}, "
                       f"{coverage_of(best):.0f} sq ft each)")
    if _qual_cov(design, palette) < C.MIN_PLANT_COVERAGE * zone_sqft:
        log.append("Still below 50%. Swap non-qualifying plants (see suggestions).")
    return design, log


def suggest_swaps(design: dict, palette: list, sun: str) -> list:
    """For each non-qualifying plant, qualifying palette plants of a similar type."""
    pool = [p for p in candidates_for(palette, sun) if p["rebate_status"] != "none"]
    out = []
    for item in design["plants"]:
        p = by_name(palette, item["botanical"])
        if not p or p["rebate_status"] != "none":
            continue
        kinds = set(p.get("types") or ["Shrub"])
        alts = [q for q in pool if kinds & set(q.get("types") or [])] or pool
        out.append({"replace": p["botanical"], "common": p["common"],
                    "options": [f"{q['botanical']} ({q['common']})" for q in alts[:4]]})
    return out


def ab1572_status(category: str, today: date | None = None) -> dict | None:
    if category not in C.AB1572_DEADLINES:
        return None
    today = today or date.today()
    deadline = date.fromisoformat(C.AB1572_DEADLINES[category])
    return {"category": category, "deadline": deadline, "days_left": (deadline - today).days}


def project_cost(sqft: float, rebate: float) -> dict:
    """Typical cost ranges for converting this much lawn, and the share the rebate covers."""
    out = {}
    for k, (lo, hi) in C.COST_PER_SQFT.items():
        clo, chi = sqft * lo, sqft * hi
        out[k] = {"low": clo, "high": chi,
                  "covers_low": min(rebate / chi, 1) if chi else 0, "covers_high": min(rebate / clo, 1) if clo else 0}
    return out


def cost_sentence(sqft: float, rebate: float) -> str:
    c = project_cost(sqft, rebate)
    d, p = c["diy"], c["pro"]
    pct = lambda a, b: f"{a:.0%}" if round(a * 100) == round(b * 100) else f"{a:.0%} to {b:.0%}"
    return (f"Replacing {sqft:,.0f} sq ft of lawn typically costs about \\${d['low']:,.0f} to \\${d['high']:,.0f} "
            f"if you do it yourself, or \\${p['low']:,.0f} to \\${p['high']:,.0f} with a landscaper. "
            f"A \\${rebate:,.0f} rebate covers roughly {pct(d['covers_low'], d['covers_high'])} of a do-it-yourself project "
            f"or {pct(p['covers_low'], p['covers_high'])} of a hired one.")
