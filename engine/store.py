"""Backend storage for projects (a homeowner's or HOA's set of lawn areas and designs).

Two interchangeable backends, picked automatically:
  • Supabase (Postgres + Storage) when SUPABASE_URL and SUPABASE_KEY are set, persistent, use this
    for the deployed app. Setup steps are in the README.
  • Local SQLite + image files otherwise (folder: STORE_DIR, default ./storage), great on a laptop.
    On Streamlit Community Cloud the local disk is wiped when the app restarts.

A project is identified by a random, unguessable ID that lives in the page URL (?p=...).
Anyone with the link can open the project, like a "share with link" document.

Saved per project:
  project.json, settings + every area's text data (design, analysis, review scores, brief...)
  images      , photo, lawn mask, final render, close-up pair, each render attempt
"""
import io, json, os, secrets, sqlite3, time
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent


def new_id() -> str:
    return secrets.token_urlsafe(9).replace("-", "a").replace("_", "b")   # 12 chars, URL-safe


def _valid(pid: str) -> bool:
    return bool(pid) and len(pid) <= 32 and pid.isalnum()


def _img_bytes(img: Image.Image, name: str) -> tuple[bytes, str]:
    b = io.BytesIO()
    if name.endswith(".png"):
        img.save(b, "PNG", optimize=True); return b.getvalue(), "image/png"
    img.convert("RGB").save(b, "JPEG", quality=88); return b.getvalue(), "image/jpeg"


# ───────────────────────────── local backend ─────────────────────────────────
class LocalStore:
    kind = "local"

    def __init__(self, folder=None):
        self.dir = Path(folder or os.getenv("STORE_DIR") or ROOT / "storage")
        self.dir.mkdir(parents=True, exist_ok=True)
        self.db = self.dir / "projects.db"
        with sqlite3.connect(self.db) as c:
            c.execute("CREATE TABLE IF NOT EXISTS projects (id TEXT PRIMARY KEY, title TEXT, "
                      "data TEXT, created REAL, updated REAL)")

    def save_doc(self, pid, title, doc):
        now = time.time()
        with sqlite3.connect(self.db) as c:
            c.execute("INSERT INTO projects VALUES (?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET "
                      "title=excluded.title, data=excluded.data, updated=excluded.updated",
                      (pid, title, json.dumps(doc), now, now))

    def load_doc(self, pid):
        with sqlite3.connect(self.db) as c:
            row = c.execute("SELECT data FROM projects WHERE id=?", (pid,)).fetchone()
        return json.loads(row[0]) if row else None

    def put_image(self, pid, name, img):
        p = self.dir / "images" / pid / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(_img_bytes(img, name)[0])

    def get_image(self, pid, name):
        p = self.dir / "images" / pid / name
        return Image.open(p).copy() if p.exists() else None

    def delete(self, pid):
        with sqlite3.connect(self.db) as c:
            c.execute("DELETE FROM projects WHERE id=?", (pid,))
        folder = self.dir / "images" / pid
        if folder.exists():
            for f in folder.iterdir():
                f.unlink()
            folder.rmdir()

    def count(self):
        with sqlite3.connect(self.db) as c:
            return c.execute("SELECT COUNT(*) FROM projects").fetchone()[0]


