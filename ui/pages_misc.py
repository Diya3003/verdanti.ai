"""Rebate plan, plant library and how-it-works pages."""
import base64
from pathlib import Path
from datetime import date
import pandas as pd
import streamlit as st
from engine import config as C
from engine.plants import search_valley_water, SUNS
from engine.impact import evaluate_design, capped_rebate, ab1572_status
from ui import theme, state


def _program_dialog(p):
    st.markdown(f'<div class="pg-top"><div class="pg-logo sm">{_logo_html(p)}</div>'
                f'<div><div class="pg-org">{p["org"]}</div><div class="pg-amt" style="margin:0">{p["amount"]}</div></div></div>',
                unsafe_allow_html=True)
    esc = lambda t: t.replace("$", "\\$")      # stop "$3,000 … $100,000" rendering as math
    st.markdown(esc(p["summary"]))
    st.markdown("\n".join(f"- {esc(d)}" for d in p["details"]))
    st.caption(f"Contact: {p['contact']} · Amounts change, so confirm on the official page before you apply.")
    st.link_button("Open official page ↗", p["url"], type="primary", use_container_width=True)


LOGOS = Path(__file__).resolve().parent.parent / "data" / "logos"


def _logo_html(p) -> str:
    """data/logos/<logo>.png|jpg|svg if present, else an initials badge."""
    for ext in ("png", "jpg", "jpeg", "webp", "svg"):
        f = LOGOS / f"{p['logo']}.{ext}"
        if f.exists():
            mime = "image/svg+xml" if ext == "svg" else f"image/{'jpeg' if ext == 'jpg' else ext}"
            return f'<img src="data:{mime};base64,{base64.b64encode(f.read_bytes()).decode()}" alt="{p["org"]}">'
    return f'<div class="pg-mark{" free" if p["kind"] == "free" else ""}">{p["mark"]}</div>'


def _tiles(programs):
    cols = st.columns(4, gap="medium")
    for i, p in enumerate(programs):
        with cols[i % 4]:
            with st.container(key=f"prog_{p['id']}"):
                st.markdown(f'<div class="pg-logo">{_logo_html(p)}</div><div class="pg-name">{p["name"]}</div>',
                            unsafe_allow_html=True)
                if st.button("Details →", key=f"btn_{p['id']}", type="tertiary", use_container_width=True):
                    st.dialog(p["name"], width="large")(_program_dialog)(p)
            st.write("")


def plan():
    from engine.programs import for_user, rebate_cap
    ptype, city = state.settings()
    cap = C.PROPERTY_TYPES[ptype]["cap"]
    cap_usd = rebate_cap(city, "hoa" if ptype == "HOA" else "home")
    pal = st.session_state["palette"]
    done = [(a, evaluate_design(a["result"]["design"], pal, a["sqft"], city, cap))
            for a in st.session_state["areas"] if a["result"]]
    who = "hoa" if ptype == "HOA" else "home"
    st.markdown('<h1 style="margin-top:0">Rebates &amp; resources</h1>'
                f'<p class="lead">Valley Water pays at least ${C.REBATE_PER_SQFT:.0f} per square foot to replace lawn, '
                f'up to ${cap_usd:,} for {f"an HOA in {city}" if who == "hoa" else f"a home in {city}"}. The one rule people miss: '
                'apply and pass a pre-inspection <b>before</b> you remove any grass. Below are the programs available '
                f'to {"HOAs" if who == "hoa" else "homeowners"} in {city}. Tap one for details.</p>',
                unsafe_allow_html=True)

    if done:
        st.markdown('<div class="section-title" style="font-size:1.6rem">Your plan</div>', unsafe_allow_html=True)
        sqft = sum(a["sqft"] for a, _ in done)
        rebate = min(sum(e["rebate_usd"] for _, e in done), cap_usd)
        k = st.columns(4)
        theme.kpi(k[0], f"{sqft:,}", "sq ft of lawn")
        theme.kpi(k[1], f"{sum(e['gallons_saved'] for _, e in done):,.0f}", "gallons saved / yr")
        theme.kpi(k[2], f"${rebate:,.0f}+", "est. rebate (at $2/sq ft)")
        theme.kpi(k[3], sum(e["plant_count"] for _, e in done), "plants")
        st.write("")
        df = pd.DataFrame([{"Area": a["name"], "Sq ft": a["sqft"], "Sun": a["result"]["sun_used"],
                            "Plants": e["plant_count"], "Rebate coverage": f"{e['qualifying_coverage_pct']:.0%}",
                            "Eligible": "Yes" if e["rebate_eligible"] else "No",
                            "Gallons saved / yr": round(e["gallons_saved"])} for a, e in done])
        st.dataframe(df, hide_index=True, use_container_width=True)
        from engine.impact import cost_sentence
        with st.container(key="costnote_plan"):
            st.markdown("**What the rebate means:** " + cost_sentence(sqft, rebate))
        c1, _ = st.columns([1.2, 2])
        c1.link_button("Get a call with a contractor  →", "https://rescape.memberclicks.net/directory",
                       use_container_width=True)
        st.caption("Opens ReScape California's directory of landscape professionals trained in water-wise, "
                   "sustainable landscaping. Search your county and contact one for a quote.")

    progs = for_user(who, city)
    st.markdown('<div class="section-title" style="font-size:1.6rem">Rebates</div>', unsafe_allow_html=True)
    _tiles([p for p in progs if p["kind"] == "rebate"])
    st.markdown('<div class="section-title" style="font-size:1.6rem">Resources</div>', unsafe_allow_html=True)
    _tiles([p for p in progs if p["kind"] == "free"])
    if not done:
        st.write("")
        st.button("Design a lawn area to estimate your rebate  →", type="primary", on_click=state.go, args=("studio",))
    theme.footer()


