"""The three AI steps. Each returns plain dicts so the app can show and save them.

  1. analyze_site(photo)            vision model reads the photo like a site assessor
  2. design_zone(analysis, zone)    model designs, but may ONLY choose palette plants
                                    (enforced by a JSON-schema enum, not by asking nicely)
  3. render (engine/render.py)    art director + masked edit + pixel checks + critic retry loop
"""
import base64, io, json, os
from PIL import Image
from . import config as C
from .plants import candidates_for, coverage_of
from .render import LOOKS

_client = None


def client():
    global _client
    if _client is None:
        from openai import OpenAI
        key = os.getenv("OPENAI_API_KEY")
        if not key:
            raise RuntimeError("No OPENAI_API_KEY set.")
        _client = OpenAI(api_key=key)
    return _client


def _data_url(img: Image.Image, max_px=1536) -> str:
    img = img.convert("RGB")
    img.thumbnail((max_px, max_px))
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=88)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def no_em_dash(text: str) -> str:
    """House style: no em dashes anywhere in the app, including AI-written text."""
    return text.replace(" \u2014 ", ", ").replace("\u2014", ", ")


def _ask_json(system: str, user_content, schema: dict, name: str) -> dict:
    r = client().chat.completions.create(
        model=C.TEXT_MODEL,
        messages=[{"role": "system", "content": system},
                  {"role": "user", "content": user_content}],
        response_format={"type": "json_schema",
                         "json_schema": {"name": name, "strict": True, "schema": schema}},
        temperature=0.4,
    )
    msg = r.choices[0].message
    if getattr(msg, "refusal", None):
        raise RuntimeError(f"Model refused: {msg.refusal}")
    return json.loads(no_em_dash(msg.content))


def _obj(props: dict) -> dict:
    """Strict JSON-schema object: every property required, no extras."""
    return {"type": "object", "properties": props, "required": list(props),
            "additionalProperties": False}

S, N = {"type": "string"}, {"type": "number"}
SA = {"type": "array", "items": S}


# ───────────────────────── 1. SITE ANALYSIS ─────────────────────────────────
ANALYSIS_SCHEMA = _obj({
    "observations": SA,     # literal things seen, BEFORE any judgment (anti-hallucination)
    "sun_exposure": _obj({"category": {"type": "string", "enum": ["Full Sun", "Partial Sun", "Full Shade"]},
                          "evidence": S}),
    "preserve": SA,         # everything outside the lawn that must not change
    "trees": {"type": "array", "items": _obj({"description": S, "location": S,
                                              "species_guess": S, "root_zone_note": S})},
    "hardscape": SA,
    "turf_condition": S,
    "soil_drainage": S,
    "views_and_use": S,      # who sees this space, from where; foot traffic
    "constraints": SA,
    "opportunities": SA,
    "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
})

ANALYSIS_SYSTEM = """You are a California-licensed landscape architect doing a turf-conversion
site assessment in the Santa Clara Valley (Mediterranean climate, often heavy adobe clay soil).
The property may be a home, an HOA common area, or a commercial site.
You are assessing landscape conditions only.

Work in this order, like a professional on a site walk:
1. OBSERVATIONS: list only what is literally visible. If you cannot see something
   (irrigation heads, soil type), say "not visible", never guess it into existence.
2. SUN: judge from shadow direction/length, canopy cover, building height and orientation.
3. PRESERVE: every tree, building, fence, sign, path, shrub bed and object outside the
   lawn, described precisely enough that an image editor can keep them identical.
4. Then trees, hardscape, turf, soil/drainage, views/use, constraints, opportunities.
Be specific to THIS photo. Generic statements are failures."""


def analyze_site(photo: Image.Image, zone: dict) -> dict:
    user = [
        {"type": "text", "text":
            f"Area: {zone['name']} (~{zone['sqft']} sq ft) at a {zone.get('property_type', 'property')}. "
            f"Owner-reported sun: {zone['sun']}. "
            f"Owner goals: {zone.get('criteria') or 'none given'}."},
        {"type": "image_url", "image_url": {"url": _data_url(photo)}},
    ]
    return _ask_json(ANALYSIS_SYSTEM, user, ANALYSIS_SCHEMA, "site_analysis")


