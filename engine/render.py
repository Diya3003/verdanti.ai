"""Render engine: turns a design into a photorealistic 'after' image, with checks.

This automates the manual trial-and-error loop used to get good renders by hand
(render → look → write specific fixes → re-render):

  1. prepare_canvas   pad any photo shape to a size the image model supports
                      (padding is a blurred copy of the photo, never black), mask the padding as 'keep'
  2. art_director     vision model sees the photo WITH the lawn outlined in red and writes a
                      placement brief tied to real landmarks, using each plant's visual description
  3. render           masked edit with the image model
  4. uncrop+composite crop back to the photo's shape, then paste the ORIGINAL pixels back
                      everywhere outside the outline (feathered edge), preservation is guaranteed by code
  5. measure          pixel checks: black/dark artifacts, 'nothing changed', seam color mismatch
  6. critic           vision model scores before vs after on a checklist and writes concrete fixes
  7. retry            if it fails, the fixes are added to the brief and it renders again;
                      the best-scoring attempt is kept (max MAX_ATTEMPTS)
"""
import base64, io, json
from pathlib import Path
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageStat
from . import config as C

MAX_ATTEMPTS = C.MAX_RENDERS     # first render + one rewrite keeps a design around 20-25 cents
PASS_SCORE = 8          # critic overall score (1-10) needed to stop early
LOOKS = json.loads((Path(__file__).resolve().parent.parent / "data" / "plant_looks.json").read_text())

SIZES = {"1536x1024": (1536, 1024), "1024x1536": (1024, 1536), "1024x1024": (1024, 1024)}


# ───────────────────────────── 1. canvas ─────────────────────────────────────
def pick_size(w, h) -> str:
    r = w / h
    return "1536x1024" if r > 1.2 else "1024x1536" if r < 0.83 else "1024x1024"


def prepare_canvas(photo: Image.Image, mask: Image.Image):
    """Fit the photo inside a supported size. Returns (canvas, canvas_mask, box, size_str).
    mask convention: alpha 0 = repaint (lawn), alpha 255 = keep."""
    size_str = pick_size(*photo.size)
    W, H = SIZES[size_str]
    s = min(W / photo.width, H / photo.height)
    w, h = round(photo.width * s), round(photo.height * s)
    x, y = (W - w) // 2, (H - h) // 2
    bg = photo.convert("RGB").resize((W, H)).filter(ImageFilter.GaussianBlur(40))   # no black bars
    canvas = bg.copy(); canvas.paste(photo.convert("RGB").resize((w, h)), (x, y))
    cmask = Image.new("RGBA", (W, H), (255, 255, 255, 255))
    a = mask.convert("RGBA").split()[3].resize((w, h))
    m = Image.new("RGBA", (w, h), (255, 255, 255, 255)); m.putalpha(a)
    cmask.paste(m, (x, y))
    return canvas, cmask, (x, y, w, h), size_str


def uncrop(result: Image.Image, box, size) -> Image.Image:
    x, y, w, h = box
    return result.convert("RGB").crop((x, y, x + w, y + h)).resize(size)


def edit_region(mask: Image.Image) -> Image.Image:
    """L-mode image: 255 where we repaint, 0 where we keep."""
    return ImageChops.invert(mask.convert("RGBA").split()[3])


def composite(before: Image.Image, after: Image.Image, mask: Image.Image, feather: int = 6) -> Image.Image:
    """Original pixels outside the outline, new garden inside, soft edge between."""
    region = edit_region(mask).resize(before.size).filter(ImageFilter.GaussianBlur(feather))
    return Image.composite(after.convert("RGB").resize(before.size), before.convert("RGB"), region)