def plants():
    st.markdown('<h1 style="margin-top:0">Plant library</h1>'
                '<p class="note"><b>Everything in this app is built on this list.</b> Every plant the designer picks, '
                'every coverage number and every rebate estimate comes from Valley Water\'s official list of '
                'rebate-qualifying plants: 2,700+ plants, each with its mature size. If a plant isn\'t here, '
                'it doesn\'t count toward your rebate.</p>', unsafe_allow_html=True)
    q = st.text_input("Search by scientific or common name", "sage", label_visibility="collapsed",
                      placeholder="Search: sage, manzanita, lavender…")
    res = search_valley_water(q, 80)
    if res:
        st.dataframe(pd.DataFrame([{"Scientific name": r["scientific"], "Common name": r["common"],
                                    "Coverage (sq ft)": r["coverage_sqft"], "CA native": "✓" if r["native_ca"] else "",
                                    "Invasive risk": "⚠" if r["invasive"] else "", "Type": ", ".join(r["types"])}
                                   for r in res]), hide_index=True, use_container_width=True)
    elif q:
        st.caption("No matches on the Valley Water list.")
    st.markdown(f'<div class="section-title">Current palette · {st.session_state["palette_name"]}</div>',
                unsafe_allow_html=True)
    sun = st.radio("Sun", SUNS, horizontal=True, label_visibility="collapsed")
    pal = [p for p in st.session_state["palette"] if sun in p["sun"]]
    st.dataframe(pd.DataFrame([{"Plant": p["botanical"], "Common name": p["common"],
                                "Rebate": {"exact": "Eligible", "genus": "Verify cultivar", "none": "No"}[p["rebate_status"]],
                                "Water": p.get("water", "low"), "CA native": "✓" if p["native_ca"] else ""}
                               for p in pal]), hide_index=True, use_container_width=True)
    theme.footer()


def _project_link(pid):
    base = ""
    try:
        base = (st.context.url or "").split("?")[0]
    except Exception:
        host = st.context.headers.get("host", "")
        base = f"https://{host}/" if host else ""
    return f"{base or 'https://<your-app-address>/'}?p={pid}"


def _open_area(ar_id):
    st.session_state["focus_area"] = ar_id
    state.go("studio")


def saved():
    ss = st.session_state
    st.markdown('<h1 style="margin-top:0">My designs</h1>', unsafe_allow_html=True)
    if ss.get("store_error"):
        st.warning(ss["store_error"])
    if not ss["areas"]:
        st.markdown('<p class="lead">Nothing saved yet. Your project saves automatically as soon as you add '
                    'a lawn photo in the Design studio, and you get a private link to come back to it.</p>',
                    unsafe_allow_html=True)
        st.button("Start designing  →", type="primary", on_click=state.go, args=("studio",))
    else:
        ptype, city = state.settings()
        st.markdown(f'<p class="lead">Everything here saves automatically. Bookmark your private link to come back '
                    f'later or open it on another device. Anyone with the link can view it, so share it only with '
                    f'people you choose (family, your HOA board, a landscaper).</p>', unsafe_allow_html=True)
        st.code(_project_link(ss["pid"]), language=None)
        st.caption(f"{ptype} · {city} · {len(ss['areas'])} lawn area{'s' if len(ss['areas']) != 1 else ''}")
        cap = C.PROPERTY_TYPES[ptype]["cap"]
        cols = st.columns(3, gap="large")
        for i, ar in enumerate(ss["areas"]):
            with cols[i % 3]:
                res = ar.get("result")
                st.image(res["after"] if res else ar["photo"], use_container_width=True)
                if res:
                    e = evaluate_design(res["design"], ss["palette"], ar["sqft"], city, cap)
                    st.markdown(f"**{ar['name']}** · {ar['sqft']:,} sq ft<br>"
                                f"<span class='muted'>{res['design'].get('chosen_style') or res['design']['concept']}<br>"
                                f"\\${e['rebate_usd']:,.0f} est. rebate · {e['gallons_saved']:,.0f} gal/yr saved</span>",
                                unsafe_allow_html=True)
                else:
                    st.markdown(f"**{ar['name']}** · {ar['sqft']:,} sq ft<br><span class='muted'>Not designed yet</span>",
                                unsafe_allow_html=True)
                st.button("Open in studio", key=f"open{ar['id']}", on_click=_open_area, args=(ar["id"],),
                          use_container_width=True)
    st.write("")
    with st.expander("Open a different project, or start over"):
        code = st.text_input("Paste a project link or code", placeholder="https://…?p=abc123  or  abc123")
        c1, c2, c3 = st.columns(3)
        if c1.button("Open", use_container_width=True, disabled=not code.strip()):
            pid = code.strip().split("p=")[-1].split("&")[0].strip("/ ")
            if state.open_project(pid):
                st.rerun()
            else:
                st.error(ss.get("store_error", "Not found."))
        if c2.button("Start a new project", use_container_width=True, disabled=not ss["areas"]):
            state.new_project(); st.rerun()
        if ss["pid"] and c3.button("Delete this project", use_container_width=True):
            ss["confirm_delete"] = True
        if ss.get("confirm_delete"):
            st.warning("This permanently deletes every photo and design in this project.")
            d1, d2, _ = st.columns([1, 1, 2])
            if d1.button("Yes, delete it", type="primary"):
                state.delete_project(); ss.pop("confirm_delete", None); st.rerun()
            if d2.button("Cancel"):
                ss.pop("confirm_delete", None); st.rerun()
    theme.footer()