# ───────────────────────── 2. DESIGN ────────────────────────────────────────
def _design_schema(plant_names: list) -> dict:
    return _obj({
        # 1. think like a designer first: three different directions, then pick one
        "house_read": S,             # architecture, colors and existing plants the garden must answer to
        "style_options": {"type": "array", "items": _obj({
            "style": S, "big_gesture": S, "focal_point": S, "why_it_suits_this_house": S})},
        "chosen_style": S,
        "why_chosen": S,
        "concept": S,                # one evocative line a client would remember
        "big_gesture": S,            # the one bold move that organizes the whole bed
        "focal_point": S,            # where the eye lands first and what is there
        "echo_existing": S,          # how the planting picks up colors/forms already on site
        "color_story": S,
        # 2. then the plant list
        "plants": {"type": "array", "items": _obj({
            "botanical": {"type": "string", "enum": plant_names},  # ← palette lock
            "count": {"type": "integer"},
            "role": {"type": "string", "enum": ["matrix", "structure", "seasonal", "specimen"]},
            "layer": {"type": "string", "enum": ["front", "middle", "back", "accent"]},
            "placement": S,          # where in THIS photo, as a drift shape
            "look": S,               # height, leaf, flower color: what the renderer draws
            "why": S,                # sun/soil/pollinator/rebate reasoning
        })},
        "hardscape_elements": SA,    # boulders, stepping stones, dry creek, gravel, edging...
        "avoid": SA,
        "maintenance_notes": SA,
    })


DESIGN_SYSTEM = """You are an award-winning California landscape designer (think APLD award entries,
Sunset magazine, Pacific Horticulture). You turn a lawn into a garden people stop on the sidewalk to
look at. A plant list that merely "works" is a failure: it must have an idea, a mood and good taste.

HARD RULES (non-negotiable)
- Use ONLY plants from the approved palette (the schema enforces this).
- Valley Water rebate: plants marked REBATE count toward the required 50% plant coverage at
  maturity; NO-REBATE plants don't, so use them only as accents. Choose counts from the coverage
  numbers so REBATE coverage is 60-90% of the area.
- Every plant must suit the area's sun exposure. Keep doors, walkways and driveway sight lines clear;
  nothing taller than a window sill in front of windows; no heavy digging at tree trunks.

HOW YOU WORK, in this order
1. HOUSE READ: the architecture (ranch, craftsman, Spanish, modern, apartment block...), wall, trim
   and roof colors, and the existing trees and shrubs. The garden must belong to THIS house.
2. THREE DIRECTIONS: sketch three genuinely different styles that could suit it, for example a
   Mediterranean gravel garden, a pollinator cottage border, modern
   sculptural (repeated grasses + succulents + boulders), a woodland shade garden, a dry-creek
   garden (a meadow only if the owner asks for one). For each give its BIG GESTURE (one bold organizing move: a sweeping curved bed edge, a
   river of one grass flowing through the bed, a dry creek of cobbles, three grouped boulders with a
   specimen plant, a stepping-stone path through the planting) and its FOCAL POINT. Choose the one
   that best suits the house and the owner's goals, and say why.
3. PLANT THE CHOSEN STYLE using four roles:
   - MATRIX (40-60% of plants): one or two low groundcovers or grasses repeated everywhere; they knit
     the bed together so it reads as one garden, not a plant collection.
   - STRUCTURE: a few shrubs or large grasses that hold the shape year-round; anchor corners and
     the back, frame the focal point.
   - SEASONAL: one or two flowering species in loose, irregular drifts that weave through the
     matrix (elongated sweeps and ribbons, never round blobs or rows).
   - SPECIMEN: at most one or two sculptural plants at the focal point.
   Be restrained: 4-6 species. Repetition with variation. Contrast of FORM (spiky vs mounding vs
   fine and airy vs bold leaf) matters more than many colors.
4. COLOR: two flower colors plus foliage (silver, blue-grey, bronze, chartreuse). ECHO what is
   already there: pick up the color of a red-leaved maple, the front door, the trim or the roof.

CURB APPEAL (front yards and anything seen from the street)
- It must read as intentionally designed and cared for within two seconds from the sidewalk. A loose,
  grassy "meadow" in a front yard reads as an overgrown lawn or a dry field, so avoid it unless the owner
  asks for a meadow. Prefer styles that photograph well: Mediterranean or dry-garden with gravel and
  boulders, a layered pollinator border with a clean edge, modern sculptural, dry creek.
- Grass-like plants (sedges, grasses, rushes, deer grass) are accents: at most a third of all plants.
  The matrix should be low mounding or mat-forming plants with a color that contrasts with lawn green
  (silver, blue-grey, grey-green, chartreuse, bronze), never a sedge "lawn".
- Bold masses: 3-5 plant groups each big enough to read from the street, with strong contrast between
  neighbours (silver next to dark green, fine next to bold, mound next to spike).
- Structure that holds the eye: a defined bed edge and, unless the area is tiny, one hardscape gesture
  (a group of 3 boulders, a stepping-stone path, a dry creek of cobbles, a gravel or decomposed granite
  area). List it in hardscape_elements.

TASTE RULES
- Never place plants in rows, grids, evenly spaced dots or a single line along an edge. Never a
  checkerboard of single plants. Groups are odd-numbered and of DIFFERENT sizes (1, 3, 5, 7, 9).
- At maturity plants touch and overlap; bare mulch shows only in small natural gaps.
- Soften hard edges: low plants spill over path and sidewalk edges.
- Taller plants toward the back, but vary the skyline: let a few grasses or a shrub step forward.
- Placements describe a drift and its shape relative to what is visible in the photo
  ("a long sweep of deer grass curving from behind the walkway toward the right corner")."""