def overlay(photo: Image.Image, mask: Image.Image, tint=(230, 40, 40), edge_color=(255, 255, 0),
            strength: float = 0.45) -> Image.Image:
    """Photo with the lawn area tinted and outlined. Red/yellow (default) is what the AI sees;
    the app shows users a softer brand-colored version."""
    region = edit_region(mask).resize(photo.size)
    tint_img = Image.new("RGB", photo.size, tint)
    out = Image.composite(Image.blend(photo.convert("RGB"), tint_img, strength), photo.convert("RGB"), region)
    edge = region.filter(ImageFilter.FIND_EDGES).point(lambda v: 255 if v > 40 else 0)
    out.paste(edge_color, mask=edge.filter(ImageFilter.MaxFilter(5)))
    return out


# ───────────────────────────── 5. pixel checks ───────────────────────────────
def measure(before: Image.Image, raw_after: Image.Image, mask: Image.Image) -> dict:
    """Deterministic quality checks on the uncomposited render (same size as before)."""
    b = before.convert("RGB").resize((512, int(512 * before.height / before.width)))
    a = raw_after.convert("RGB").resize(b.size)
    inside = edit_region(mask).resize(b.size).point(lambda v: 255 if v > 128 else 0)
    outside = ImageChops.invert(inside)
    diff = ImageChops.difference(a, b).convert("L")

    def mean_in(img, m):
        st = ImageStat.Stat(img, m)
        return st.mean[0] if st.count[0] else 0.0

    dark_a = a.convert("L").point(lambda v: 255 if v < 18 else 0)
    dark_b = b.convert("L").point(lambda v: 255 if v < 18 else 0)
    inside_px = max(ImageStat.Stat(inside).sum[0] / 255, 1)
    dark_new = (ImageStat.Stat(ImageChops.multiply(dark_a, inside)).sum[0]
                - ImageStat.Stat(ImageChops.multiply(dark_b, inside)).sum[0]) / 255 / inside_px
    m = {
        "inside_change": round(mean_in(diff, inside), 1),     # did the lawn actually change?
        "outside_drift": round(mean_in(diff, outside), 1),    # did the model repaint the scene?
        "new_dark_frac": round(max(dark_new, 0), 3),          # black holes / bars inside the bed
    }
    fails = []
    if m["inside_change"] < 10:
        fails.append("The lawn area barely changed; the garden was not drawn inside the red area.")
    if m["new_dark_frac"] > 0.05:
        fails.append("Large black or very dark patches appeared inside the bed area.")
    if m["outside_drift"] > 45:
        fails.append("The image model repainted the surroundings; lighting/colors at the bed edge may not match.")
    m["fails"] = fails
    return m


# ───────────────────────────── helpers ───────────────────────────────────────
def _url(img: Image.Image, px=1024) -> str:
    img = img.convert("RGB").copy(); img.thumbnail((px, px))
    buf = io.BytesIO(); img.save(buf, "JPEG", quality=85)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def plant_looks_text(design: dict) -> str:
    lines = []
    for p in design["plants"]:
        lk = LOOKS.get(p["botanical"])
        if lk:
            lines.append(f"- {lk['name']} ({p['botanical']}): {p['count']} total | role: {p.get('role', p.get('layer', ''))} | "
                         f"designer wants it: {p.get('placement', '')} | mature ~{lk['height_cm']} cm tall x "
                         f"{lk['width_cm']} cm wide | {lk['look']}")
        else:
            lines.append(f"- {p['botanical']}: {p['count']} total | designer's note: {p.get('look', '')} "
                         f"(describe its real appearance from botanical knowledge)")
    return "\n".join(lines)


