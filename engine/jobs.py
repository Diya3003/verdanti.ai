"""Background design jobs.

A design takes 1-3 minutes. If it ran inside the page's script, clicking another page would make
Streamlit stop the script and the design (and the money already spent) would be lost. Instead the
design runs in a background thread on the server; pages just check on it.

The worker never touches Streamlit. When it finishes it writes the result into the lawn area and
saves the project, so the design is kept even if the person changed pages or closed the tab.
"""
import threading
import time
import uuid

JOBS: dict = {}                 # job_id -> {"status", "log", "error", "started"}
SAVE_LOCK = threading.Lock()    # one project save at a time (page autosave vs. finished job)


def start(target, *args) -> str:
    job_id = uuid.uuid4().hex[:10]
    job = {"status": "running", "log": [], "error": None, "started": time.time()}
    JOBS[job_id] = job

    def run():
        try:
            target(job, *args)
            job["status"] = "done"
        except Exception as ex:          # shown to the person on their next page view
            job["status"], job["error"] = "error", str(ex)
    threading.Thread(target=run, daemon=True, name=f"design-{job_id}").start()
    return job_id


def get(job_id):
    return JOBS.get(job_id)


def running(job_id) -> bool:
    j = JOBS.get(job_id)
    return bool(j) and j["status"] == "running"