# ───────────────────────────── Supabase backend ──────────────────────────────
class SupabaseStore:
    """Talks to Supabase's REST APIs directly (no extra package needed)."""
    kind = "supabase"
    BUCKET = "designs"

    def __init__(self, url, key):
        import httpx                        # installed with the openai package
        self.url = url.rstrip("/")
        self.h = {"apikey": key, "Authorization": f"Bearer {key}"}
        self.http = httpx.Client(timeout=30)

    def _ok(self, r):
        if r.status_code >= 300:
            raise RuntimeError(f"Supabase error {r.status_code}: {r.text[:200]}")
        return r

    def save_doc(self, pid, title, doc):
        self._ok(self.http.post(f"{self.url}/rest/v1/projects",
                                headers=self.h | {"Prefer": "resolution=merge-duplicates"},
                                json={"id": pid, "title": title, "data": doc,
                                      "updated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}))

    def load_doc(self, pid):
        r = self._ok(self.http.get(f"{self.url}/rest/v1/projects", headers=self.h,
                                   params={"id": f"eq.{pid}", "select": "data"}))
        rows = r.json()
        return rows[0]["data"] if rows else None

    def put_image(self, pid, name, img):
        data, ctype = _img_bytes(img, name)
        self._ok(self.http.post(f"{self.url}/storage/v1/object/{self.BUCKET}/{pid}/{name}",
                                headers=self.h | {"Content-Type": ctype, "x-upsert": "true"}, content=data))

    def get_image(self, pid, name):
        r = self.http.get(f"{self.url}/storage/v1/object/{self.BUCKET}/{pid}/{name}", headers=self.h)
        return Image.open(io.BytesIO(r.content)).copy() if r.status_code == 200 else None

    def delete(self, pid):
        r = self.http.post(f"{self.url}/storage/v1/object/list/{self.BUCKET}", headers=self.h,
                           json={"prefix": f"{pid}/", "limit": 1000})
        names = [f"{pid}/{o['name']}" for o in (r.json() if r.status_code == 200 else [])]
        if names:
            self.http.request("DELETE", f"{self.url}/storage/v1/object/{self.BUCKET}", headers=self.h,
                              json={"prefixes": names})
        self._ok(self.http.delete(f"{self.url}/rest/v1/projects", headers=self.h, params={"id": f"eq.{pid}"}))


_store = None


def get_store():
    global _store
    if _store is None:
        url, key = os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY")
        _store = SupabaseStore(url, key) if url and key else LocalStore()
    return _store


# ───────────────────────────── project <-> storage ───────────────────────────
# Image fields saved for each area. Values are PIL images in the session.
def _area_images(ar):
    out = {"photo.jpg": ar.get("photo"), "lawn.png": ar.get("lawn")}
    res = ar.get("result")
    if res:
        out["after.jpg"] = res.get("after")
        z = res["render"].get("zoom")
        if z:
            out["zoom_before.jpg"], out["zoom_after.jpg"] = z
        for i, at in enumerate(res["render"]["attempts"]):
            out[f"attempt{i}.jpg"] = at.get("image")
    return {k: v for k, v in out.items() if v is not None}


def _strip(obj):
    """JSON-safe copy without images."""
    if isinstance(obj, Image.Image):
        return None
    if isinstance(obj, dict):
        return {k: _strip(v) for k, v in obj.items() if not isinstance(v, Image.Image)}
    if isinstance(obj, (list, tuple)):
        return [_strip(v) for v in obj if not isinstance(v, Image.Image)]
    return obj


def _fp(img) -> str:
    """Content fingerprint, cached on the image object (images are never edited in place)."""
    fp = getattr(img, "_l2g_fp", None)
    if fp is None:
        import hashlib
        fp = hashlib.md5(img.tobytes()).hexdigest() + f"{img.size}{img.mode}"
        img._l2g_fp = fp
    return fp


def save_project(pid, settings, areas, saved_ids: dict):
    """Write the project. saved_ids maps image path -> fingerprint of what was last saved,
    so unchanged images are not uploaded again. Returns the updated map."""
    st_ = get_store()
    doc_areas = []
    for ar in areas:
        for name, img in _area_images(ar).items():
            path = f"{ar['id']}/{name}"
            if saved_ids.get(path) != _fp(img):
                st_.put_image(pid, path.replace("/", "_"), img)
                saved_ids[path] = _fp(img)
        a = {k: v for k, v in ar.items() if k not in ("photo", "lawn", "last_stroke", "job_id", "design_error")}
        if a.get("result"):
            r = dict(a["result"]); r.pop("after", None)
            rr = dict(r["render"]); rr["zoom"] = bool(rr.get("zoom"))
            rr.pop("after", None)
            rr["attempts"] = [{k: v for k, v in at.items() if k != "image"} for at in rr["attempts"]]
            r["render"] = rr
            a["result"] = r
        doc_areas.append(_strip(a))
    title = ", ".join(a["name"] for a in areas)[:120] or "Untitled project"
    body = {"version": 1, "settings": settings, "areas": doc_areas}
    sig = json.dumps(body, sort_keys=True, default=str)
    if saved_ids.get("__doc__") != sig:                 # skip the write when nothing changed
        st_.save_doc(pid, title, body | {"saved_at": time.time()})
        saved_ids["__doc__"] = sig
    return saved_ids


def load_project(pid):
    """Returns (settings, areas, saved_ids) or None if the project doesn't exist."""
    if not _valid(pid):
        return None
    st_ = get_store()
    doc = st_.load_doc(pid)
    if not doc:
        return None
    areas, saved = [], {}

    def img(ar_id, name):
        im = st_.get_image(pid, f"{ar_id}_{name}")
        if im is not None:
            im = im.convert("L") if name.endswith(".png") else im.convert("RGB")
            saved[f"{ar_id}/{name}"] = _fp(im)
        return im

    for a in doc["areas"]:
        ar = dict(a)
        ar["photo"], ar["lawn"] = img(a["id"], "photo.jpg"), img(a["id"], "lawn.png")
        if ar["photo"] is None:
            continue
        if ar["lawn"] is None:
            ar["lawn"] = Image.new("L", ar["photo"].size, 0)
        res = ar.get("result")
        if res:
            res["after"] = img(a["id"], "after.jpg")
            rr = res["render"]
            rr["zoom"] = (img(a["id"], "zoom_before.jpg"), img(a["id"], "zoom_after.jpg")) if rr.get("zoom") else None
            if rr["zoom"] and None in rr["zoom"]:
                rr["zoom"] = None
            for i, at in enumerate(rr["attempts"]):
                at["image"] = img(a["id"], f"attempt{i}.jpg")
            if res["after"] is None:
                ar["result"] = None
        ar["mask_ver"] = ar.get("mask_ver", 0) + 1          # make the brush reload the saved mask
        areas.append(ar)
    return doc.get("settings", {}), areas, saved


def delete_project(pid):
    if _valid(pid):
        get_store().delete(pid)
