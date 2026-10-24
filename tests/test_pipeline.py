"""Offline tests: whole pipeline with the OpenAI client mocked out, plus palette checks."""
import json, sys, base64, io
sys.path.insert(0, ".")
from types import SimpleNamespace as NS
import pandas as pd
from PIL import Image
from engine import ai
from engine.plants import default_palette, candidates_for, custom_palette_from_table, match_valley_water
from engine.impact import evaluate_design, fix_coverage

palette = list(default_palette())
zone = {"name": "Front yard", "sqft": 500, "sun": "Auto-detect from photo", "criteria": "pollinators",
        "property_type": "Single-family home"}

# ── palette cross-referencing ────────────────────────────────────────────────
assert match_valley_water("Lavandula angustifolia 'Hidcote'")[0] == "exact"      # Lavandula Spp.
assert match_valley_water("Salvia clevelandii 'Winnifred Gilman'")[0] == "exact"
assert match_valley_water("Polystichum munitum")[0] == "none"
assert match_valley_water("Grevillea 'Coast Gem'")[0] == "genus"
custom, warn = custom_palette_from_table(pd.DataFrame({"Botanical name": ["Salvia clevelandii", "Polystichum munitum"],
                                                       "Sun": ["Full Sun", "Full Shade"]}))
assert [p["rebate_status"] for p in custom] == ["exact", "none"] and custom[1]["sun"] == ["Full Shade"]

# ── mocked AI pipeline ───────────────────────────────────────────────────────
fake_analysis = {"observations": ["lawn by sidewalk"], "sun_exposure": {"category": "Full Sun", "evidence": "short shadows"},
    "preserve": ["two-story stucco house", "concrete driveway left"], "trees": [], "hardscape": ["driveway"],
    "turf_condition": "patchy", "soil_drainage": "clay", "views_and_use": "street-facing", "constraints": [],
    "opportunities": [], "confidence": "medium"}
fake_design = {"concept": "pollinator meadow", "color_story": "purple+yellow", "plants": [
    {"botanical": "Lavandula Spp.", "count": 6, "layer": "front", "placement": "path edge", "look": "purple spikes", "why": "bees"},
    {"botanical": "Achillea Millefolium (Ca Native Cultivars)", "count": 8, "layer": "middle", "placement": "center", "look": "yellow", "why": "native"}],
    "hardscape_elements": ["mulch"], "avoid": ["lawn"], "maintenance_notes": ["cut back yarrow in fall"]}

from tests.fake_openai import BRIEF, REVIEW
reviews = [dict(REVIEW, overall=5, fixes=["keep the walkway clear"]), dict(REVIEW, overall=9), dict(REVIEW, overall=9)]
class FakeChat:
    def __init__(self): self.calls = []
    def create(self, **kw):
        self.calls.append(kw)
        name = kw["response_format"]["json_schema"]["name"]
        out = {"site_analysis": fake_analysis, "zone_design": fake_design, "render_brief": BRIEF}.get(name) \
            or reviews.pop(0)
        return NS(choices=[NS(message=NS(content=json.dumps(out), refusal=None))])
class FakeImages:
    def __init__(self): self.prompts = []; self.qualities = []
    def edit(self, **kw):
        self.prompts.append(kw["prompt"]); self.qualities.append(kw["quality"])
        W, H = map(int, kw["size"].split("x"))
        b = io.BytesIO(); Image.new("RGB", (W, H), (60, 140, 60)).save(b, "PNG")   # 'garden' everywhere
        return NS(data=[NS(b64_json=base64.b64encode(b.getvalue()).decode())])
chat = FakeChat(); images = FakeImages()
ai._client = NS(chat=NS(completions=chat), images=images)

