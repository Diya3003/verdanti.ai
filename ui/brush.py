"""Python wrapper for the lawn brush component (ui/components/lawn_brush/index.html)."""
import base64, io
from pathlib import Path
import streamlit.components.v1 as components
from PIL import Image

_brush = components.declare_component(
    "lawn_brush", path=str(Path(__file__).resolve().parent / "components" / "lawn_brush"))


def _url(img: Image.Image, fmt="JPEG") -> str:
    buf = io.BytesIO()
    img.save(buf, fmt, **({"quality": 85} if fmt == "JPEG" else {}))
    return f"data:image/{fmt.lower()};base64," + base64.b64encode(buf.getvalue()).decode()


def lawn_brush(photo: Image.Image, lawn: Image.Image, version: str, key: str, max_px: int = 820):
    """Show the photo with the lawn mask; let the user paint/erase.
    Returns an updated lawn mask (L, photo size, 255 = lawn) and stroke count, or (None, None)."""
    disp = photo.convert("RGB").copy()
    disp.thumbnail((max_px, max_px))
    m = Image.new("RGBA", disp.size, (255, 255, 255, 0))
    m.putalpha(lawn.convert("L").resize(disp.size))
    val = _brush(photo=_url(disp), mask=_url(m, "PNG"), width=disp.width, height=disp.height,
                 ver=version, key=key, default=None)
    if not val:
        return None, None
    raw = Image.open(io.BytesIO(base64.b64decode(val["png"].split(",", 1)[1]))).convert("RGBA")
    alpha = raw.split()[3].point(lambda v: 255 if v > 127 else 0)
    return alpha.resize(photo.size, Image.NEAREST), val["n"]