# ───────────────────────────── 2. art director ───────────────────────────────
# Lesson from the hand-tuned Lakes renders: image models copy the STRUCTURE of the prompt. A list of
# "species X here, species Y there" comes back as polka dots and rows. What worked was describing the
# finished garden the way a photographer would caption it: one big shape, a focal point, drifts that
# weave into each other, then the details.
EXAMPLE_BRIEF = """(Excerpt of a brief written in the style that produces beautiful renders.)
SCENE: A mature, naturalistic California garden photographed two springs after planting. A broad
sweep of silvery groundcover flows from the sidewalk edge up into the bed like water, spilling softly
over the concrete. Out of it rises a loose river of blue-green deer grass that starts as a single clump
near the walkway and widens into a generous drift of seven toward the right corner, its fine flower
spikes catching the light. Purple lavender and pale-yellow yarrow weave between the grasses in long
irregular ribbons, never in rows. Three half-buried grey boulders sit just left of center with one
sculptural blue agave beside them: the focal point. Plants touch and overlap; dark bark mulch shows only
in small shadowed gaps.
PRESERVE EXACTLY: the concrete walkway on the left (same joints and color); the beige two-story building
and every window; the dark-green hedge along the wall; the burgundy plum tree center-background.
FEEL: relaxed, generous, designed by a professional, like a garden in Sunset magazine."""

BRIEF_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "required": ["scene", "preserve", "big_gesture", "focal_point", "drifts", "edges_and_ground",
                 "camera_and_light", "avoid"],
    "properties": {
        "scene": {"type": "string"},             # 5-8 sentence photographer's caption of the finished garden
        "preserve": {"type": "array", "items": {"type": "string"}},
        "big_gesture": {"type": "string"},
        "focal_point": {"type": "string"},
        "drifts": {"type": "array", "items": {
            "type": "object", "additionalProperties": False,
            "required": ["plant", "shape_and_size", "where", "weaves_with"],
            "properties": {"plant": {"type": "string"}, "shape_and_size": {"type": "string"},
                           "where": {"type": "string"}, "weaves_with": {"type": "string"}}}},
        "edges_and_ground": {"type": "string"},
        "camera_and_light": {"type": "string"},
        "avoid": {"type": "array", "items": {"type": "string"}},
    },
}

TASTE = """- From the sidewalk it must read as an intentionally designed, cared-for garden within two seconds:
  bold masses with strong contrast (silver next to dark green, fine next to bold, mound next to spike),
  a clean bed edge, a clear focal point. A uniform sea of grass-like plants reads as an unmowed field: fail.
- No rows, no grids, no evenly spaced plants, no line of identical mounds along an edge, no
  polka-dot scatter of single plants on mulch, no mirror symmetry.
- Drifts are irregular, elongated sweeps of DIFFERENT sizes that interlock with their neighbours.
- One low matrix plant repeats through the whole bed so it reads as one garden.
- Plants touch and overlap at maturity; mulch shows only in small natural gaps (about 15-25%).
- Soft edges: low plants spill over paving. Vary the skyline: a few tall grasses step forward.
- One clear focal point; everything else supports it."""

DIRECTOR_SYSTEM = f"""You are the art director for a landscape design studio. You write the brief an
image-editing model follows to paint a finished garden into a real photo. You have excellent taste:
your renders look like professional garden photography, never like plants plotted by a computer.

You get: (1) the original photo, (2) the same photo with the area to replant tinted RED and outlined
in YELLOW, (3) the designer's concept, big gesture, focal point and plants with sizes and looks.

Write:
- SCENE: 5-8 vivid sentences describing the finished garden as a photographer would caption it:
  the big gesture first, then the focal point, then how the drifts flow and weave, then texture and
  light. Use positions visible in THIS photo (left/right/front/back, "beside the walkway", "under
  the red maple"). This paragraph matters most.
- PRESERVE: every object near or touching the red area (walls, windows, doors, steps, paths,
  driveway, curbs, fences, trees and trunks, existing shrubs, vehicles) with color/material/position.
- DRIFTS: each drift's plant, shape and size ("long ribbon of 5", "single specimen", "broad sweep of
  9 widening to the right"), where it sits, and which drift it weaves into. Counts are for the whole
  area; describe what is visible from this camera, at mature size about two years after planting,
  scaled against doors (~2 m) and windows.
- EDGES AND GROUND: how the bed meets the paving and any remaining lawn; mulch or gravel color.
- CAMERA AND LIGHT: match time of day, shadow direction, color temperature, lens and angle.

Taste rules:
{TASTE}
Practical rules: keep doors, paths and the driveway clear; nothing above window-sill height in front
of windows; nothing outside the red area changes; no text, people or new structures unless listed.

Example of the style that works:
{EXAMPLE_BRIEF}"""


