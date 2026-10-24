# verdanti.ai

*Smarter landscapes. Less water.*

verdanti.ai takes a photo of a lawn, designs a replacement garden using only plants that qualify for
Valley Water's lawn rebate, calculates the rebate and the water saved, and shows an image of the garden
in that same yard.

It is built for homeowners and HOA boards in Santa Clara County. California's AB 1572 bans watering
nonfunctional turf in HOA common areas with drinking water from January 1, 2029. Valley Water pays at
least $2 per square foot to replace lawn, but only if qualifying plants cover at least 50% of the area
when grown, and only if the rebate is approved before any grass is removed.

> **Judges:** the live app is at **[APP LINK]**. Running an AI design needs the passcode in the submission
> notes. Every other page works without it, and the demo video shows a complete run.

---

## How it works

1. **Set up:** pick homeowner or HOA and a city. HOAs can upload their own approved plant list; it is
   checked against Valley Water's list automatically.
2. **Upload a photo:** JPG, PNG, WebP or iPhone HEIC, from a phone or a laptop.
3. **Outline the lawn:** draw one loop around the grass to replace, then fix edges with Paint and Erase.
4. **Design** (runs in the background, about 1 to 3 minutes, so you can keep using the app):
   - **Site reading** (AI): lists what is visible, then judges sun, trees and root zones, paths and windows.
   - **Designer** (AI): reads the house style, considers three garden styles, picks one, and chooses plants
     by role (groundcover, structure, seasonal color, a feature plant). It can only pick plants from the
     palette; a strict JSON schema makes any other choice impossible.
   - **Rule checks** (code): designs that are more than 40% grasses go back to the designer once; plant
     counts are adjusted until qualifying plants cover at least 50% of the area at mature size.
   - **Art director** (AI): writes a detailed description of the finished garden on this exact photo.
   - **Render** (AI image model): repaints only the outlined lawn. Small lawns are zoomed in first for detail.
     Code puts back every original pixel outside the outline, and pixel checks catch bad renders.
   - **Critic** (AI): scores preservation, realism, scale, artistry and match to the design. If artistry is
     below 7, the art director rewrites the description and it renders once more. The better render is kept.
5. **Results:** before/after slider, plant list with quantities and placement, rebate estimate (with city
   bonuses and caps), gallons saved per year, and what the rebate covers against typical project costs.
6. **Rebate plan:** totals for every area, the rebates and free programs in your city (each checked against
   its official page), and a button to ReScape California's directory of trained landscapers.
7. **My designs:** every project saves automatically to a private link you can bookmark or share.

All money and water numbers come from code, not AI. Water savings use California's MWELO formula with local
reference evapotranspiration. Estimates only; Valley Water's pre-inspection makes the final decision.

## Run it on your computer

```bash
git clone [REPO URL] && cd [repo folder]
python3 -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # then open .env and paste your OpenAI API key and a passcode
streamlit run app.py
```

The app opens in your browser. Without an API key, everything except the AI design step still works.

Developer mode: `FAKE_OPENAI=1 streamlit run app.py` runs the whole app with canned AI responses and no
API cost. Offline tests: `python tests/test_pipeline.py`.

### Settings (`.env` locally, or Secrets when deployed)

