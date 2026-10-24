"""Landing page."""
from datetime import date
from pathlib import Path
import streamlit as st
from PIL import Image
from engine import config as C
from ui import theme
from ui.state import go, go_as

GALLERY = Path(__file__).resolve().parent.parent / "data" / "gallery"


def gallery_pairs():
    """data/gallery/<name>_before.jpg + <name>_after.jpg (or .png) → list of (name, before, after)."""
    out = []
    for b in sorted(GALLERY.glob("*_before.*")):
        name = b.name.rsplit("_before", 1)[0]
        a = next(iter(GALLERY.glob(f"{name}_after.*")), None)
        if a:
            out.append((name.replace("-", " ").replace("_", " ").title(), b, a))
    return out


def hero_photo():
    """data/hero.(jpg|png|webp), else the first gallery 'after' image, else None."""
    root = GALLERY.parent
    for ext in ("jpg", "jpeg", "png", "webp"):
        if (root / f"hero.{ext}").exists():
            return root / f"hero.{ext}"
    pairs = gallery_pairs()
    return pairs[0][2] if pairs else None


HEADLINE = "<h1>What if your thirsty lawn became <em>a garden that pays?</em></h1>"
LEAD = ('<p class="lead">Upload a photo of your lawn. Get a professional, water-wise planting design, '
        'a photorealistic preview of your own yard, and a plan that qualifies for Valley Water rebates.</p>')


# ───────────────────────────── hero ──────────────────────────────────────────
def photo_hero(path):
    img = Image.open(path).convert("RGB"); img.thumbnail((1800, 1800))
    st.markdown(f"<style>.st-key-herophoto {{ background-image: linear-gradient(180deg, rgba(0,0,0,0) 40%, "
                f"rgba(0,0,0,.25)), url('data:image/jpeg;base64,{theme.img_b64(img, 80)}'); }}</style>",
                unsafe_allow_html=True)
    with st.container(key="herophoto"):
        with st.container(key="herocard"):
            st.markdown(HEADLINE + LEAD, unsafe_allow_html=True)
            b1, _ = st.columns([1, 1.6])
            b1.button("Design my lawn  →", type="primary", on_click=go, args=("studio",), use_container_width=True)


def dark_hero():
    with st.container(key="hero"):
        left, right = st.columns([1.25, 1], gap="large")
        with left:
            st.markdown(HEADLINE + LEAD, unsafe_allow_html=True)
            b1, _ = st.columns([1, 1.6])
            b1.button("Design my lawn  →", type="primary", on_click=go, args=("studio",), use_container_width=True)
        with right:
            st.markdown(theme.SPRIG, unsafe_allow_html=True)


# ───────────────────────────── sections ──────────────────────────────────────
def roadmap(steps, dark=False):
    rows = "".join(f'<div class="rm-row"><div class="rm-dot">{i}</div><div class="rm-t">{t}</div></div>'
                   for i, t in enumerate(steps, 1))
    return f'<div class="roadmap{" dark" if dark else ""}">{rows}</div>'


def _today():
    """Today in California, so the countdown ticks over at local midnight."""
    try:
        from zoneinfo import ZoneInfo
        from datetime import datetime
        return datetime.now(ZoneInfo("America/Los_Angeles")).date()
    except Exception:
        return date.today()


def for_homeowners():
    cap = C.REBATE_CAP["single_family"]
    with st.container(key="homeband"):
        left, right = st.columns([1, 1.15], gap="large")
        with left:
            st.markdown(f'<div class="section-title" style="margin-top:0">For homeowners</div>'
                        f'<p class="lead">See your own yard as a finished garden before you spend a dollar. '
                        f'Valley Water pays at least ${C.REBATE_PER_SQFT:.0f} for every square foot of lawn you replace, '
                        f'up to ${cap:,}, more in some cities. For a 500 sq ft lawn that is at least $1,000, '
                        f'roughly a quarter to two-thirds of what it costs to do it yourself. A lawn uses roughly '
                        f'four times the water of a water-wise garden.</p>', unsafe_allow_html=True)
            st.button("Design my yard  →", type="primary", on_click=go_as, args=("studio", "Independent homeowner"), key="cta_home")
        with right:
            st.markdown(roadmap([
                "verdanti.ai designs your garden and shows it on a photo of your yard",
                "Apply for the Valley Water rebate before removing any lawn",
                "Pass the pre-inspection, then finish within 90 days",
                "Plant it yourself or hire a landscaper, using the verdanti.ai plan",
                "Get your rebate check after the final inspection",
            ]), unsafe_allow_html=True)