def art_director(photo, mask, analysis, design, zone) -> dict:
    from .ai import client, no_em_dash
    r = client().chat.completions.create(
        model=C.TEXT_MODEL, temperature=0.5,
        messages=[{"role": "system", "content": DIRECTOR_SYSTEM},
                  {"role": "user", "content": [
                      {"type": "text", "text":
                          f"Area: {zone['name']}, ~{zone['sqft']} sq ft, {zone['sun']}, {zone.get('property_type', '')}.\n"
                          f"Style: {design.get('chosen_style', '')}. Concept: {design['concept']}.\n"
                          f"Big gesture: {design.get('big_gesture', '')}\nFocal point: {design.get('focal_point', '')}\n"
                          f"Echo existing: {design.get('echo_existing', '')}\nColor story: {design['color_story']}.\n"
                          f"Hardscape in design: {', '.join(design.get('hardscape_elements', [])) or 'mulch only'}.\n"
                          f"Site notes: {json.dumps({k: analysis[k] for k in ('preserve', 'trees', 'hardscape', 'constraints')})}\n\n"
                          f"PLANTS (role, where the designer wants them):\n{plant_looks_text(design)}\n\n"
                          f"Image 1 = original. Image 2 = red = area to replant."},
                      {"type": "image_url", "image_url": {"url": _url(photo)}},
                      {"type": "image_url", "image_url": {"url": _url(overlay(photo, mask))}}]}],
        response_format={"type": "json_schema",
                         "json_schema": {"name": "render_brief", "strict": True, "schema": BRIEF_SCHEMA}})
    msg = r.choices[0].message
    if getattr(msg, "refusal", None):
        raise RuntimeError(f"Art director refused: {msg.refusal}")
    return json.loads(no_em_dash(msg.content))


REVISE_SYSTEM = DIRECTOR_SYSTEM + """

REVISION MODE: you also get the previous render (last image) and the design director's critique.
The previous brief did not produce a beautiful garden. Do not just repeat it with small edits:
write a NEW brief that changes the composition enough to fix every problem (bigger and bolder masses,
stronger color and form contrast, a clearer focal point and bed edge), using the same plants."""


def revise_brief(photo, mask, analysis, design, zone, brief, review, last) -> dict:
    """Retry strategy: rewrite the whole brief from the critic's notes and the failed image,
    instead of appending corrections to a brief that already failed."""
    from .ai import client, no_em_dash
    r = client().chat.completions.create(
        model=C.TEXT_MODEL, temperature=0.6,
        messages=[{"role": "system", "content": REVISE_SYSTEM},
                  {"role": "user", "content": [
                      {"type": "text", "text":
                          f"Area: {zone['name']}, ~{zone['sqft']} sq ft, {zone['sun']}.\n"
                          f"Style: {design.get('chosen_style', '')}. Concept: {design['concept']}.\n"
                          f"Big gesture: {design.get('big_gesture', '')}\nFocal point: {design.get('focal_point', '')}\n"
                          f"Hardscape in design: {', '.join(design.get('hardscape_elements', [])) or 'mulch only'}.\n"
                          f"PLANTS:\n{plant_looks_text(design)}\n\n"
                          f"PREVIOUS BRIEF:\n{json.dumps(brief)}\n\n"
                          f"CRITIQUE (artistry {review.get('artistry')}/10, overall {review['overall']}/10):\n"
                          + "\n".join(f"- {x}" for x in review["problems"] + review["fixes"]) +
                          "\n\nImage 1 = original. Image 2 = red = area to replant. Image 3 = previous render."},
                      {"type": "image_url", "image_url": {"url": _url(photo)}},
                      {"type": "image_url", "image_url": {"url": _url(overlay(photo, mask))}},
                      {"type": "image_url", "image_url": {"url": _url(last)}}]}],
        response_format={"type": "json_schema",
                         "json_schema": {"name": "render_brief", "strict": True, "schema": BRIEF_SCHEMA}})
    return json.loads(no_em_dash(r.choices[0].message.content))


