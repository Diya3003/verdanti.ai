"""Central constants. Every number the app reports traces back to a line here.

Sources (checked Oct 2026):
- Valley Water Landscape Rebate Program: valleywater.org/saving-water/rebates-surveys/landscape-rebates
- Valley Water Qualifying Plant List (50% coverage rule, coverage = spread^2 x 0.7854)
- AB 1572 deadlines: sunnyvale.ca.gov/.../nonfunctional-turf
- Water use formula: California MWELO (Model Water Efficient Landscape Ordinance)
"""
import os

# ── AI models (override in .env / Streamlit secrets) ─────────────────────────
TEXT_MODEL = os.getenv("OPENAI_TEXT_MODEL", "gpt-4o")        # vision + reasoning
IMAGE_MODEL = os.getenv("OPENAI_IMAGE_MODEL", "gpt-image-2")  # masked photo edit
IMAGE_QUALITY = os.getenv("OPENAI_IMAGE_QUALITY", "medium")        # draft attempts
FINAL_QUALITY = os.getenv("OPENAI_FINAL_QUALITY", "off")           # optional detail pass on the winner ("high"); off keeps cost ~20-25 cents
MAX_RENDERS = int(os.getenv("MAX_RENDERS", "2"))                    # draft renders per design (each ~6 cents)

# Spending guard for a public demo: max AI designs per visitor session and per day.
SESSION_DESIGN_LIMIT = int(os.getenv("SESSION_DESIGN_LIMIT", "5"))
DAILY_DESIGN_LIMIT = int(os.getenv("DAILY_DESIGN_LIMIT", "40"))

# ── Valley Water rebate rules ────────────────────────────────────────────────
# What a lawn conversion typically costs, so people can see what the rebate covers.
# DIY: about $2.60-8.60/sq ft for tools, plants and materials (LawnStarter xeriscaping cost guide, Dec 2025).
# Hired: California design-build averages about $15-25/sq ft (Ridgeline Outdoor Living 2026 guide;
# LawnStarter's national range is $5-20). Rounded and kept as ranges on purpose.
COST_PER_SQFT = {"diy": (3, 8), "pro": (15, 25)}
REBATE_PER_SQFT = 2.00                 # Landscape Conversion base rate
REBATE_CAP = {"single_family": 3000,   # SF + MF <= 4 units (default)
              "multifamily_5plus": 100000}  # commercial / MF 5+ / HOA common area
MIN_PLANT_COVERAGE = 0.50              # >= 50% coverage at maturity, qualifying plants
VW_HOTLINE = "(408) 630-2554"
VW_URL = "https://www.valleywater.org/saving-water/rebates-surveys/landscape-rebates"

# ── Water use (MWELO): gallons = ETo(in/yr) x Kc x sqft x 0.62 / irrigation efficiency
# Reference ETo by city (CIMIS zone averages, in/yr). Valley Water service area.
ETO_INCHES = {"Palo Alto": 43.6, "Mountain View": 43.6, "Los Altos": 43.6, "Sunnyvale": 44.2,
              "Cupertino": 44.2, "Santa Clara": 44.2, "Saratoga": 44.2, "Campbell": 45.4,
              "Los Gatos": 45.4, "San Jose": 45.4, "Milpitas": 45.4, "Morgan Hill": 46.4,
              "Gilroy": 46.4, "default": 44.0}
KC_TURF = 0.8          # cool-season lawn
KC_LOW_WATER = 0.2     # low-water plants (WUCOLS "Low")
KC_MODERATE = 0.5      # WUCOLS "Moderate" (e.g. ferns, hydrangea, camellia)
EFFICIENCY_SPRAY = 0.75   # overhead spray (typical lawn)
EFFICIENCY_DRIP = 0.81    # drip (MWELO default)
GAL_PER_CCF = 748

# ── AB 1572: stop irrigating nonfunctional turf with potable water by ───────
AB1572_DEADLINES = {
    "Public agency property": "2027-01-01",
    "Commercial / industrial / institutional": "2028-01-01",
    "HOA / common interest development common areas": "2029-01-01",
}

# ── Property types: rebate cap bucket + AB 1572 category (None = not covered) ─
PROPERTY_TYPES = {
    "Independent homeowner": {"cap": "single_family", "ab1572": None},
    "HOA": {"cap": "multifamily_5plus", "ab1572": "HOA / common interest development common areas"},
}

# Default coverage (sq ft per plant at maturity) when a palette plant has no
# Valley Water value, by plant type. Conservative = smaller than typical.
DEFAULT_COVERAGE = {"Groundcover": 9, "Perennial": 4, "Grass": 5, "Shrub": 16,
                    "Fern": 7, "Tree": 50, "default": 6}
