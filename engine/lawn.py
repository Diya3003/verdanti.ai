"""Automatic lawn detection.

Two signals, combined:
  1. Color + position (free, instant): grass-colored pixels (green, plus yellow-green for
     tired lawns), cleaned with morphology, keeping large regions in the lower part of the frame
     (trees and hedges are green too, but they sit higher and are darker/more textured).
  2. Vision model hint (optional, ~1 cent): the AI outlines where it sees lawn. This rescues
     brown/dry lawns that color alone misses, and removes green shrubs color alone wrongly includes.

The result is an editable mask: 255 = lawn to replace, 0 = keep.
"""
import base64, io, json
import cv2
import numpy as np
from PIL import Image, ImageDraw

WORK = 768      # detection runs at this width for speed


def _np(img: Image.Image) -> np.ndarray:
    return np.array(img.convert("RGB"))


def color_mask(photo: Image.Image) -> np.ndarray:
    """uint8 mask (0/255) of likely lawn at WORK width."""
    small = photo.convert("RGB").copy()
    small.thumbnail((WORK, WORK))
    rgb = _np(small)
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)          # H 0-179, S 0-255, V 0-255
    h, s, v = hsv[..., 0].astype(int), hsv[..., 1].astype(int), hsv[..., 2].astype(int)
    green = (h >= 28) & (h <= 85) & (s >= 45) & (v >= 45)
    yellow_green = (h >= 20) & (h < 28) & (s >= 60) & (v >= 90)   # stressed lawn
    m = ((green | yellow_green) * 255).astype(np.uint8)

    # Lawn is fine-textured; hedges/trees have strong light-dark texture. Penalize high local variance.
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY).astype(np.float32)
    mean = cv2.blur(gray, (9, 9))
    var = cv2.blur(gray * gray, (9, 9)) - mean * mean
    m[var > 900] = 0
    m[v < 55] = 0                                         # deep shade under shrubs

    k = max(3, small.width // 120)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((k * 2, k * 2), np.uint8))
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((k, k), np.uint8))
    m = _keep_lawn_regions(m)
    return refine(rgb, m, var)


def refine(rgb: np.ndarray, rough: np.ndarray, var: np.ndarray, iters: int = 4) -> np.ndarray:
    """GrabCut: learn lawn vs not-lawn colors from confident pixels, then relabel the uncertain
    band. Confident lawn = rough mask eroded, low texture, lower half. Confident not-lawn =
    far from the rough mask, or highly textured (foliage), or the top of the frame."""
    if rough.sum() == 0:
        return rough
    H, W = rough.shape
    k = max(5, W // 60)
    gc = np.full((H, W), cv2.GC_PR_BGD, np.uint8)
    gc[rough > 0] = cv2.GC_PR_FGD
    sure_fg = cv2.erode(rough, np.ones((k * 2, k * 2), np.uint8)) > 0
    sure_fg &= (var < 400)
    sure_fg[: int(H * 0.45)] = False
    far = cv2.dilate(rough, np.ones((k * 3, k * 3), np.uint8)) == 0
    gc[far] = cv2.GC_BGD
    gc[: int(H * 0.12)] = cv2.GC_BGD
    # Foliage cues: shrubs/hedges are more textured and darker than lawn, and stand above it.
    rows = np.arange(H)[:, None] / H
    v = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)[..., 2].astype(np.float32)
    v_lawn = np.median(v[sure_fg]) if sure_fg.any() else np.median(v[rough > 0])
    foliage = ((var > 1100) & (rows < 0.75)) | ((v < 0.62 * v_lawn) & (var > 350) & (rows < 0.8))
    foliage = cv2.morphologyEx(foliage.astype(np.uint8) * 255, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8)) > 0
    gc[(var > 2500) & ~sure_fg] = cv2.GC_PR_BGD
    gc[foliage & ~sure_fg] = cv2.GC_BGD
    gc[sure_fg] = cv2.GC_FGD
    if not (gc == cv2.GC_FGD).any() or not (gc == cv2.GC_BGD).any():
        return rough
    bgd, fgd = np.zeros((1, 65), np.float64), np.zeros((1, 65), np.float64)
    try:
        cv2.grabCut(cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR), gc, None, bgd, fgd, iters, cv2.GC_INIT_WITH_MASK)
    except cv2.error:
        return rough
    out = np.where((gc == cv2.GC_FGD) | (gc == cv2.GC_PR_FGD), 255, 0).astype(np.uint8)
    out = cv2.morphologyEx(out, cv2.MORPH_OPEN, np.ones((k, k), np.uint8))
    return _keep_lawn_regions(out)


def _keep_lawn_regions(m: np.ndarray) -> np.ndarray:
    H, W = m.shape
    n, lab, stats, cent = cv2.connectedComponentsWithStats(m, 8)
    out = np.zeros_like(m)
    for i in range(1, n):
        area = stats[i, cv2.CC_STAT_AREA]
        cy = cent[i][1] / H
        bottom = (stats[i, cv2.CC_STAT_TOP] + stats[i, cv2.CC_STAT_HEIGHT]) / H
        if area < 0.015 * H * W:          # too small
            continue
        if cy < 0.35 or bottom < 0.5:     # floating high in the frame = trees/hedges
            continue
        out[lab == i] = 255
    return fill_holes(out)