def brief_to_prompt(brief: dict, corrections: list) -> str:
    """Prose first (the image model copies the prompt's structure), details after."""
    lines = ["Photorealistic edit of a real photograph. Replace ONLY the masked lawn with a mature,",
             "professionally designed water-wise California garden. Everything outside the mask stays",
             "pixel-identical.", "", brief["scene"], "",
             f"BIG GESTURE: {brief['big_gesture']}", f"FOCAL POINT: {brief['focal_point']}", "",
             "DRIFTS (irregular shapes that interlock, never rows or evenly spaced dots):"] + [
             f"- {d['plant']}: {d['shape_and_size']}, {d['where']}; weaves into {d['weaves_with']}."
             for d in brief["drifts"]] + [
             "", f"EDGES AND GROUND: {brief['edges_and_ground']}",
             f"CAMERA AND LIGHT: {brief['camera_and_light']}", "",
             "PRESERVE EXACTLY:"] + [f"- {x}" for x in brief["preserve"]] + [
             "", "AVOID:"] + [f"- {x}" for x in brief["avoid"] + [
                 "plants in rows, grids or evenly spaced along the edge",
                 "identical round blobs dotted on bare mulch", "black or empty areas",
                 "text, labels, watermarks", "plants floating, oversized or cartoonish"]]
    if corrections:
        lines += ["", "CORRECTIONS (the previous attempt had these problems; fix every one):"] + \
                 [f"- {c}" for c in corrections]
    lines += ["", "Looks like a real garden photographed for a design magazine: natural, generous, layered,",
              "real plant scale, light matching the original photo, sharp focus."]
    return "\n".join(lines)


# ───────────────────────────── 6. critic ─────────────────────────────────────
CRITIC_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "required": ["preservation", "realism", "scale", "artistry", "design_match", "overall",
                 "problems", "fixes"],
    "properties": {k: {"type": "integer"} for k in
                   ("preservation", "realism", "scale", "artistry", "design_match", "overall")} | {
        "problems": {"type": "array", "items": {"type": "string"}},
        "fixes": {"type": "array", "items": {"type": "string"}}},
}

CRITIC_SYSTEM = f"""You are the design director of a high-end landscape studio, reviewing an AI render
before a homeowner sees it. You have strong taste. Image 1: original photo. Image 2: area to replant
(red). Image 3: the render.

Score 1-10:
- preservation: everything outside red unchanged, nothing added or removed.
- realism: looks like a real photo; believable plants, light, shadows and bed edges.
- scale: plant sizes plausible against doors, windows and cars.
- artistry: would this garden be featured in a design magazine? Judge with these rules:
{TASTE}
  Rows, evenly spaced plants or a polka-dot look cap artistry at 4.
- design_match: the overall palette, forms and colors match the design (exact species ID from a
  photo is not required).
overall: your honest verdict, weighted most on artistry and realism (8+ = a homeowner would be
excited to build it; 5 = generic and computer-looking; below 5 = unusable). preservation below 7
caps overall at 5.
problems: specific visible defects. fixes: concrete commands with locations for the next render,
aimed at composition and beauty (e.g. "Break the line of lavender along the sidewalk into two
irregular drifts of different sizes that weave back into the bed"). Never ask to space plants apart
or make every species separately visible. Do not praise; fixes may be empty only if it is excellent."""


