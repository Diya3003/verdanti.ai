"""Design studio: property setup → add lawn areas → auto-detect lawn → design → results."""
import io, time, uuid
from pathlib import Path
import pandas as pd
import streamlit as st
from PIL import Image, ImageDraw, ImageOps
from engine import config as C
from engine.plants import default_palette, custom_palette_from_table, SUNS
from engine.impact import evaluate_design, fix_coverage, suggest_swaps, ab1572_status
from engine.lawn import detect_lawn, apply_polygon, to_edit_mask, coverage
from engine.render import overlay
from ui import theme, state

SAMPLES = sorted(p for p in (Path(__file__).resolve().parent.parent / "data" / "samples").glob("*")
                 if p.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp", ".heic"))


def photo_types():
    try:
        import pillow_heif  # noqa: F401
        return ["jpg", "jpeg", "png", "webp", "heic", "heif"]
    except ImportError:
        return ["jpg", "jpeg", "png", "webp"]


# ───────────────────────────── property setup ────────────────────────────────
def property_setup():
    ss = st.session_state
    c1, c2, c3 = st.columns([1, 1, 1.4], gap="medium", vertical_alignment="bottom")
    c1.selectbox("Residence type", list(C.PROPERTY_TYPES), key="property_type",
                 help="HOA common areas must stop watering decorative lawn by Jan 1, 2029 (AB 1572).")
    c2.selectbox("City", [c for c in C.ETO_INCHES if c != "default"], key="city",
                 help="Valley Water service area (Santa Clara County)")
    ptype, _ = state.settings()
    ab = ab1572_status(C.PROPERTY_TYPES[ptype]["ab1572"] or "")
    from engine.programs import rebate_cap, boost
    _, city = state.settings()
    who = "hoa" if ptype == "HOA" else "home"
    cap, b = rebate_cap(city, who), boost(city, who)
    extra = f'{city} pays extra: {b["amount"]}, up to ${cap:,}.' if b else \
        f'Valley Water rebate: ${C.REBATE_PER_SQFT:.0f}+/sq ft, up to ${cap:,}.'
    note = (f'<b>AB 1572:</b> stop watering decorative lawn by <b>{ab["deadline"]:%b %d, %Y}</b> '
            f'({ab["days_left"]:,} days). {extra}' if ab else extra)
    c3.markdown(f'<p class="muted" style="margin-bottom:.6rem">{note}</p>', unsafe_allow_html=True)
    hoa = ptype == "HOA"
    with st.expander(f"**Plant palette:** {ss['palette_name']}" + (" · upload your HOA's approved list here" if hoa else ""),
                     expanded=False):
        c1, c2 = st.columns(2, gap="large")
        with c1:
            st.markdown('<p class="muted">The designer may only use plants from this palette. The starter palette has '
                        '75 plants that qualify for Valley Water rebates, tagged by sun exposure.</p>',
                        unsafe_allow_html=True)
        with c2:
            choice = st.radio("Plant palette (the only plants the designer may use)",
                              ["Valley Water starter palette (75 plants)", "Upload my approved plant list"])
            if choice.startswith("Valley"):
                if ss["palette_name"] != "Valley Water starter palette":
                    ss["palette"], ss["palette_name"] = list(default_palette()), "Valley Water starter palette"
            else:
                tmpl = "Botanical name,Common name,Sun exposure\nSalvia clevelandii,Cleveland sage,Full Sun\nHeuchera maxima,Island alum root,Full Shade\n"
                st.download_button("Download template", tmpl, "palette_template.csv")
                f = st.file_uploader("Plant list (CSV or Excel)", type=["csv", "xlsx"])
                if f:
                    df = pd.read_csv(f) if f.name.endswith(".csv") else pd.read_excel(f)
                    pal, warn = custom_palette_from_table(df)
                    if pal:
                        ss["palette"], ss["palette_name"] = pal, f"Custom list ({f.name})"
                        n = {s: sum(p["rebate_status"] == s for p in pal) for s in ("exact", "genus", "none")}
                        st.success(f"{len(pal)} plants · {n['exact']} rebate-eligible · {n['genus']} verify cultivar · "
                                   f"{n['none']} not on the rebate list")
                        if warn:
                            st.caption(" · ".join(warn[:6]) + (" …" if len(warn) > 6 else ""))
                    else:
                        st.error(warn[0] if warn else "Couldn't read that file.")


# ───────────────────────────── access ────────────────────────────────────────
def access_bar():
    if not state.has_key():
        st.info("AI design isn't configured on this server. You can still explore the plant library and rebate rules.")
    elif state.needs_code() and not st.session_state.get("unlocked"):
        with st.container(border=True):
            a, b = st.columns([3, 1])
            code = a.text_input("Access code", type="password", placeholder="Enter the access code to run AI designs",
                                label_visibility="collapsed")
            if b.button("Unlock", use_container_width=True) or code:
                if state.try_unlock(code):
                    st.rerun()
                elif code:
                    st.error("That code isn't right.")
            st.caption("AI designs use paid API calls, so they're limited to people with the code. "
                       "Lawn detection, rebate math and the plant library work without it.")


# ───────────────────────────── add area ──────────────────────────────────────
def add_area_form():
    with st.form("add_area", clear_on_submit=True):
        st.markdown('<h4 style="margin:0 0 .4rem">Add a lawn area</h4>', unsafe_allow_html=True)
        a, b = st.columns([1, 1], gap="large")
        with a:
            photo = st.file_uploader("Photo of the lawn", type=photo_types(),
                                     help="A phone photo from standing height, showing the whole lawn, works best.")
            sample = None
            if SAMPLES:
                sample = st.selectbox("…or try a sample photo", ["None"] + [p.stem.replace("_", " ") for p in SAMPLES])
        with b:
            name = st.text_input("Name", placeholder="Front yard, parkway strip, courtyard…")
            c1, c2 = st.columns(2)
            sqft = c1.number_input("Lawn size (sq ft)", 20, 50000, 400,
                                   help="Pace it: one step ≈ 2.5 ft. Or measure in Google Maps.")
            sun = c2.selectbox("Sun", ["Detect from photo"] + SUNS)
            goals = st.text_input("Goals (optional)", placeholder="Pollinators, low maintenance, privacy…")
        st.caption("Your project saves automatically to a private link (see My designs). Photos are sent to "
                   "OpenAI to create the design; OpenAI doesn't use them for training. Details on the Privacy page.")
        if st.form_submit_button("Add lawn area", type="primary"):
            src = photo or (next(p for p in SAMPLES if p.stem.replace("_", " ") == sample)
                            if sample and sample != "None" else None)
            if src is None:
                st.error("Add a photo first."); return
            try:
                img = ImageOps.exif_transpose(Image.open(src)).convert("RGB")
            except Exception:
                st.error("Couldn't read that image. Try a JPG or PNG, or a screenshot of the photo."); return
            img.thumbnail((1600, 1600))
            lawn, method = Image.new("L", img.size, 0), "you"
            st.session_state["areas"].append({
                "id": uuid.uuid4().hex[:8], "name": name or f"Lawn area {len(st.session_state['areas']) + 1}",
                "sqft": int(sqft), "sun": sun, "criteria": goals, "photo": img,
                "lawn": lawn, "auto_lawn": lawn.copy(), "method": method,
                "pts": [], "mode": "Add", "result": None})
            st.rerun()


# ───────────────────────────── lawn editor ───────────────────────────────────
def lawn_editor(ar):
    from ui.brush import lawn_brush
    ar.setdefault("mask_ver", 0)
    l, r = st.columns([3, 1.2], gap="large")
    with l:
        new, n = lawn_brush(ar["photo"], ar["lawn"], version=f"{ar['id']}-{ar['mask_ver']}",
                            key=f"brush_{ar['id']}_{ar['mask_ver']}")
        if new is not None and n != ar.get("last_stroke"):
            ar["lawn"], ar["last_stroke"] = new, n
    with r:
        st.markdown(f'<h4 style="margin:0 0 .3rem">Lawn to replace</h4>'
                    f'<p class="muted">Show us which grass to replace. <b>Outline</b> and draw a loop around the lawn, '
                    f'or <b>Paint</b> over it. <b>Erase</b> anything that isn\'t lawn: walls, shrubs, paths, cars.</p>', unsafe_allow_html=True)
        if st.button("Clear all", key=f"cl{ar['id']}", use_container_width=True, help="Start from nothing and paint the lawn yourself"):
            ar["lawn"] = Image.new("L", ar["photo"].size, 0); ar["mask_ver"] += 1; ar.pop("last_stroke", None); st.rerun()
        st.write("")
        left, why = state.usage_left()
        empty = coverage(ar["lawn"]) < 0.01
        go = st.button("Design this area", type="primary", key=f"go{ar['id']}", use_container_width=True,
                       disabled=not state.ai_unlocked() or empty or left == 0)
        if empty:
            st.caption("Paint the lawn first.")
        elif not state.ai_unlocked():
            st.caption("Enter the access code above to run the AI designer.")
        elif why:
            st.caption(why)
        else:
            st.caption("Takes 1–4 minutes. Each preview is reviewed and re-rendered if it isn't good enough.")
    return go


def _design_worker(job, ar, zone, palette, project):
    """Runs in a background thread (engine/jobs.py). No Streamlit calls in here."""
    from engine import ai
    from engine.render import render_design
    say = job["log"].append
    say("Reading the site: sun, shade, trees, paths, windows…")
    analysis = ai.analyze_site(ar["photo"], zone)
    sun = analysis["sun_exposure"]["category"] if ar["sun"].startswith("Detect") else ar["sun"]
    zone["sun"] = sun
    say(f"Sun: {sun}. {analysis['sun_exposure']['evidence']}")
    say("Designing with approved plants only…")
    design = ai.design_zone(analysis, zone, palette, photo=ar["photo"])
    say(f"Style: {design.get('chosen_style', '')}: {design['concept']}")
    design, log = fix_coverage(design, palette, ar["sqft"], sun)
    if log:
        say("Adjusted to meet Valley Water's 50% coverage rule.")
    rr = render_design(ar["photo"], to_edit_mask(ar["lawn"]), analysis, design, zone, log=say)
    from engine import store, jobs
    with jobs.SAVE_LOCK:
        ar["result"] = dict(analysis=analysis, design=design, after=rr["after"], render=rr, log=log, sun_used=sun)
        ar.pop("job_id", None)
        # Save now, so the design is kept even if nobody is looking at the page anymore.
        if project.get("pid"):
            try:
                store.save_project(project["pid"], project["settings"], project["areas"], project["saved_ids"])
            except Exception:
                pass                   # the page's own autosave will retry
    say("Your design is ready.")


def run_design(ar):
    """Start the design in the background and return immediately."""
    from engine import jobs
    ss = st.session_state
    ptype, _ = state.settings()
    zone = {"name": ar["name"], "sqft": ar["sqft"], "sun": ar["sun"], "criteria": ar["criteria"],
            "property_type": ptype}
    state.count_usage()
    state.autosave()                   # make sure the project (and its link) exists first
    project = {"pid": ss["pid"], "settings": state.project_settings(), "areas": ss["areas"],
               "saved_ids": ss["saved_ids"]}
    ar.pop("design_error", None)
    ar["job_id"] = jobs.start(_design_worker, ar, zone, list(ss["palette"]), project)
    st.rerun()


@st.fragment(run_every="3s")
def background_notice():
    """Shown on other pages while a design is being made in the background."""
    from engine import jobs
    areas = st.session_state["areas"]
    busy = [a for a in areas if a.get("job_id") and jobs.running(a["job_id"])]
    done = [a for a in areas if a.get("job_id") and not jobs.running(a["job_id"])]
    if busy:
        st.markdown(f"<div class='note'>Your design for <b>{busy[0]['name']}</b> is still being made. "
                    f"It keeps going while you look around and will be in the Design studio when it's ready.</div>",
                    unsafe_allow_html=True)
    else:
        st.session_state["_bg_ready"] = True
        st.markdown("<div class='note'>Your design is ready. Open the <b>Design studio</b> to see it.</div>",
                    unsafe_allow_html=True)


@st.fragment(run_every="2s")
def design_progress(ar):
    """Live progress while the background job runs; refreshes itself every 2 seconds."""
    from engine import jobs
    job = jobs.get(ar.get("job_id"))
    if job is None or job["status"] != "running":
        if job and job["status"] == "error":
            ar["design_error"] = job["error"]
        ar.pop("job_id", None)
        st.rerun()                     # whole page: show the result
    secs = int(time.time() - job["started"])
    with st.status(f"Designing your garden… {secs // 60}:{secs % 60:02d}", expanded=True):
        for line in job["log"]:
            st.write(line)
    st.caption("You can keep using the app. The design keeps going and will be here when it's done.")


# ───────────────────────────── results ───────────────────────────────────────
def plant_table(rows):
    h = ["<table class='plants'><tr><th>Plant</th><th>Qty</th><th>Where</th><th>Coverage</th><th>Water</th><th>Rebate</th></tr>"]
    for r in rows:
        h.append(f"<tr><td><i>{r['botanical']}</i><br><span class='muted'>{r['common']}"
                 f"{' · CA native' if r['native_ca'] else ''}</span></td><td data-l='Qty'>{r['count']}</td>"
                 f"<td class='muted' data-l='Where'>{r.get('placement', '')}</td><td data-l='Coverage'>{r['coverage_total']:.0f} sq ft</td>"
                 f"<td data-l='Water'>{r['water']}</td><td>{theme.badge(r['rebate_status'])}</td></tr>")
    st.markdown("".join(h) + "</table>", unsafe_allow_html=True)


def results(ar):
    res = ar["result"]
    ptype, city = state.settings()
    zoom = res["render"].get("zoom")
    if zoom and st.toggle("Zoom to garden", value=True, key=f"zoom{ar['id']}",
                          help="Close-up of the redesigned area at full detail. Turn off to see the whole photo."):
        theme.before_after(*zoom)
    else:
        theme.before_after(ar["photo"], res["after"])
    ev = evaluate_design(res["design"], st.session_state["palette"], ar["sqft"], city, C.PROPERTY_TYPES[ptype]["cap"])
    k = st.columns(4)
    theme.kpi(k[0], ev["plant_count"], "plants")
    theme.kpi(k[1], f"{ev['qualifying_coverage_pct']:.0%}", "rebate coverage (≥50%)")
    theme.kpi(k[2], f"${ev['rebate_usd']:,.0f}", "est. rebate")
    theme.kpi(k[3], f"{ev['gallons_saved']:,.0f}", f"gal/yr saved · −{ev['pct_saved']:.0%}")
    from engine.impact import cost_sentence
    with st.container(key=f"costnote_{ar['id']}"):
        st.markdown("**What the rebate means:** " + cost_sentence(ar["sqft"], ev["rebate_usd"]))
    dz = res["design"]
    style = f"<p class='muted' style='margin:0;text-transform:uppercase;letter-spacing:.08em;font-size:.78rem'>{dz['chosen_style']}</p>" if dz.get("chosen_style") else ""
    extra = "".join(f"<p class='muted' style='margin:.2rem 0'><b>{lbl}:</b> {dz[key]}</p>"
                    for lbl, key in (("Big idea", "big_gesture"), ("Focal point", "focal_point"),
                                     ("Ties into your home", "echo_existing")) if dz.get(key))
    st.markdown(f"<div style='margin-top:1.6rem'>{style}<h3 style='margin:.2rem 0 .4rem'>{dz['concept']}</h3>{extra}"
                f"<p class='muted' style='margin:.2rem 0'><b>Color story:</b> {dz['color_story']}</p></div>", unsafe_allow_html=True)
    if not ev["rebate_eligible"]:
        st.warning("This design is below Valley Water's 50% coverage rule.")
        if st.button("Adjust plant counts to qualify", key=f"fix{ar['id']}"):
            _, lg = fix_coverage(res["design"], st.session_state["palette"], ar["sqft"], res["sun_used"])
            res["log"] += lg; st.rerun()
        for sw in suggest_swaps(res["design"], st.session_state["palette"], res["sun_used"]):
            st.caption(f"Swap {sw['common']} for: " + ", ".join(sw["options"]))
    plant_table(ev["rows"])
    if res["design"]["maintenance_notes"]:
        st.markdown("<p class='muted' style='margin-top:1rem'><b>Care:</b> " +
                    " · ".join(res["design"]["maintenance_notes"]) + "</p>", unsafe_allow_html=True)
    rr = res["render"]
    with st.expander(f"Quality review: {len(rr['attempts'])} render(s), best scored "
                     f"{rr['attempts'][rr['best_index']]['review']['overall']}/10"):
        for i, at in enumerate(rr["attempts"]):
            rv = at["review"]
            st.markdown(f"**{'Final detail pass' if at.get('detail_pass') else f'Render {i + 1}'}{' · shown' if i == rr['best_index'] else ''}**: {rv['overall']}/10 "
                        f"(preservation {rv['preservation']}, realism {rv['realism']}, scale {rv['scale']}, "
                        f"artistry {rv.get('artistry', rv.get('composition', '–'))}, design match {rv['design_match']})")
            for p in at["metrics"]["fails"] + rv["problems"]:
                st.caption("• " + p)
            if at.get("image") is not None:
                st.image(at["image"], width=340)
    with st.expander("Site analysis and render brief"):
        if res["design"].get("style_options"):
            st.markdown("**Directions the designer considered**")
            for o in res["design"]["style_options"]:
                st.caption(f"• {o['style']}: {o['big_gesture']}")
            st.caption(f"Chose {res['design'].get('chosen_style', '')}: {res['design'].get('why_chosen', '')}")
        st.json(res["analysis"])
        for j, b in enumerate(rr.get("briefs") or [rr["brief"]]):
            st.caption("Render brief" if j == 0 else f"Rewritten brief #{j} (after the critique)")
            st.json(b)
    d1, d2, d3, _ = st.columns([1, 1, 1, 1])
    buf = io.BytesIO(); res["after"].save(buf, "PNG")
    d1.download_button("Download image", buf.getvalue(), f"{ar['name']}_after.png", key=f"dl{ar['id']}",
                       use_container_width=True)
    if d2.button("Redesign", key=f"re{ar['id']}", use_container_width=True):
        ar["result"] = None; st.rerun()
    return d3


# ───────────────────────────── page ──────────────────────────────────────────
def render():
    st.session_state.pop("_bg_ready", None)
    st.markdown('<h1 style="margin-top:0">Design your garden</h1>'
                '<p class="lead">Add a photo of each lawn area. Shade the grass you want gone, '
                'and the AI designer does the rest.</p>', unsafe_allow_html=True)
    property_setup()
    access_bar()
    add_area_form()
    areas = st.session_state["areas"]
    focus = st.session_state.pop("focus_area", None)
    for idx, ar in enumerate(list(areas)):
        st.markdown(f"<div id='area-{ar['id']}'></div>", unsafe_allow_html=True)
        if focus == ar["id"]:              # opened from My designs: scroll to this area
            import streamlit.components.v1 as components
            components.html(f"<script>setTimeout(()=>parent.document.getElementById('area-{ar['id']}')"
                            f"?.scrollIntoView({{behavior:'smooth'}}),600)</script>", height=0)
        st.markdown(f"<div class='section-title' style='margin-top:2.4rem;font-size:1.7rem'>{ar['name']}"
                    f"<span class='muted' style='font-family:Inter;font-size:.95rem'> &nbsp;·&nbsp; {ar['sqft']} sq ft"
                    f" &nbsp;·&nbsp; {ar['result']['sun_used'] if ar['result'] else ar['sun']}</span></div>",
                    unsafe_allow_html=True)
        if ar.get("job_id"):
            design_progress(ar)
            continue
        if ar.get("design_error"):
            st.error(f"Something went wrong while designing: {ar['design_error']}")
        if ar["result"] is None:
            if lawn_editor(ar):
                run_design(ar)
            if st.button("Remove this area", key=f"rm{ar['id']}"):
                areas.pop(idx); st.rerun()
        else:
            slot = results(ar)
            if slot.button("Remove", key=f"rm2{ar['id']}", use_container_width=True):
                areas.pop(idx); st.rerun()
    if any(a["result"] for a in areas):
        st.write("")
        st.button("See your rebate plan →", type="primary", on_click=state.go, args=("plan",), key="toplan")
    theme.footer()
