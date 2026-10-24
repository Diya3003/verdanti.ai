"""verdanti.ai, web app entry point.

Run:  streamlit run app.py
Config (env vars, .env file, or Streamlit secrets):
  OPENAI_API_KEY   required for AI design
  APP_PASSCODE     access code people must enter before AI designs run (protects your API budget)
  SUPABASE_URL / SUPABASE_KEY   optional: store saved projects in Supabase (otherwise ./storage)
"""
import os
import streamlit as st

st.set_page_config(page_title="verdanti.ai | Smarter landscapes. Less water.", page_icon=next((str(p) for p in __import__("pathlib").Path(__file__).parent.joinpath("data").glob("icon.png")), "🌱"), layout="wide",
                   initial_sidebar_state="collapsed")

try:
    from dotenv import load_dotenv; load_dotenv()
except ImportError:
    pass
for k in ("OPENAI_API_KEY", "APP_PASSCODE", "OPENAI_TEXT_MODEL", "OPENAI_IMAGE_MODEL",
          "SESSION_DESIGN_LIMIT", "DAILY_DESIGN_LIMIT", "SUPABASE_URL", "SUPABASE_KEY", "STORE_DIR"):
    try:
        if k in st.secrets and not os.getenv(k):
            os.environ[k] = str(st.secrets[k])
    except Exception:
        pass
if os.getenv("FAKE_OPENAI"):          # developer mode: canned AI responses, no API cost
    os.environ.setdefault("OPENAI_API_KEY", "fake")
    import tests.fake_openai  # noqa: F401
try:
    from pillow_heif import register_heif_opener   # iPhone HEIC photos
    register_heif_opener()
except ImportError:
    pass

from ui import theme, state, home, studio, pages_misc

APP_NAME = "verdanti.ai"

state.init()
theme.inject()

# ── top navigation ──
page = st.session_state["page"]
if page != "studio":
    st.markdown(f"<style>.st-key-nav_{page} button {{ color: {theme.FOREST} !important; "
                f"border-bottom: 2px solid {theme.CLAY} !important; font-weight: 600 !important; }}</style>",
                unsafe_allow_html=True)
with st.container(key="nav"):
    left, right = st.columns([2.6, len(state.PAGES)], vertical_alignment="center")
    left.markdown(theme.brand(), unsafe_allow_html=True)
    with right.container(key="navlinks"):        # its own row, so phones can swipe it sideways
        for col, (pid, label) in zip(st.columns(len(state.PAGES), vertical_alignment="center"), state.PAGES.items()):
            with col.container(key=f"nav_{pid}"):
                st.button(label, type="tertiary", on_click=state.go, args=(pid,), use_container_width=True)

if page != "studio" and (st.session_state.get("_bg_ready") or any(a.get("job_id") for a in st.session_state["areas"])):
    studio.background_notice()

{"home": home.render, "studio": studio.render, "plan": pages_misc.plan,
 "plants": pages_misc.plants, "saved": pages_misc.saved, "privacy": pages_misc.privacy}.get(page, home.render)()

state.autosave()      # every change is saved to the backend (engine/store.py)