def critic(before, mask, after, design) -> dict:
    from .ai import client, no_em_dash
    r = client().chat.completions.create(
        model=C.TEXT_MODEL, temperature=0,
        messages=[{"role": "system", "content": CRITIC_SYSTEM},
                  {"role": "user", "content": [
                      {"type": "text", "text": f"Style: {design.get('chosen_style', '')}. Concept: {design['concept']}\n"
                                               f"Intended plants:\n{plant_looks_text(design)}"},
                      {"type": "image_url", "image_url": {"url": _url(before)}},
                      {"type": "image_url", "image_url": {"url": _url(overlay(before, mask))}},
                      {"type": "image_url", "image_url": {"url": _url(after)}}]}],
        response_format={"type": "json_schema",
                         "json_schema": {"name": "render_review", "strict": True, "schema": CRITIC_SCHEMA}})
    return json.loads(no_em_dash(r.choices[0].message.content))


# ───────────────────────────── 3. render call ────────────────────────────────
def _edit(canvas, cmask, prompt, size_str, quality=None) -> Image.Image:
    from .ai import client

    def png(im):
        b = io.BytesIO(); im.save(b, "PNG"); return b.getvalue()
    r = client().images.edit(model=C.IMAGE_MODEL, image=("before.png", png(canvas.convert("RGBA")), "image/png"),
                             mask=("mask.png", png(cmask), "image/png"), prompt=prompt,
                             size=size_str, quality=quality or C.IMAGE_QUALITY, n=1)
    return Image.open(io.BytesIO(base64.b64decode(r.data[0].b64_json)))


# ───────────────────────────── 7. the loop ───────────────────────────────────
# ───────────────────────────── auto-zoom ─────────────────────────────────────
ZOOM_TARGET = 1536        # long side of the enlarged close-up sent to the image model
ZOOM_SKIP_FRAC = 0.6      # if the lawn's box already covers this much of the photo, don't zoom


def lawn_box(photo_size, mask):
    """Box around the lawn with margin (extra above, so the house base stays as context).
    Returns None when zooming wouldn't help."""
    region = edit_region(mask).resize(photo_size).point(lambda v: 255 if v > 128 else 0)
    bb = region.getbbox()
    if not bb:
        return None
    W, H = photo_size
    x0, y0, x1, y1 = bb
    w, h = x1 - x0, y1 - y0
    pad = int(0.12 * max(w, h)) + 16
    x0, x1 = max(0, x0 - pad), min(W, x1 + pad)
    y0, y1 = max(0, y0 - pad - int(0.35 * h)), min(H, y1 + pad)
    if (x1 - x0) * (y1 - y0) > ZOOM_SKIP_FRAC * W * H:
        return None
    return (x0, y0, x1, y1)


def render_design(photo, mask, analysis, design, zone, log=print) -> dict:
    """Full render with auto-zoom, art direction, checks and retries. Returns
    {after, zoom: (before, after) or None, box, brief, attempts, best_index}."""
    photo = photo.convert("RGB")
    mask = mask.convert("RGBA").resize(photo.size)
    box = lawn_box(photo.size, mask)
    if box:
        crop = photo.crop(box)
        k = min(ZOOM_TARGET / max(crop.size), 4.0)
        size = (round(crop.width * max(k, 1)), round(crop.height * max(k, 1)))
        work, wmask = crop.resize(size, Image.LANCZOS), mask.crop(box).resize(size, Image.NEAREST)
        log("Zooming in on the lawn for a sharper, more detailed design…")
    else:
        work, wmask = photo, mask
    r = _render_loop(work, wmask, analysis, design, zone, log)
    best = r["attempts"][r["best_index"]]["image"]
    if box:
        full = photo.copy()
        full.paste(best.resize((box[2] - box[0], box[3] - box[1]), Image.LANCZOS), box[:2])
        after = composite(photo, full, mask)          # original pixels everywhere outside the lawn
        return {**r, "after": after, "zoom": (work, best), "box": box}
    return {**r, "after": best, "zoom": None, "box": None}