def for_hoas():
    days = (date.fromisoformat(C.AB1572_DEADLINES["HOA / common interest development common areas"]) - _today()).days
    with st.container(key="hoaband"):
        left, right = st.columns([1, 1.15], gap="large")
        with left:
            st.markdown(f'<div class="section-title" style="margin-top:0">For HOAs</div>'
                        f'<div class="countdown"><span>{max(days, 0):,}</span> days until AB 1572</div>'
                        f'<p class="lead">From <b>January 1, 2029</b>, California law bans watering nonfunctional turf in '
                        f'HOA common areas with drinking water, including the strips along sidewalks, entries, medians and '
                        f'building edges.</p>'
                        f'<p class="lead">Board votes, budgets, member notices, bids and installation take months, and '
                        f'Valley Water\'s rebate (up to ${C.REBATE_CAP["multifamily_5plus"]:,} per site) is only funded '
                        f'until June 30, 2027 or until it runs out. Communities that start now get paid to comply.</p>',
                        unsafe_allow_html=True)
            st.button("Plan our common areas  →", type="primary", on_click=go_as, args=("studio", "HOA"), key="cta_hoa")
        with right:
            st.markdown(roadmap([
                "verdanti.ai designs every common-area lawn using your approved plant list",
                "The board reviews the designs and votes",
                "Apply for the Valley Water rebate and pass the pre-inspection",
                "Collect landscaper bids with the verdanti.ai plan",
                "Phased installation before 2029",
            ], dark=True), unsafe_allow_html=True)


FAQS = [
    ("Do I have to replace my whole lawn?",
     "No. Outline only what you want to change: a parkway strip, one side yard or just the front. Each area is designed separately."),
    ("Do I really have to apply before I start?",
     "Yes. Valley Water requires an application and pre-inspection before any lawn is removed. Projects started early don't qualify, "
     "and sites that are denied can't reapply for three years."),
    ("Will the rebate cover the whole project?",
     "Sometimes most of it. At $2 or more per square foot, a 500 sq ft lawn earns at least $1,000. Doing it yourself typically "
     "costs about $3 to $8 per square foot, so the rebate can cover a quarter to two-thirds. Hiring a landscaper in California "
     "typically runs $15 to $25 per square foot, so the rebate covers about a tenth. Each design in the studio shows the "
     "numbers for your own lawn."),
    ("Will a water-wise garden look brown and dead in summer?",
     "Not when it's designed well. The plant list mixes evergreen shrubs, grasses and flowers with different bloom seasons, so "
     "something looks good year-round. Plants need regular water their first year while roots establish."),
    ("What happens to my sprinklers?",
     "Spray sprinklers are usually converted to drip irrigation, which waters roots directly. Valley Water also offers rebates "
     "for drip conversion and smart controllers."),
    ("Can my HOA stop me from replacing my lawn?",
     "California law limits HOAs from banning water-efficient landscaping on your own lot, though they can still have design "
     "guidelines. Check your HOA's rules, and upload their approved plant list in the studio."),
    ("Is the preview really my yard?",
     "Yes. The AI only repaints the area you outline, and the app restores every pixel of your house, trees and paths from your photo."),
    ("What happens to my photos?",
     "Your project saves to a private link so you can come back to it, and you can delete it anytime on My designs. "
     "Photos are sent to OpenAI to create the design; OpenAI doesn't use them for training."),
]


def faqs():
    st.markdown('<div class="section-title">FAQs</div>', unsafe_allow_html=True)
    with st.container(key="faq"):
        for q, a in FAQS:
            with st.expander(q):
                st.markdown(a.replace("$", "\\$"))


def render():
    photo = hero_photo()
    photo_hero(photo) if photo else dark_hero()
    st.markdown('<div class="trust"><div class="t">Complies with</div><div class="row">'
                '<span>Valley Water Rebate Program</span><span>California MWELO</span>'
                '<span>AB 1572</span><span>CIMIS climate data</span></div></div>', unsafe_allow_html=True)
    pairs = gallery_pairs()
    if len(pairs) > 1:
        st.markdown('<div class="section-title">Real yards, redesigned</div>', unsafe_allow_html=True)
        cols = st.columns(2, gap="large")
        for i, (name, b, a) in enumerate(pairs[1:5]):
            with cols[i % 2]:
                theme.before_after(Image.open(b), Image.open(a))
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    for_homeowners()
    st.markdown('<div style="height:2.4rem"></div>', unsafe_allow_html=True)
    for_hoas()
    faqs()
    with st.container(key="floatcta"):
        st.button("Design my lawn  →", on_click=go, args=("studio",), key="floatbtn")
    theme.footer()