def fill_holes(m: np.ndarray, max_hole_frac: float = 0.01) -> np.ndarray:
    """Fill small holes (sprinkler heads, leaves, shadows) but keep big ones (paths, beds)."""
    inv = cv2.bitwise_not(m)
    n, lab, stats, _ = cv2.connectedComponentsWithStats(inv, 4)
    H, W = m.shape
    out = m.copy()
    for i in range(1, n):
        x, y, w, h, a = stats[i]
        touches_edge = x == 0 or y == 0 or x + w == W or y + h == H
        if not touches_edge and a < max_hole_frac * H * W:
            out[lab == i] = 255
    return out


# ───────────────────────── AI hint ───────────────────────────────────────────
HINT_SCHEMA = {
    "type": "object", "additionalProperties": False, "required": ["lawns"],
    "properties": {"lawns": {"type": "array", "items": {
        "type": "object", "additionalProperties": False, "required": ["points"],
        "properties": {"points": {"type": "array", "items": {
            "type": "object", "additionalProperties": False, "required": ["x", "y"],
            "properties": {"x": {"type": "number"}, "y": {"type": "number"}}}}}}}},
}


def ai_hint(photo: Image.Image) -> np.ndarray | None:
    """Ask the vision model to outline lawn areas. Returns a WORK-size mask or None."""
    from .ai import client
    from . import config as C
    small = photo.convert("RGB").copy(); small.thumbnail((WORK, WORK))
    buf = io.BytesIO(); small.save(buf, "JPEG", quality=85)
    url = "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()
    r = client().chat.completions.create(
        model=C.TEXT_MODEL, temperature=0,
        messages=[{"role": "system", "content":
                   "You outline lawn (turf grass, green or dry/brown) in photos for a landscaping tool. "
                   "Return one polygon per separate lawn area, 6-20 points each, tracing its edge, in "
                   "normalized coordinates (x and y from 0 to 1, origin top-left). Exclude paths, driveways, "
                   "existing planting beds, mulch, shrubs, hedges, trees and their canopy, and sky. "
                   "If there is no lawn, return an empty list."},
                  {"role": "user", "content": [{"type": "image_url", "image_url": {"url": url}}]}],
        response_format={"type": "json_schema",
                         "json_schema": {"name": "lawn_outline", "strict": True, "schema": HINT_SCHEMA}})
    lawns = json.loads(r.choices[0].message.content)["lawns"]
    m = Image.new("L", small.size, 0)
    d = ImageDraw.Draw(m)
    for lw in lawns:
        pts = [(min(max(p["x"], 0), 1) * small.width, min(max(p["y"], 0), 1) * small.height) for p in lw["points"]]
        if len(pts) >= 3:
            d.polygon(pts, fill=255)
    arr = np.array(m)
    return arr if arr.any() else None


# ───────────────────────── combine ───────────────────────────────────────────
def detect_lawn(photo: Image.Image, use_ai: bool = False) -> tuple[Image.Image, str]:
    """Returns (mask at photo size, L mode 255 = lawn, short description of method)."""
    cm = color_mask(photo)
    method = "color analysis"
    if use_ai:
        try:
            hint = ai_hint(photo)
        except Exception:
            hint = None
        if hint is not None:
            k = max(5, hint.shape[1] // 25)
            near_hint = cv2.dilate(hint, np.ones((k, k), np.uint8))
            both = cv2.bitwise_and(cm, near_hint)
            # Dry/brown lawn: color found little inside the AI's outline → trust the outline.
            if both.sum() < 0.35 * hint.sum():
                cm, method = hint, "AI outline (lawn looks dry/brown)"
            else:
                cm, method = fill_holes(both), "color analysis + AI outline"
    smooth = cv2.GaussianBlur(cm, (0, 0), 2)
    cm = (smooth > 127).astype(np.uint8) * 255
    return Image.fromarray(cm).resize(photo.size, Image.NEAREST), method


def apply_polygon(mask: Image.Image, points: list, add: bool) -> Image.Image:
    """User edit: add (or erase) a clicked polygon to the lawn mask."""
    m = mask.copy()
    if len(points) >= 3:
        ImageDraw.Draw(m).polygon([tuple(p) for p in points], fill=255 if add else 0)
    return m


def to_edit_mask(lawn: Image.Image) -> Image.Image:
    """Lawn mask (255 = lawn) → image-model mask (alpha 0 = repaint, 255 = keep)."""
    out = Image.new("RGBA", lawn.size, (255, 255, 255, 255))
    out.putalpha(Image.eval(lawn.convert("L"), lambda v: 255 - v))
    return out


def coverage(lawn: Image.Image) -> float:
    a = np.array(lawn.convert("L"))
    return float((a > 127).mean())
