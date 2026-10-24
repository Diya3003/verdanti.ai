"""Visual design system: fonts, colors, and reusable HTML components.

Direction: modern landscape-design studio. Deep forest-green bands, warm linen backgrounds,
sage and clay accents, editorial serif headlines (Fraunces), clean sans body (Inter), small
monospaced labels (JetBrains Mono), rounded cards, pill buttons, generous whitespace.
"""
import base64, io
import streamlit as st
from PIL import Image

FOREST, MOSS, SAGE, LINEN, PAPER, CLAY, INK, MUTED, LIME = (
    "#17332A", "#2E5A43", "#A9B98F", "#F4F1EA", "#FBF9F4", "#C26A3D", "#1D2A22", "#6E6B5E", "#D3E27A")

GRAIN = ("url(\"data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='160' height='160'>"
         "<filter id='n'><feTurbulence type='fractalNoise' baseFrequency='.85' numOctaves='3'/></filter>"
         "<rect width='100%' height='100%' filter='url(%23n)' opacity='.09'/></svg>\")")

CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,300;9..144,500;9..144,600&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@500&display=swap');

/* ── chrome off ── */
header[data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stDecoration"],
footer, #MainMenu {{ display: none !important; }}
.stApp {{ background: {LINEN}; }}
.block-container {{ max-width: 1180px; padding: 1.2rem 2rem 4rem; }}

/* ── type ── */
.stApp, .stApp p, .stApp li, .stApp label, .stApp input, .stApp textarea, .stApp button,
.stApp td, .stApp th, .stMarkdown {{ font-family: 'Inter', system-ui, sans-serif; color: {INK}; }}
.stApp h1, .stApp h2, .stApp h3, .display {{ font-family: 'Fraunces', Georgia, serif !important;
  font-weight: 500; letter-spacing: -0.015em; color: {INK}; }}
.eyebrow {{ font-family: 'JetBrains Mono', monospace; font-size: .72rem; letter-spacing: .14em;
  text-transform: uppercase; color: {MOSS}; margin-bottom: .6rem; }}
.lead {{ font-size: 1.12rem; line-height: 1.65; color: {MUTED}; max-width: 38rem; }}
.muted {{ color: {MUTED}; font-size: .9rem; }}

/* ── buttons ── */
.stButton button, .stDownloadButton button, .stFormSubmitButton button {{
  border-radius: 999px; padding: .55rem 1.25rem; font-weight: 600; border: 1px solid #D8D1BF;
  background: {PAPER}; color: {INK}; transition: all .15s ease; }}
.stButton button:hover, .stDownloadButton button:hover {{ border-color: {MOSS}; color: {MOSS}; }}
button[data-testid="stBaseButton-primary"], button[data-testid="stBaseButton-primaryFormSubmit"] {{
  background: {FOREST} !important; color: {LINEN} !important; border: none !important; }}
button[data-testid="stBaseButton-primary"]:hover {{ background: {MOSS} !important; }}
button[data-testid="stBaseButton-primary"]:disabled {{ background: #B9B5A6 !important; }}

.stButton button p, .stDownloadButton button p, .stFormSubmitButton button p {{ color: inherit !important;
  font-weight: inherit; }}
button[data-testid="stBaseButton-tertiary"] {{ border: none !important; background: transparent !important;
  border-radius: 0 !important; box-shadow: none !important; }}

/* ── nav ── */
.st-key-nav {{ background: rgba(251,249,244,.92); border: 1px solid #E6DFCF; border-radius: 18px;
  padding: .45rem 1rem; margin-bottom: .9rem; box-shadow: 0 6px 24px rgba(23,51,42,.06); }}
.st-key-nav_cta button {{ background: {LIME} !important; color: {FOREST} !important; border: none !important; }}
.st-key-nav_cta button p {{ color: {FOREST} !important; font-weight: 600; }}
.st-key-nav_cta button:hover {{ background: #C4D660 !important; }}

/* ── rebate band (announcement strip) ── */
.rebate-band {{ background: {MOSS}; color: {LINEN}; border-radius: 14px; padding: .7rem 1.2rem;
  font-size: .9rem; display: flex; gap: .9rem; align-items: center; flex-wrap: wrap; margin-bottom: 1.4rem; }}
.rebate-band b {{ color: {LIME}; }}
.rebate-band .tag {{ font-family: 'JetBrains Mono', monospace; font-size: .64rem; letter-spacing: .12em;
  background: {LIME}; color: {FOREST}; border-radius: 99px; padding: 2px 9px; }}

/* ── photo hero with frosted card ── */
.st-key-herophoto {{ border-radius: 28px; min-height: 600px; padding: 2rem; justify-content: flex-end;
  background-size: cover; background-position: center; }}
.st-key-herocard {{ background: rgba(248,246,239,.80); backdrop-filter: blur(14px); -webkit-backdrop-filter: blur(14px);
  border: 1px solid rgba(255,255,255,.5); border-radius: 22px; padding: 2.2rem 2.2rem 1.8rem; max-width: 640px; }}
.st-key-herocard h1 {{ font-size: clamp(2.2rem, 4vw, 3.4rem); line-height: 1.05; font-weight: 400; margin: 0 0 .9rem; }}
.st-key-herocard h1 em {{ font-style: italic; color: {MOSS}; }}
.st-key-herocard .lead {{ color: #4E5348; font-size: 1.05rem; }}
.st-key-herocard .chip {{ border-color: #CFC7B2; color: {INK}; background: rgba(255,255,255,.55); }}
.st-key-herocard .chip b {{ color: {MOSS}; }}
.photo-credit {{ position: absolute; right: 1.4rem; bottom: 1.1rem; background: rgba(0,0,0,.45); color: #fff;
  font-size: .72rem; padding: 3px 10px; border-radius: 99px; }}

/* ── trust row ── */
.trust {{ text-align: center; margin: 2.6rem 0 .4rem; }}
.trust .t {{ font-family: 'JetBrains Mono', monospace; font-size: .68rem; letter-spacing: .14em; text-transform: uppercase; color: {MUTED}; }}
.trust .row {{ display: flex; justify-content: center; gap: 2.6rem; flex-wrap: wrap; margin-top: .8rem;
  font-family: 'Fraunces', serif; font-size: 1.25rem; color: #8A8676; }}

/* ── floating CTA ── */
.st-key-floatcta {{ position: fixed; right: 26px; bottom: 26px; z-index: 1000; width: auto !important; }}
.st-key-floatcta button {{ background: {FOREST} !important; color: {LINEN} !important; border: none !important;
  box-shadow: 0 10px 30px rgba(23,51,42,.35); padding: .75rem 1.4rem !important; }}
.st-key-floatcta button p {{ color: {LINEN} !important; }}
.st-key-nav button[data-testid="stBaseButton-tertiary"] {{ font-weight: 500; color: {MUTED};
  padding: .35rem .2rem; border-radius: 0; }}
.st-key-nav button[data-testid="stBaseButton-tertiary"]:hover {{ color: {FOREST}; }}
.nav-active button[data-testid="stBaseButton-tertiary"] {{ color: {FOREST} !important;
  border-bottom: 2px solid {CLAY} !important; }}
.brand {{ display: flex; align-items: center; gap: .6rem; margin: 0; white-space: nowrap; }}
.brand .wm {{ font-family: 'Fraunces', serif; font-size: 1.45rem; font-weight: 600; color: {FOREST};
  letter-spacing: -.01em; line-height: 1; }}
.brand .wm span {{ color: {CLAY}; }}
.brand img {{ height: 46px; width: auto; display: block; }}
.st-key-nav [data-testid="stColumn"]:first-child [data-testid="stMarkdownContainer"],
.st-key-nav [data-testid="stColumn"]:first-child [data-testid="stMarkdownContainer"] p {{ margin: 0 !important; }}
.brand small {{ font-family: 'JetBrains Mono', monospace; font-size: .58rem; letter-spacing: .12em; line-height: 1;
  color: {CLAY}; border: 1px solid {CLAY}; border-radius: 99px; padding: 4px 7px 3px; }}

/* ── hero ── */
.st-key-hero {{ background: {FOREST} {GRAIN}; border-radius: 28px; padding: 3.4rem 3rem 3rem;
  position: relative; overflow: hidden; }}
.st-key-hero h1, .st-key-hero p, .st-key-hero .eyebrow, .st-key-hero span {{ color: {LINEN} !important; }}
.st-key-hero .eyebrow {{ color: {LIME} !important; }}
.st-key-hero h1 {{ font-size: clamp(2.4rem, 4.6vw, 3.9rem); line-height: 1.04; font-weight: 400; margin: 0 0 1rem; }}
.st-key-hero h1 em {{ font-style: italic; color: {LIME}; }}
.st-key-hero .lead {{ color: #C9D2C3 !important; }}
.st-key-hero button[data-testid="stBaseButton-primary"] {{ background: {LIME} !important; color: {FOREST} !important; }}
.st-key-hero button[data-testid="stBaseButton-primary"] p {{ color: {FOREST} !important; }}
.st-key-hero button[data-testid="stBaseButton-secondary"] p {{ color: inherit !important; }}
.st-key-hero button[data-testid="stBaseButton-secondary"] {{ background: transparent; color: {LINEN};
  border-color: #5E7B69; }}
.st-key-hero button[data-testid="stBaseButton-secondary"]:hover {{ color: {LIME}; border-color: {LIME}; }}
.chips {{ display: flex; gap: .6rem; flex-wrap: wrap; margin-top: 1.6rem; }}
.chip {{ border: 1px solid #4C6A58; border-radius: 99px; padding: .35rem .85rem; font-size: .82rem; color: #DCE3D6; }}
.chip b {{ color: {LIME}; font-weight: 600; }}

/* ── cards / sections ── */
.card {{ background: {PAPER}; border: 1px solid #E4DDCC; border-radius: 20px; padding: 1.5rem 1.6rem; height: 100%;
  min-height: 15.5rem; }}
.step-n {{ font-family: 'Fraunces', serif; font-size: 2.2rem; color: {CLAY}; line-height: 1; }}
.card h4 {{ font-family: 'Fraunces', serif; font-size: 1.2rem; font-weight: 500; margin: .7rem 0 .4rem; }}
.card p {{ color: {MUTED}; font-size: .93rem; line-height: 1.55; margin: 0; }}
.card p.how {{ margin-top: .8rem; padding-top: .7rem; border-top: 1px dashed #D9D1BE; font-size: .8rem; color: #85826F; }}
.st-key-nav_studio button {{ background: {LIME} !important; color: #111 !important; border-radius: 999px !important;
  border: none !important; font-weight: 600 !important; }}
.st-key-nav_studio button p {{ color: #111 !important; font-weight: 600 !important; }}
.st-key-nav_studio button:hover {{ background: #C4D660 !important; }}
.band {{ background: {MOSS} {GRAIN}; border-radius: 24px; padding: 2.2rem 2.4rem; color: {LINEN}; }}
.band .stat {{ font-family: 'Fraunces', serif; font-size: 2.6rem; color: {LIME}; line-height: 1.05; }}
.band .lbl {{ color: #D8E0D2; font-size: .9rem; margin-top: .3rem; }}
.section-title {{ font-family: 'Fraunces', serif; font-size: 2.1rem; font-weight: 400; margin: 3.2rem 0 1.2rem; }}
.kpi {{ background: {PAPER}; border: 1px solid #E4DDCC; border-radius: 18px; padding: 1.1rem 1.3rem; }}
.kpi .v {{ font-family: 'Fraunces', serif; font-size: 1.9rem; color: {FOREST}; }}
.kpi .l {{ font-family: 'JetBrains Mono', monospace; font-size: .66rem; letter-spacing: .12em;
  text-transform: uppercase; color: {MUTED}; }}
.pill {{ display:inline-block; padding: 2px 10px; border-radius: 99px; font-size: .74rem; font-weight: 600; }}
.ok {{ background: #DDE8D2; color: {MOSS}; }} .no {{ background: #F3DCCF; color: #8A3B22; }}
.mid {{ background: #F1E6C6; color: #7A5B12; }}

/* ── timeline (how it works) ── */
.timeline {{ display: grid; grid-template-columns: repeat(5, 1fr); gap: 1.6rem; position: relative; margin-top: .6rem; }}
.timeline::before {{ content: ""; position: absolute; top: 19px; left: 20px; right: 20px; height: 2px;
  background: repeating-linear-gradient(90deg, {SAGE} 0 8px, transparent 8px 14px); }}
.tl-step {{ position: relative; }}
.tl-dot {{ width: 40px; height: 40px; border-radius: 50%; background: {FOREST}; color: {LIME}; display: flex;
  align-items: center; justify-content: center; font-family: 'Fraunces', serif; font-size: 1.1rem;
  box-shadow: 0 0 0 6px {LINEN}; position: relative; }}
.tl-step h4 {{ font-family: 'Fraunces', serif; font-weight: 500; font-size: 1.12rem; margin: 1rem 0 .35rem; color: {INK}; }}
.tl-step p {{ color: {MUTED}; font-size: .9rem; line-height: 1.5; margin: 0; }}
.tl-step p.how {{ font-size: .78rem; color: #8F8B78; margin-top: .55rem; font-style: italic; }}
.divider {{ height: 1px; background: #DDD5C2; margin: 3.6rem 0 2.8rem; }}

/* ── roadmap (vertical) ── */
.roadmap {{ position: relative; padding-left: .2rem; }}
.rm-row {{ display: flex; gap: 1.1rem; position: relative; padding-bottom: 1.5rem; }}
.rm-row:not(:last-child)::before {{ content: ""; position: absolute; left: 17px; top: 38px; bottom: 0; width: 2px; background: #D3CBB6; }}
.rm-dot {{ flex: 0 0 36px; height: 36px; border-radius: 50%; border: 2px solid {MOSS}; color: {MOSS};
  display: flex; align-items: center; justify-content: center; font-weight: 600; font-size: .9rem; background: {LINEN}; }}
.rm-t {{ font-family: 'Fraunces', serif; font-size: 1.15rem; color: {INK}; margin-top: .3rem; }}
.rm-d {{ color: {MUTED}; font-size: .92rem; line-height: 1.5; margin-top: .15rem; }}
.roadmap.dark .rm-row:not(:last-child)::before {{ background: #4C6A58; }}
.roadmap.dark .rm-dot {{ border-color: {LIME}; color: {LIME}; background: {FOREST}; }}
.roadmap.dark .rm-t {{ color: {LINEN}; }}
.roadmap.dark .rm-d {{ color: #BFCABB; }}

.roadmap .rm-t {{ margin-top: .45rem; font-size: 1.08rem; line-height: 1.4; }}

/* ── homeowner band (light) ── */
.st-key-homeband {{ background: #E6EDD5 {GRAIN}; border-radius: 28px; padding: 3rem 3rem 2.4rem; }}
.st-key-homeband .lead {{ color: #3C4A3F; max-width: none; font-size: 1.02rem; }}
.st-key-homeband .rm-dot {{ background: {MOSS}; color: #fff; border-color: {MOSS}; }}
.st-key-homeband .rm-row:not(:last-child)::before {{ background: #B9C79E; }}

.st-key-footlinks button {{ padding: 0 !important; min-height: 0 !important; }}
.st-key-footlinks button p {{ font-size: .8rem !important; color: {MUTED} !important; text-decoration: underline; }}

/* cost explainer under the numbers */
[class*="st-key-costnote"] {{ background: #EEF2E2; border-radius: 14px; padding: .8rem 1rem; margin: .6rem 0 .4rem; }}
[class*="st-key-costnote"] p {{ margin: 0; font-size: .95rem; color: #2C3A30; }}

/* ── HOA band ── */
.st-key-hoaband {{ background: {FOREST} {GRAIN}; border-radius: 28px; padding: 3rem 3rem 2.4rem; }}
.st-key-hoaband .section-title, .st-key-hoaband b {{ color: {LINEN}; }}
.st-key-hoaband .lead {{ color: #C9D2C3; max-width: none; font-size: 1.02rem; }}
.countdown {{ font-family: 'JetBrains Mono', monospace; font-size: .75rem; letter-spacing: .14em; text-transform: uppercase;
  color: #C9D2C3; margin: -.4rem 0 1.2rem; }}
.countdown span {{ font-family: 'Fraunces', serif; font-size: 3.4rem; letter-spacing: 0; color: {LIME};
  text-transform: none; margin-right: .5rem; vertical-align: middle; }}
.st-key-hoaband button[data-testid="stBaseButton-primary"] {{ background: {LIME} !important; }}
.st-key-hoaband button[data-testid="stBaseButton-primary"] p {{ color: {FOREST} !important; }}

/* ── FAQ as clean dividers, not boxes ── */
.st-key-faq [data-testid="stExpander"], .st-key-faq details {{ background: transparent !important; border: none !important;
  border-bottom: 1px solid #DDD5C2 !important; border-radius: 0 !important; box-shadow: none !important; }}
.st-key-faq details summary:hover {{ background: transparent !important; }}
.st-key-faq details[open] summary {{ background: transparent !important; }}
.st-key-faq [data-testid="stExpanderDetails"] {{ padding-left: 0; }}
.st-key-faq [data-testid="stExpander"] summary {{ padding: 1.05rem 0; }}
.st-key-faq [data-testid="stExpander"] summary p {{ font-family: 'Fraunces', serif; font-size: 1.15rem; }}
.st-key-faq [data-testid="stExpander"] [data-testid="stExpanderDetails"] p {{ color: {MUTED}; }}

/* ── program tiles (rebates page) ── */
.pg-logo {{ height: 92px; display: flex; align-items: center; justify-content: center; background: #fff;
  border-radius: 14px; border: 1px solid #EEE8DA; margin-bottom: .8rem; padding: .8rem; }}
.pg-logo img {{ max-height: 100%; max-width: 100%; object-fit: contain; }}
.pg-logo .pg-mark {{ flex: 0 0 56px; height: 56px; font-size: 1.15rem; }}
.pg-logo.sm {{ height: 52px; width: 52px; padding: .35rem; margin: 0; flex: 0 0 52px; }}
.pg-logo.sm .pg-mark {{ flex: 0 0 40px; height: 40px; font-size: .85rem; }}
[class*="st-key-prog_"] .pg-name {{ text-align: center; font-size: 1.02rem; min-height: 2.5rem; }}
[class*="st-key-prog_"] .stButton {{ display: flex; justify-content: center; }}
[class*="st-key-prog_"] {{ background: {PAPER}; border: 1px solid #E4DDCC; border-radius: 20px; padding: 1rem 1rem .4rem;
  transition: all .15s ease; height: 100%; }}
[class*="st-key-prog_"]:hover {{ border-color: {MOSS}; box-shadow: 0 8px 26px rgba(23,51,42,.08); transform: translateY(-2px); }}
.pg-top {{ display: flex; align-items: center; gap: .75rem; }}
.pg-mark {{ flex: 0 0 44px; height: 44px; border-radius: 12px; background: {FOREST}; color: {LIME}; display: flex;
  align-items: center; justify-content: center; font-family: 'Fraunces', serif; font-weight: 600; font-size: .95rem; }}
.pg-mark.free {{ background: {SAGE}; color: {FOREST}; }}
.pg-org {{ font-size: .78rem; color: {MUTED}; }}
.pg-name {{ font-family: 'Fraunces', serif; font-size: 1.12rem; color: {INK}; line-height: 1.2; }}
.pg-amt {{ font-family: 'Fraunces', serif; font-size: 1.6rem; color: {MOSS}; margin: .8rem 0 .3rem; }}
.pg-sum {{ color: {MUTED}; font-size: .88rem; line-height: 1.5; min-height: 3.9rem; }}
[class*="st-key-prog_"] button[data-testid="stBaseButton-tertiary"] p {{ color: {CLAY} !important; font-weight: 600; }}
.note {{ border-left: 3px solid {CLAY}; padding: .2rem 0 .2rem 1rem; color: {INK}; font-size: 1rem; line-height: 1.6;
  margin: .4rem 0 1.6rem; max-width: 46rem; }}

/* ── Streamlit widgets ── */
[data-testid="stExpander"] {{ background: {PAPER}; border: 1px solid #E4DDCC !important; border-radius: 18px !important; }}
[data-testid="stForm"] {{ background: {PAPER}; border: 1px solid #E4DDCC; border-radius: 20px; padding: 1.4rem; }}
[data-testid="stMetricValue"] {{ font-family: 'Fraunces', serif; color: {FOREST}; }}
[data-testid="stFileUploaderDropzone"] {{ background: {LINEN}; border: 1.5px dashed #CFC6B0; border-radius: 16px; }}
.stTextInput input, .stNumberInput input, .stTextArea textarea, [data-baseweb="select"] > div {{
  background: {PAPER} !important; border-radius: 12px !important; }}
table.plants {{ width: 100%; border-collapse: collapse; font-size: .92rem; }}
table.plants th {{ text-align: left; font-family: 'JetBrains Mono', monospace; font-size: .66rem;
  letter-spacing: .1em; text-transform: uppercase; color: {MUTED}; border-bottom: 1px solid #DDD5C2; padding: .5rem .4rem; }}
table.plants td {{ border-bottom: 1px solid #ECE6D8; padding: .6rem .4rem; vertical-align: top; }}
.footer {{ margin-top: 4rem; padding-top: 1.4rem; border-top: 1px solid #E2DBCA; color: {MUTED}; font-size: .82rem; }}
/* ── phones ── */
@media (max-width: 640px) {{
  .block-container {{ padding: .6rem .9rem 3rem; }}
  .st-key-nav [data-testid="stHorizontalBlock"] {{ flex-wrap: wrap !important; gap: 0 .2rem !important; }}
  .st-key-nav [data-testid="stColumn"] {{ flex: 1 0 100% !important; width: 100% !important; min-width: 0 !important; }}
  .st-key-nav button[data-testid="stBaseButton-tertiary"] {{ font-size: .82rem; padding: .2rem .35rem; }}
  .brand {{ font-size: 1.15rem; }}
  .brand img {{ height: 40px; }}
  .st-key-herophoto {{ min-height: 0; padding: .8rem; }}
  .st-key-herocard {{ padding: 1.4rem 1.2rem 1rem; }}
  .st-key-herocard .lead {{ font-size: .95rem; }}
  .rebate-band {{ font-size: .82rem; }}
  .st-key-floatcta {{ display: none !important; }}          /* hero and bands already have buttons */
  /* nav: brand on top, the five links on one swipeable line */
  .st-key-navlinks [data-testid="stHorizontalBlock"] {{ flex-wrap: nowrap !important; overflow-x: auto; gap: .1rem !important;
    scrollbar-width: none; -webkit-overflow-scrolling: touch; }}
  .st-key-navlinks [data-testid="stHorizontalBlock"]::-webkit-scrollbar {{ display: none; }}
  .st-key-nav .st-key-navlinks [data-testid="stColumn"],
  .st-key-nav .st-key-navlinks [data-testid="stColumn"]:first-child {{ flex: 0 0 auto !important; width: auto !important; min-width: 0 !important; }}
  .st-key-nav button[data-testid="stBaseButton-tertiary"], .st-key-nav_studio button {{ padding: .22rem .22rem !important; min-height: 0 !important; }}
  .st-key-nav button p {{ font-size: .72rem !important; white-space: nowrap; letter-spacing: -.005em; }}
  .st-key-nav {{ padding: .45rem .55rem !important; }}
  .st-key-navlinks [data-testid="stHorizontalBlock"] {{ justify-content: space-between; gap: 0 !important; }}
  .st-key-homeband, .st-key-hoaband {{ padding: 1.8rem 1.3rem 1.4rem !important; border-radius: 22px !important; }}
  /* trust row: compact chips */
  .trust {{ margin-top: 1.8rem; }}
  .trust .row {{ gap: .4rem .5rem; }}
  .trust .row span {{ font-size: .82rem !important; padding: .25rem .7rem; border: 1px solid #E0D8C5; border-radius: 99px; }}
  /* number cards: two per row instead of four tall cards */
  [data-testid="stHorizontalBlock"]:has(> [data-testid="stColumn"] .kpi) {{ flex-wrap: wrap !important; gap: .6rem !important; }}
  [data-testid="stHorizontalBlock"]:has(> [data-testid="stColumn"] .kpi) > [data-testid="stColumn"] {{
    flex: 1 1 calc(50% - .6rem) !important; width: calc(50% - .6rem) !important; min-width: 0 !important; }}
  .kpi {{ padding: .85rem 1rem; }} .kpi .v {{ font-size: 1.45rem; }} .kpi .l {{ font-size: .58rem; }}
  /* program tiles: two per row */
  [data-testid="stHorizontalBlock"]:has([class*="st-key-prog_"]) {{ flex-wrap: wrap !important; gap: .6rem !important; }}
  [data-testid="stHorizontalBlock"]:has([class*="st-key-prog_"]) > [data-testid="stColumn"] {{
    flex: 1 1 calc(50% - .6rem) !important; width: calc(50% - .6rem) !important; min-width: 0 !important; }}
  .pg-name {{ font-size: .9rem !important; }}
  /* plant table becomes cards */
  table.plants, table.plants tbody, table.plants tr, table.plants td {{ display: block; width: 100%; }}
  table.plants tr:first-child {{ display: none; }}
  table.plants tr {{ border: 1px solid #E4DDCC; border-radius: 14px; padding: .7rem .9rem; margin-bottom: .6rem; background: {PAPER}; }}
  table.plants td {{ border: none; padding: .12rem 0; }}
  table.plants td[data-l] {{ display: inline-block; width: auto; margin-right: .9rem; font-size: .88rem; }}
  table.plants td[data-l="Where"] {{ display: block; width: 100%; margin: .15rem 0; }}
  table.plants td[data-l]::before {{ content: attr(data-l) ": "; color: {MUTED}; font-size: .78rem; }}
  .section-title {{ font-size: 1.55rem !important; }}
  h1 {{ font-size: 2.1rem !important; }}
}}
</style>
"""

SPRIG = f"""<svg viewBox="0 0 320 300" width="100%" style="max-width:360px;display:block;margin:auto"
 fill="none" stroke="{SAGE}" stroke-width="1.6" stroke-linecap="round">
 <path d="M160 290 C158 220 150 160 132 96"/><path d="M160 290 C166 210 186 150 214 110"/>
 <path d="M160 290 C160 230 162 180 168 120"/>
 <path d="M132 96 c-30-6-48 8-56 26 c22 6 44-2 56-26z" fill="{SAGE}" fill-opacity=".14"/>
 <path d="M146 160 c-34 0-52 18-56 38 c26 2 46-12 56-38z" fill="{SAGE}" fill-opacity=".14"/>
 <path d="M214 110 c28-14 52-6 64 10 c-22 12-46 8-64-10z" fill="{SAGE}" fill-opacity=".14"/>
 <path d="M178 176 c30-10 54 2 62 20 c-24 8-46 0-62-20z" fill="{SAGE}" fill-opacity=".14"/>
 <path d="M168 120 c-6-30 6-50 22-60 c8 22 0 44-22 60z" fill="{SAGE}" fill-opacity=".14"/>
 <circle cx="168" cy="52" r="7" stroke="{LIME}"/><circle cx="216" cy="98" r="5" stroke="{LIME}"/>
 <circle cx="126" cy="86" r="5" stroke="{LIME}"/>
 <path d="M40 290 C44 262 52 246 62 236 M58 290 C58 266 64 252 74 244 M262 290 C258 262 250 248 240 238 M244 290 C246 268 240 254 230 246" stroke-width="1.2"/>
 <path d="M20 291 H300" stroke="#4C6A58"/>
</svg>"""


def brand() -> str:
    """Nav logo: data/logo.(svg|png|webp|jpg) if present, otherwise the text wordmark."""
    from pathlib import Path
    root = Path(__file__).resolve().parent.parent / "data"
    for ext, mime in (("svg", "image/svg+xml"), ("png", "image/png"), ("webp", "image/webp"), ("jpg", "image/jpeg")):
        p = root / f"logo.{ext}"
        if p.exists():
            import base64
            return (f'<div class="brand"><img alt="verdanti.ai" src="data:{mime};base64,'
                    f'{base64.b64encode(p.read_bytes()).decode()}"><small>BETA</small></div>')
    return '<div class="brand"><span class="wm">verdanti.ai</span><small>BETA</small></div>'


def inject():
    st.markdown(CSS, unsafe_allow_html=True)


def img_b64(img: Image.Image, q=85) -> str:
    buf = io.BytesIO(); img.convert("RGB").save(buf, "JPEG", quality=q)
    return base64.b64encode(buf.getvalue()).decode()


def kpi(col, value, label):
    col.markdown(f'<div class="kpi"><div class="v">{value}</div><div class="l">{label}</div></div>',
                 unsafe_allow_html=True)


def badge(status):
    return {"exact": '<span class="pill ok">Rebate eligible</span>',
            "genus": '<span class="pill mid">Eligible · verify cultivar</span>',
            "none": '<span class="pill no">Not on rebate list</span>'}[status]


_ba = None


def before_after(before: Image.Image, after: Image.Image):
    """Drag-to-compare slider (ui/components/before_after). Before is resized to the render's
    size so they line up; the slider fits the image's shape at any screen width."""
    global _ba
    if _ba is None:
        from pathlib import Path
        _ba = st.components.v1.declare_component(
            "before_after", path=str(Path(__file__).resolve().parent / "components" / "before_after"))
    before = before.resize(after.size)
    a64, b64 = img_b64(after), img_b64(before)
    import hashlib
    _ba(after=f"data:image/jpeg;base64,{a64}", before=f"data:image/jpeg;base64,{b64}",
        w=after.width, h=after.height, max_h=620 if after.height > after.width else 520,
        key=hashlib.md5(a64[:2000].encode() + b64[-2000:].encode()).hexdigest(), default=None)


def footer():
    from ui import state
    st.markdown('<div class="footer">Estimates only. Valley Water\'s pre-inspection makes the final rebate decision. '
                'Built for Santa Clara Valley · Plant data: Valley Water Landscape Rebate Program.</div>',
                unsafe_allow_html=True)
    with st.container(key="footlinks"):
        st.button("Privacy", type="tertiary", on_click=state.go, args=("privacy",), key="foot_privacy")