photo = Image.new("RGB", (1200, 900), "olive")
a = ai.analyze_site(photo, zone)
zone["sun"] = a["sun_exposure"]["category"]
d = ai.design_zone(a, zone, palette)
enum = chat.calls[1]["response_format"]["json_schema"]["schema"]["properties"]["plants"]["items"]["properties"]["botanical"]["enum"]
assert enum == [p["botanical"] for p in candidates_for(palette, "Full Sun")]
assert "Salvia Spathacea" not in enum, "shade plant must be locked out of a full-sun design"
d, log = fix_coverage(d, palette, zone["sqft"], zone["sun"])
e = evaluate_design(d, palette, zone["sqft"], "Palo Alto", "single_family")
assert e["rebate_eligible"], e
from engine.render import render_design, prepare_canvas, measure
from engine import config as Cfg
Cfg.FINAL_QUALITY = "high"   # exercise the optional detail pass
# Wide photo (2.5:1), previously produced black bars
photo = Image.new("RGB", (1500, 600), (150, 120, 90))
mask = ai.polygon_mask(photo.size, [[100, 350], [1400, 350], [1400, 590], [100, 590]])
canvas, cmask, box, size = prepare_canvas(photo, mask)
assert size == "1536x1024" and min(canvas.convert("L").getdata()) > 20, "padding must not be black"
rr = render_design(photo, mask, a, d, zone, log=lambda m: None)
out = rr["after"]
assert out.size == photo.size
assert out.getpixel((50, 50)) == (150, 120, 90), "outside the outline must be the original pixels"
assert out.getpixel((750, 500))[1] > 120, "inside the outline must be the new garden"
assert len(rr["attempts"]) == 3 and rr["attempts"][2].get("detail_pass"), "winner gets a detail pass"
assert images.qualities == ["medium", "medium", "high"], images.qualities
assert rr["best_index"] == 2, "detail pass kept when it scores as well"
assert "keep the walkway clear" in images.prompts[1], "critic fixes must feed the next attempt"
# black-patch detector
black = photo.copy(); black.paste((0, 0, 0), (100, 350, 1400, 590))
assert measure(photo, black, mask)["fails"], "black patch must be caught"
m = ai.polygon_mask((100, 100), [[10, 10], [90, 10], [50, 90]])
assert m.getpixel((50, 30))[3] == 0 and m.getpixel((2, 2))[3] == 255
# low artistry -> the brief is rewritten (revise call carries the failed render + critique)
reviews[:] = [dict(REVIEW, overall=6, artistry=4, problems=["looks like a dry field"], fixes=["bolder masses"]),
              dict(REVIEW, overall=9, artistry=9), dict(REVIEW, overall=4, artistry=4)]
n_before = len(chat.calls)
rr2 = render_design(photo, mask, a, d, zone, log=lambda m: None)
revise_calls = [c for c in chat.calls[n_before:] if "REVISION MODE" in c["messages"][0]["content"]]
assert len(revise_calls) == 1 and len(rr2["briefs"]) == 2, "low artistry must trigger a brief rewrite"
assert "looks like a dry field" in revise_calls[0]["messages"][1]["content"][0]["text"]
assert len(revise_calls[0]["messages"][1]["content"]) == 4, "revision must see the failed render"
assert rr2["best_index"] == 1, "a worse detail pass must not replace the winner"
# too many grasses -> design redone once with a revision note
grassy = dict(fake_design, plants=[dict(fake_design["plants"][0], botanical="Carex Pansa", count=30),
                                   dict(fake_design["plants"][1], count=10)])
calls = {"n": 0}
def grassy_then_ok(**kw):
    chat.calls.append(kw); calls["n"] += 1
    out = grassy if calls["n"] == 1 else fake_design
    return NS(choices=[NS(message=NS(content=json.dumps(out), refusal=None))])
orig = chat.create; chat.create = grassy_then_ok
d2 = ai.design_zone(a, zone, palette)
chat.create = orig
assert calls["n"] == 2 and "REVISION NEEDED" in chat.calls[-1]["messages"][1]["content"], "grass-heavy design must be redone"
assert ai.no_em_dash("a \u2014 b") == "a, b"
print("ALL PASS | attempts:", len(rr["attempts"]), "| fix:", log, f"| qualifying {e['qualifying_coverage_pct']:.0%} | rebate ${e['rebate_usd']:,.0f} | saved {e['gallons_saved']:,.0f} gal")