def _render_loop(photo, mask, analysis, design, zone, log) -> dict:
    log("Art director is planning plant placement on your photo…")
    brief = art_director(photo, mask, analysis, design, zone)
    briefs = [brief]
    canvas, cmask, cbox, size_str = prepare_canvas(photo, mask)
    attempts, corrections = [], []
    for i in range(MAX_ATTEMPTS):
        log(f"Rendering attempt {i + 1}/{MAX_ATTEMPTS}…")
        prompt = brief_to_prompt(brief, corrections)
        raw = uncrop(_edit(canvas, cmask, prompt, size_str), cbox, photo.size)
        metrics = measure(photo, raw, mask)
        final = composite(photo, raw, mask)
        log("Reviewing the render…")
        review = critic(photo, mask, final, design)
        art = review.get("artistry", review["overall"])
        score = (review["overall"] + art) / 2 - 3 * len(metrics["fails"])     # beauty counts as much as overall
        attempts.append({"prompt": prompt, "metrics": metrics, "review": review, "score": score, "image": final})
        log(f"→ score {review['overall']}/10, artistry {art}/10"
            + (f", checks failed: {len(metrics['fails'])}" if metrics["fails"] else ""))
        if review["overall"] >= PASS_SCORE and art >= PASS_SCORE - 1 and not metrics["fails"]:
            break
        if i == MAX_ATTEMPTS - 1:
            break
        if art < PASS_SCORE - 1:
            # The composition itself is the problem: rewrite the brief, don't just patch it.
            log("Not beautiful enough yet. Art director is rethinking the composition…")
            brief = revise_brief(photo, mask, analysis, design, zone, brief, review, final)
            briefs.append(brief)
            corrections = metrics["fails"]
        else:
            corrections = metrics["fails"] + review["fixes"]
    best = max(range(len(attempts)), key=lambda k: attempts[k]["score"])
    if C.FINAL_QUALITY not in ("off", C.IMAGE_QUALITY):
        best = _detail_pass(photo, mask, design, attempts, best, log)
    return {"brief": briefs[-1], "briefs": briefs, "attempts": attempts, "best_index": best}


DETAIL_PROMPT = """Photorealistic refinement of this exact image. Keep the garden's composition identical:
every plant, boulder, path and bed edge stays in the same place, size and color. Only increase photographic
quality inside the masked area: crisp individual leaves and flower spikes, real plant textures, natural
shadows under each plant, clean mulch and bed edges, light matching the rest of the photo. Do not add,
remove or move anything. No text."""


def _detail_pass(photo, mask, design, attempts, best, log):
    """Re-render the winning image at high quality, keeping its composition. Kept only if the
    critic agrees it is at least as good."""
    log("Adding final high-quality detail to the best design…")
    win = attempts[best]
    try:
        canvas, cmask, cbox, size_str = prepare_canvas(win["image"], mask)
        raw = uncrop(_edit(canvas, cmask, DETAIL_PROMPT, size_str, quality=C.FINAL_QUALITY), cbox, photo.size)
    except Exception as ex:                      # a failed polish never loses the design
        log(f"Detail pass skipped ({ex}).")
        return best
    metrics = measure(photo, raw, mask)
    final = composite(photo, raw, mask)
    review = critic(photo, mask, final, design)
    art = review.get("artistry", review["overall"])
    score = (review["overall"] + art) / 2 - 3 * len(metrics["fails"])
    attempts.append({"prompt": DETAIL_PROMPT, "metrics": metrics, "review": review, "score": score,
                     "image": final, "detail_pass": True})
    if score >= win["score"] - 0.5 and not metrics["fails"]:
        log(f"→ high-quality version kept ({review['overall']}/10, artistry {art}/10)")
        return len(attempts) - 1
    log("→ kept the original render (the detailed version scored lower)")
    return best