| Setting | What it does |
|---|---|
| `OPENAI_API_KEY` | Your OpenAI key. Required for AI designs. |
| `APP_PASSCODE` | Passcode people must enter before running AI designs, so strangers can't spend your credits. |
| `SESSION_DESIGN_LIMIT` | Max designs per visitor (default 5). |
| `DAILY_DESIGN_LIMIT` | Max designs per day for the whole site (default 40). |
| `MAX_RENDERS` | Renders per design (default 2: a first try plus one rewrite if the critic isn't satisfied). |
| `OPENAI_TEXT_MODEL` / `OPENAI_IMAGE_MODEL` | Override models (defaults `gpt-4o`, `gpt-image-2`). |
| `OPENAI_IMAGE_QUALITY` / `OPENAI_FINAL_QUALITY` | Render quality (default `medium`) and an optional high-quality pass on the winner (default `off`; `high` costs about 4x per image). |
| `APP_CONTACT` | Optional. Contact shown on the Privacy page. |
| `SUPABASE_URL` / `SUPABASE_KEY` | Optional. Store saved projects in Supabase (see below). Otherwise they save to `storage/`. |

## Put it online (free, about 10 minutes)

1. Push this folder to a **public GitHub repo**. `.env` and `storage/` are git-ignored, so your key and
   saved photos stay private.
2. Go to **share.streamlit.io**, sign in with GitHub, click **Create app**, pick the repo, and set the main
   file to `app.py`.
3. Under **Advanced settings → Secrets**, paste:
   ```toml
   OPENAI_API_KEY = "sk-..."
   APP_PASSCODE = "choose-a-code"
   ```
4. Click **Deploy**. Share the link, and give the passcode only to people who should run designs.

### Protect your API budget
- In **platform.openai.com → Settings → Limits**, set a monthly **budget limit** (for example $25).
  Once it's reached, AI calls stop instead of charging more.
- One design costs roughly **$0.15 to $0.25**: a few vision calls plus one or two image renders.
- The passcode and the per-visitor and daily limits add a second layer of protection.

### Saved projects (backend)
Every project saves automatically under a private link (`...?p=abc123`), shown on **My designs**. Opening
the link restores every photo, outline and design, even after a refresh or on another device.

- **On your computer**, projects are stored in `storage/` (SQLite plus image files). Nothing to set up.
- **Online**, Streamlit Cloud wipes local files when the app restarts, so use **Supabase** (free):
  1. Create a project at **supabase.com**.
  2. **SQL Editor** → run:
     ```sql
     create table projects (id text primary key, title text, data jsonb, updated timestamptz default now());
     alter table projects enable row level security;
     ```
  3. **Storage** → **New bucket** named `designs` (leave it private).
  4. **Project Settings → API**: copy the Project URL and the `service_role` key into your Secrets:
     ```toml
     SUPABASE_URL = "https://xxxx.supabase.co"
     SUPABASE_KEY = "your-service-role-key"
     ```
  The `service_role` key stays on the server, and row level security blocks direct public access to the
  table. Projects are reachable only through the app with their unguessable link.

## Privacy
No accounts, and no names, emails or addresses are collected. Photos and designs are stored under the
project's private link and can be deleted anytime on My designs. Photos are sent to OpenAI's API to create
designs; OpenAI does not train on API data and keeps it up to 30 days for abuse monitoring. Streamlit usage
analytics are turned off. The full statement is on the app's Privacy page.

## Images you can swap
- `data/logo.png` (nav logo) and `data/icon.png` (browser-tab icon). Originals are in `data/brand/`.
- `data/hero.jpg`: the home page hero photo.
- `data/gallery/`: optional before/after pairs (`name_before.jpg` + `name_after.png`) shown on the home page.
- `data/samples/`: optional lawn photos visitors can try without uploading their own.
- `data/logos/`: logos for the rebate program tiles.

## Project structure

| Path | Purpose |
|---|---|
| `app.py` | Entry point: settings, navigation, page routing, autosave |
| `ui/home.py` | Home page: hero, homeowner and HOA sections, AB 1572 countdown, FAQs |
| `ui/studio.py` | Design studio: setup, upload, outline, background design, results |
| `ui/pages_misc.py` | Rebate plan, plant library, My designs, privacy |
| `ui/state.py` | Session state, project links and autosave, passcode, spending limits |
| `ui/theme.py` | Design system: colors, fonts, layout (desktop and phone), before/after slider |
| `ui/brush.py`, `ui/components/lawn_brush/` | Outline, paint and erase tool (custom JavaScript component) |
| `ui/components/before_after/` | Before/after slider that fits any screen (custom JavaScript component) |
| `engine/ai.py` | Site reading and palette-locked design (strict JSON outputs), grass limit |
| `engine/render.py` | Render engine: auto-zoom, canvas fitting, art director, masked edit, pixel checks, critic, rewrites |
| `engine/impact.py` | Rebate rule, coverage auto-fix, water math (MWELO), cost ranges, AB 1572 |
| `engine/plants.py` | Palettes and cross-checking against the Valley Water list |
| `engine/programs.py` | Rebates and free programs by city, each with its official source |
| `engine/store.py` | Backend: saves projects to Supabase or local SQLite plus image files |
| `engine/jobs.py` | Runs each design in the background so switching pages doesn't stop it |
| `engine/lawn.py` | Earlier automatic lawn detection (color, texture, GrabCut), kept for reference |
| `engine/config.py` | Every constant, with its source |
| `data/` | Valley Water plant list (2,713 plants), starter palette (75), plant visual descriptions |
| `scripts/` | Rebuild the data files; `smoke_test.py` runs one real end-to-end design from the terminal |
| `tests/` | Offline tests with the AI mocked |

## Data sources
- Santa Clara Valley Water District: Landscape Rebate Program and Qualifying Plant List
- City and nonprofit program pages (Palo Alto, Mountain View, Santa Clara, Milpitas, Our City Forest,
  Canopy, Cal Water), linked from each program in the app
- California Model Water Efficient Landscape Ordinance (MWELO) water-use formula; CIMIS reference ETo
- AB 1572 compliance deadlines
- ReScape California Qualified Professionals Directory
- Typical project cost ranges: LawnStarter xeriscaping cost guide (Dec 2025) and Ridgeline Outdoor Living
  California cost guide (2026)

## Tools and AI disclosure
- **Languages and libraries:** Python, JavaScript, HTML/CSS; Streamlit, OpenAI Python SDK, Pillow,
  OpenCV, NumPy, pandas, pillow-heif.
- **AI inside the app:** OpenAI `gpt-4o` (site reading, design, art direction, render review) and
  `gpt-image-2` (masked photo edit).
- **AI used to build the app:** Claude (Anthropic) wrote most of the code with me, based on my design
  process, testing and direction. [Logo tool] was used for the logo. See the application's AI answer for
  what I did myself.

## Author
[Your name] · [School] · California's 16th Congressional District

Built as part of a Girl Scout Gold Award project: *AI-Powered Sustainable Landscaping*.
