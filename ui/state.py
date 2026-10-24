"""Session state, settings, access code and spending limits."""
import os
from datetime import date
import streamlit as st
from engine import config as C
from engine.plants import default_palette

OTHER_PAGES = {"privacy"}          # reachable from the footer, not the nav
PAGES = {"home": "Home", "studio": "Design studio", "plan": "Rebate plan",
         "plants": "Plant library", "saved": "My designs"}


def init():
    ss = st.session_state
    ss.setdefault("page", "home")
    ss.setdefault("areas", [])
    ss.setdefault("palette", list(default_palette()))
    ss.setdefault("palette_name", "Valley Water starter palette")
    ss.setdefault("property_type", "Independent homeowner")
    ss.setdefault("city", "Palo Alto")
    # Streamlit forgets a widget's value when its page isn't shown; re-assigning keeps
    # residence type and city across pages.
    ss["property_type"], ss["city"] = ss["property_type"], ss["city"]
    if ss["property_type"] not in C.PROPERTY_TYPES:      # value from an older version of the app
        ss["property_type"] = "Independent homeowner"
    if ss["page"] not in PAGES and ss["page"] not in OTHER_PAGES:
        ss["page"] = "home"
    if "pid" not in ss:                       # first run of this browser session
        ss["pid"], ss["saved_ids"] = None, {}
        pid = st.query_params.get("p")
        if pid:
            open_project(pid)


# ── saved projects (backend in engine/store.py) ──────────────────────────────
def open_project(pid: str) -> bool:
    from engine import store
    ss = st.session_state
    try:
        got = store.load_project(pid)
    except Exception as ex:
        ss["store_error"] = f"Couldn't load the saved project: {ex}"
        return False
    if not got:
        ss["store_error"] = "That project link wasn't found. It may have been deleted."
        st.query_params.pop("p", None)
        return False
    settings_, areas, saved = got
    ss["pid"], ss["areas"], ss["saved_ids"] = pid, areas, saved
    if settings_.get("property_type") in C.PROPERTY_TYPES:
        ss["property_type"] = settings_["property_type"]
    if settings_.get("city"):
        ss["city"] = settings_["city"]
    if settings_.get("palette"):
        ss["palette"], ss["palette_name"] = settings_["palette"], settings_.get("palette_name", "Custom list")
    st.query_params["p"] = pid
    ss.pop("store_error", None)
    return True


def autosave():
    """Called at the end of every run: saves the project if anything changed.
    A project is created (and its link put in the URL) when the first lawn area is added."""
    from engine import store
    ss = st.session_state
    if not ss["areas"] and not ss["pid"]:
        return
    if not ss["pid"]:
        ss["pid"] = store.new_id()
        ss["saved_ids"] = {}
    if st.query_params.get("p") != ss["pid"]:
        st.query_params["p"] = ss["pid"]
    from engine import jobs
    try:
        with jobs.SAVE_LOCK:              # a finished background design may be saving too
            ss["saved_ids"] = store.save_project(ss["pid"], project_settings(), ss["areas"], ss["saved_ids"])
        ss.pop("store_error", None)
    except Exception as ex:
        ss["store_error"] = f"Autosave failed: {ex}"


def project_settings() -> dict:
    ss = st.session_state
    custom = not ss["palette_name"].startswith("Valley Water")
    return {"property_type": ss["property_type"], "city": ss["city"],
            "palette_name": ss["palette_name"], "palette": ss["palette"] if custom else None}


def new_project():
    ss = st.session_state
    ss["pid"], ss["saved_ids"], ss["areas"] = None, {}, []
    st.query_params.pop("p", None)


def delete_project():
    from engine import store
    ss = st.session_state
    if ss["pid"]:
        store.delete_project(ss["pid"])
    new_project()


def go(page: str):
    st.session_state["page"] = page


def go_as(page: str, property_type: str):
    """Navigate and set the residence type (e.g. HOA buttons open the studio in HOA mode)."""
    st.session_state["property_type"] = property_type
    st.session_state["page"] = page


def settings():
    ss = st.session_state
    return ss["property_type"], ss["city"]


# ── access code ──────────────────────────────────────────────────────────────
def has_key() -> bool:
    return bool(os.getenv("OPENAI_API_KEY"))


def needs_code() -> bool:
    return bool(os.getenv("APP_PASSCODE"))


def ai_unlocked() -> bool:
    return has_key() and (not needs_code() or st.session_state.get("unlocked", False))


def try_unlock(code: str) -> bool:
    ok = code.strip() == os.getenv("APP_PASSCODE", "").strip()
    st.session_state["unlocked"] = ok
    return ok


# ── spending limits ──────────────────────────────────────────────────────────
@st.cache_resource
def _daily_counter():
    return {"day": date.today(), "n": 0}      # shared by all visitors on this server


def usage_left() -> tuple[int, str]:
    c = _daily_counter()
    if c["day"] != date.today():
        c["day"], c["n"] = date.today(), 0
    if c["n"] >= C.DAILY_DESIGN_LIMIT:
        return 0, "Today's design limit for this demo has been reached. Please try again tomorrow."
    left = C.SESSION_DESIGN_LIMIT - st.session_state.get("designs_used", 0)
    return max(left, 0), ("" if left > 0 else f"Demo limit: {C.SESSION_DESIGN_LIMIT} designs per visit.")


def count_usage():
    _daily_counter()["n"] += 1
    st.session_state["designs_used"] = st.session_state.get("designs_used", 0) + 1
