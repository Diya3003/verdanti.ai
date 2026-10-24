"""Real end-to-end test with your OpenAI key (costs about $0.10-0.25).

    python scripts/smoke_test.py path/to/lawn_photo.jpg

Outlines the bottom 45% of the photo as 'lawn', runs all four steps, and saves
smoke_after.png next to this script's folder. Prints what each step returned."""
import json, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent / ".env")
from PIL import Image, ImageOps
from engine import ai, config as C
from engine.plants import default_palette
from engine.impact import fix_coverage, evaluate_design

photo = ImageOps.exif_transpose(Image.open(sys.argv[1])).convert("RGB")
photo.thumbnail((1600, 1600))
w, h = photo.size
zone = {"name": "Test lawn", "sqft": 400, "sun": "Auto-detect from photo",
        "criteria": "pollinators, low maintenance", "property_type": "Single-family home"}
palette = list(default_palette())
from engine.render import render_design, pick_size, overlay
print(f"Models: {C.TEXT_MODEL} + {C.IMAGE_MODEL} | photo {w}x{h} -> render canvas {pick_size(w, h)}")

t = time.time(); a = ai.analyze_site(photo, zone)
zone["sun"] = a["sun_exposure"]["category"]
print(f"\n1 ANALYSIS ok ({time.time()-t:.0f}s): sun={zone['sun']}, {a['sun_exposure']['evidence']}")
print("  preserve:", a["preserve"][:4])

t = time.time(); d = ai.design_zone(a, zone, palette)
print(f"\n2 DESIGN ok ({time.time()-t:.0f}s): {d['concept']}")
for p in d["plants"]:
    print(f"  {p['count']:>3} x {p['botanical']}  [{p['layer']}]")

d, log = fix_coverage(d, palette, zone["sqft"], zone["sun"])
e = evaluate_design(d, palette, zone["sqft"], "Palo Alto", "single_family")
print(f"\n3 REBATE CHECK: qualifying {e['qualifying_coverage_pct']:.0%} | rebate ${e['rebate_usd']:,.0f} | "
      f"water saved {e['gallons_saved']:,.0f} gal/yr | fixes: {log or 'none'}")

t = time.time()
# Lawn outline: pass points as "x1,y1 x2,y2 ..." (fractions 0-1 of width/height) to match your photo,
# e.g.  python scripts/smoke_test.py photo.jpg "0,0.6 1,0.6 1,1 0,1"
pts = sys.argv[2] if len(sys.argv) > 2 else "0.03,0.62 0.97,0.62 0.97,0.97 0.03,0.97"
poly = [[float(x) * w, float(y) * h] for x, y in (p.split(",") for p in pts.split())]
mask = ai.polygon_mask(photo.size, poly)
root = Path(__file__).resolve().parent.parent
overlay(photo, mask).save(root / "smoke_outline.jpg")
rr = render_design(photo, mask, a, d, zone, log=lambda m: print("  " + m))
rr["after"].save(root / "smoke_after.png")
for i, at in enumerate(rr["attempts"]):
    at["image"].save(root / f"smoke_attempt{i+1}.png")
    rv = at["review"]
    print(f"  attempt {i+1}: overall {rv['overall']}/10 | checks failed: {at['metrics']['fails'] or 'none'}")
    for pr in rv["problems"][:4]:
        print("     -", pr)
print(f"\n4 RENDER done ({time.time()-t:.0f}s): best = attempt {rr['best_index']+1} -> smoke_after.png "
      f"(outline used: smoke_outline.jpg)")
print("\nALL STEPS WORKED ✅")
