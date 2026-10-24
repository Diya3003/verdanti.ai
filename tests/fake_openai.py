"""Fake OpenAI client for UI testing without API cost (set FAKE_OPENAI=1)."""
import base64, io, json, time
from types import SimpleNamespace as NS
from PIL import Image, ImageFilter
from engine import ai

ANALYSIS = {"observations": ["lawn between walkway and building", "two mature trees"],
    "sun_exposure": {"category": "Partial Sun", "evidence": "tree canopy shades half the lawn"},
    "preserve": ["building facade", "two tree trunks", "walkway"], "trees": [], "hardscape": ["walkway"],
    "turf_condition": "patchy", "soil_drainage": "clay", "views_and_use": "seen from walkway",
    "constraints": ["tree roots"], "opportunities": ["pollinator border"], "confidence": "medium"}

BRIEF = {"scene": "A sweep of silver groundcover flows toward the walkway.", "preserve": ["building facade", "tree trunks"],
         "big_gesture": "curving river of deer grass", "focal_point": "three boulders left of center",
         "drifts": [{"plant": "lavender", "shape_and_size": "long ribbon of 5", "where": "front edge", "weaves_with": "yarrow"}],
         "edges_and_ground": "plants spill over the walkway; dark bark mulch in gaps",
         "camera_and_light": "eye level, soft afternoon light", "avoid": ["blocking walkway"]}
REVIEW = {"preservation": 9, "realism": 8, "scale": 8, "artistry": 8, "design_match": 8, "overall": 8,
          "problems": [], "fixes": []}

class _Chat:
    def create(self, **kw):
        time.sleep(0.5)
        name = kw["response_format"]["json_schema"]["name"]
        if name == "site_analysis":
            out = ANALYSIS
        elif name == "render_brief":
            out = BRIEF
        elif name == "render_review":
            out = REVIEW
        else:
            enum = kw["response_format"]["json_schema"]["schema"]["properties"]["plants"]["items"]["properties"]["botanical"]["enum"]
            out = {"concept": "Layered pollinator border", "color_story": "purple and gold",
                   "plants": [{"botanical": n, "count": 5, "layer": l, "placement": f"{l} of bed",
                               "look": "mounding", "why": "fits sun"} for n, l in zip(enum[:4], ["front", "middle", "middle", "back"])],
                   "hardscape_elements": ["3-inch mulch"], "avoid": ["dense carpet"], "maintenance_notes": ["deep water monthly in year 1"]}
        return NS(choices=[NS(message=NS(content=json.dumps(out), refusal=None))])

class _Images:
    def edit(self, **kw):
        img = Image.open(io.BytesIO(kw["image"][1])).convert("RGB").filter(ImageFilter.GaussianBlur(3)).resize(tuple(map(int, kw["size"].split("x"))))
        b = io.BytesIO(); img.save(b, "PNG")
        return NS(data=[NS(b64_json=base64.b64encode(b.getvalue()).decode())])

ai._client = NS(chat=NS(completions=_Chat()), images=_Images())