def design_zone(analysis: dict, zone: dict, palette: list, photo: Image.Image = None,
                _retry: bool = False, _user=None) -> dict:
    """zone['sun'] must be a real exposure here (the app fills it from the analysis
    when the owner chose auto-detect)."""
    cands = candidates_for(palette, zone["sun"])
    if not cands:
        raise RuntimeError(f"No palette plants tolerate {zone['sun']}.")
    lines = []
    for p in cands:
        tag = "REBATE" if p["rebate_status"] != "none" else "NO-REBATE"
        lk = LOOKS.get(p["botanical"])
        size = f"{lk['height_cm']}x{lk['width_cm']} cm mature | {lk['look']}" if lk else "size: use botanical knowledge"
        lines.append(f"- {p['botanical']} ({p['common']}) | {coverage_of(p):.0f} sqft/plant | "
                     f"{p.get('water', 'low')} water | {tag}{' | CA native' if p['native_ca'] else ''} | {size}")
    user = (f"ZONE: {zone['name']} | {zone['sqft']} sq ft | sun: {zone['sun']}\n"
            f"PROPERTY: {zone.get('property_type', 'unknown')}\n"
            f"OWNER GOALS: {zone.get('criteria') or 'none'}\n\n"
            f"SITE ANALYSIS:\n{json.dumps(analysis, indent=1)}\n\n"
            f"APPROVED PALETTE:\n" + "\n".join(lines))
    if photo is not None:                       # let the designer actually see the house
        user = [{"type": "text", "text": user + "\n\nThe photo of the area is attached."},
                {"type": "image_url", "image_url": {"url": _data_url(photo)}}]
    if _user is not None:
        user = _user
    design = _ask_json(DESIGN_SYSTEM, user, _design_schema([p["botanical"] for p in cands]),
                       "zone_design")
    # Guard rails: drop zero/negative counts, merge duplicate picks of the same plant.
    merged = {}
    for p in design["plants"]:
        if p["count"] <= 0:
            continue
        if p["botanical"] in merged:
            merged[p["botanical"]]["count"] += p["count"]
        else:
            merged[p["botanical"]] = p
    design["plants"] = list(merged.values())
    if not design["plants"]:
        raise RuntimeError("The design came back empty. Try again.")
    # Code-enforced taste: too many grass-like plants reads as a dry field from the street.
    share, grassy = grass_share(design)
    if share > MAX_GRASS_SHARE and not _retry:
        note = (f"\n\nREVISION NEEDED: grass-like plants ({', '.join(grassy)}) are {share:.0%} of all plants; "
                f"the limit is {MAX_GRASS_SHARE:.0%}. From the street this looks like an overgrown lawn. Rework the "
                f"design: use a low mounding, silver or blue-grey matrix plant and bolder flowering and shrub masses, "
                f"keep grasses as accents, and add a hardscape gesture if there is none.")
        if isinstance(user, list):
            user = [dict(user[0], text=user[0]["text"] + note)] + user[1:]
        else:
            user = user + note
        return design_zone(analysis, zone, palette, photo, _retry=True, _user=user)
    return design


GRASS_GENERA = {"carex", "muhlenbergia", "festuca", "stipa", "nassella", "leymus", "juncus", "pennisetum",
                "calamagrostis", "lomandra", "sesleria", "helictotrichon", "bouteloua", "elymus", "chondropetalum",
                "elegia", "deschampsia", "melica", "miscanthus", "anigozanthos", "panicum", "aristida", "sporobolus"}
MAX_GRASS_SHARE = 0.4


def grass_share(design: dict):
    total = sum(p["count"] for p in design["plants"]) or 1
    grassy = [p for p in design["plants"] if p["botanical"].split()[0].lower() in GRASS_GENERA]
    return sum(p["count"] for p in grassy) / total, [p["botanical"] for p in grassy]


# ───────────────────────── 3. RENDER ────────────────────────────────────────
# Rendering (art direction, checks, critic loop) lives in engine/render.py.


def polygon_mask(size: tuple, points: list) -> Image.Image:
    """Build an edit mask from clicked outline points (in image pixels).
    Inside polygon -> transparent (repaint). Outside -> opaque (keep)."""
    from PIL import ImageDraw
    m = Image.new("RGBA", size, (255, 255, 255, 255))
    if len(points) >= 3:
        ImageDraw.Draw(m).polygon([tuple(p) for p in points], fill=(0, 0, 0, 0))
    return m