def privacy():
    import os
    contact = os.getenv("APP_CONTACT", "").strip()
    st.markdown('<h1 style="margin-top:0">Privacy</h1>', unsafe_allow_html=True)
    st.markdown("""
verdanti.ai has no accounts and never asks for your name, email or address. This page explains what the app
does with what you give it.

**What you give the app**
- The photos you upload, the lawn area you outline, and the details you type (area name, size, sun, goals).
- Your residence type and city, used to look up rebates.
- If you upload one, your HOA's plant list.

**Where it is saved**
- Your project saves automatically to a private link (shown on *My designs*) so you can come back to it.
- Anyone who has that link can open the project, so share it only with people you choose.
- Projects are stored on the app's server or its database host. Delete a project anytime on *My designs*:
  that permanently removes its photos and designs.

**AI processing**
- To create a design, your photo and details are sent to OpenAI's API.
- OpenAI does not use API data to train its models. It keeps API data for up to 30 days to monitor for
  abuse, then deletes it, unless the law requires keeping it longer.

**What the app does not do**
- No selling or sharing of your information, and no ads.
- No analytics or tracking added by this app. The hosting service may keep standard server logs
  (such as IP addresses), like any website.

**Tips**
- Use photos of the yard itself. Avoid people, license plates and house numbers where you can.
""")
    if contact:
        st.markdown(f"**Questions?** Contact {contact}.")
    st.caption("Last updated October 24, 2026.")
    theme.footer()


def about():
    st.markdown('<h1 style="margin-top:0">AI that designs, code that checks</h1>'
                '<p class="lead">AI is good at seeing and designing, and unreliable at rules and arithmetic. '
                'So every number and every rule in this app is enforced by code, the AI never computes '
                'money or water.</p>', unsafe_allow_html=True)
    stages = [("Lawn detection", "Computer vision finds grass by color and texture, refined with GrabCut; an AI outline rescues dry lawns. You can add or erase."),
              ("Site analysis", "A vision model lists what it literally sees before judging sun, trees, soil and constraints, to prevent made-up details."),
              ("Palette-locked design", "The designer can only pick plants from the palette: names are enforced by the response schema, not by asking."),
              ("Rebate check", "Python computes coverage at maturity against Valley Water's 50% rule and adjusts counts or suggests swaps."),
              ("Art direction", "The AI sees your photo with the lawn highlighted and writes placements tied to real landmarks, using real plant descriptions."),
              ("Render + review loop", "The image model repaints only the lawn. Code checks for artifacts and restores every pixel outside the lawn; an AI critic scores it and requests fixes; it retries up to 3 times.")]
    cols = st.columns(3, gap="medium")
    for i, (t, d) in enumerate(stages):
        cols[i % 3].markdown(f'<div class="card" style="margin-bottom:1rem"><div class="step-n">{i + 1:02d}</div>'
                             f'<h4>{t}</h4><p>{d}</p></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Data and formulas</div>', unsafe_allow_html=True)
    st.markdown(f"""
- **Plants:** Valley Water Landscape Rebate qualifying plant list (2,713 plants, mature coverage values); a starter palette of 75 qualifying plants tagged by sun exposure.
- **Water:** California MWELO formula, ETo × plant factor × area × 0.62 ÷ irrigation efficiency (lawn 0.8 on spray vs. low-water plants 0.2 on drip).
- **Rebate:** ${C.REBATE_PER_SQFT:.0f}/sq ft; caps by property type; ≥{C.MIN_PLANT_COVERAGE:.0%} plant coverage at maturity.
- **AB 1572:** deadlines for public agencies (2027), commercial/institutional (2028), HOA common areas (2029).
- **AI models:** OpenAI vision/reasoning model for detection hints, analysis, design, art direction and review; OpenAI image model for the preview.
""")
    theme.footer()
