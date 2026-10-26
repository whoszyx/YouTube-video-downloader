import os
import re
import shutil
import tempfile
import threading
import time
import uuid
from urllib.parse import parse_qs, urlparse, unquote

import yt_dlp
from flask import Flask, jsonify, render_template, request, send_file

app = Flask(__name__)

jobs = {}

COOKIEFILE = "cookies.txt"

HTTP_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

CLIENT_COMBOS = [
    ["android_vr"],
    ["mweb"],
    ["ios"],
    ["android"],
    ["web"],
    ["tv_embedded"],
]

YT_ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")


def _normalize_url(url):
    if not url:
        return url

    for _ in range(3):
        parsed = urlparse(url)
        qs = parse_qs(parsed.query)
        wrapped = None
        for key in ("q", "u", "url", "target"):
            if key in qs and qs[key]:
                candidate = unquote(qs[key][0])
                if "youtube.com" in candidate or "youtu.be" in candidate:
                    wrapped = candidate
                    break
        if not wrapped:
            break
        url = wrapped

    parsed = urlparse(url)
    host = (parsed.netloc or "").lower()
    path = parsed.path or ""
    qs = parse_qs(parsed.query)

    if host.endswith("youtu.be"):
        vid = path.lstrip("/").split("/")[0]
        if YT_ID_RE.match(vid):
            return f"https://www.youtube.com/watch?v={vid}"

    if "v" in qs and qs["v"]:
        vid = qs["v"][0]
        if YT_ID_RE.match(vid):
            return f"https://www.youtube.com/watch?v={vid}"

    if host.endswith("youtube.com") or host.endswith("youtube-nocookie.com"):
        segments = [s for s in path.split("/") if s]
        if len(segments) >= 2 and segments[0] in ("shorts", "embed", "live", "v", "e"):
            vid = segments[1]
            if YT_ID_RE.match(vid):
                return f"https://www.youtube.com/watch?v={vid}"

    return url


def _base_opts(clients=None):
    opts = {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "retries": 10,
        "fragment_retries": 10,
        "skip_unavailable_fragments": True,
        "socket_timeout": 30,
        "http_headers": HTTP_HEADERS,
    }
    if clients is not None:
        opts["extractor_args"] = {"youtube": {"player_client": clients}}
    if os.path.exists(COOKIEFILE):
        opts["cookiefile"] = COOKIEFILE
    return opts


def _probe_info(url):
    """Walk client combos until one returns metadata. Formats are not required —
    the download step will try combos again and pick its own stream.
    """
    last_err = None
    for clients in CLIENT_COMBOS:
        opts = _base_opts(clients)
        opts["skip_download"] = True
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=False)
        except Exception as e:  # noqa: BLE001
            last_err = e
            continue

        if info.get("_type") == "playlist":
            entries = info.get("entries") or []
            if not entries:
                last_err = RuntimeError("Playlist is empty.")
                continue
            info = entries[0]

        return info, clients

    if last_err is not None:
        raise last_err
    raise RuntimeError("All client combos failed.")


def _clean_err(e):
    msg = str(e)
    msg = re.sub(r"\x1b\[[0-9;]*m", "", msg)
    msg = msg.replace("ERROR: ", "").strip()
    return msg[:800]


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/info", methods=["POST"])
def api_info():
    data = request.get_json(silent=True) or {}
    raw = (data.get("url") or "").strip()
    if not raw:
        return jsonify({"error": "No URL provided."}), 400

    url = _normalize_url(raw)

    try:
        info, _ = _probe_info(url)
    except Exception as e:  # noqa: BLE001
        return jsonify({"error": _clean_err(e)}), 502

    return jsonify({
        "title": info.get("title"),
        "thumbnail": info.get("thumbnail"),
        "duration": info.get("duration"),
        "uploader": info.get("uploader") or info.get("channel"),
    })


@app.route("/api/download", methods=["POST"])
def api_download():
    data = request.get_json(silent=True) or {}
    raw = (data.get("url") or "").strip()
    if not raw:
        return jsonify({"error": "No URL provided."}), 400

    url = _normalize_url(raw)

    job_id = uuid.uuid4().hex
    tmpdir = tempfile.mkdtemp(prefix=f"rex_{job_id}_")
    jobs[job_id] = {
        "status": "starting",
        "progress": 0.0,
        "error": None,
        "tmpdir": tmpdir,
        "download_name": None,
    }

    thread = threading.Thread(
        target=_run_download, args=(job_id, url), daemon=True
    )
    thread.start()

    return jsonify({"job_id": job_id})


def _run_download(job_id, url):
    job = jobs.get(job_id)
    if not job:
        return
    tmpdir = job["tmpdir"]

    outtmpl = os.path.join(tmpdir, "%(title)s.%(ext)s")
    payload = {
        "format": "bestvideo+bestaudio/best",
        "outtmpl": outtmpl,
        "merge_output_format": "mp4",
    }

    def hook(d):
        if job_id not in jobs:
            return
        if d.get("status") == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            downloaded = d.get("downloaded_bytes") or 0
            if total > 0:
                jobs[job_id]["progress"] = min(99.0, downloaded / total * 100.0)
            jobs[job_id]["status"] = "downloading"
        elif d.get("status") == "finished":
            jobs[job_id]["progress"] = 99.0
            jobs[job_id]["status"] = "processing"

    attempts = [(c, payload) for c in CLIENT_COMBOS] + [(None, payload)] * 2
    last_err = None

    for clients, base in attempts:
        opts = _base_opts(clients)
        opts.update(base)
        opts["progress_hooks"] = [hook]
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([url])
            produced = [
                os.path.join(tmpdir, f)
                for f in os.listdir(tmpdir)
                if os.path.isfile(os.path.join(tmpdir, f))
            ]
            if not produced:
                raise RuntimeError("Download produced no file.")
            final_path = max(produced, key=os.path.getsize)
            if job_id not in jobs:
                shutil.rmtree(tmpdir, ignore_errors=True)
                return
            jobs[job_id]["download_name"] = os.path.basename(final_path)
            jobs[job_id]["progress"] = 100.0
            jobs[job_id]["status"] = "ready"
            return
        except Exception as e:  # noqa: BLE001
            last_err = e
            for f in os.listdir(tmpdir):
                p = os.path.join(tmpdir, f)
                try:
                    if os.path.isfile(p):
                        os.remove(p)
                    else:
                        shutil.rmtree(p, ignore_errors=True)
                except OSError:
                    pass
            time.sleep(1.0)

    if job_id in jobs:
        jobs[job_id]["status"] = "error"
        jobs[job_id]["error"] = _clean_err(last_err)
        shutil.rmtree(tmpdir, ignore_errors=True)
        jobs[job_id]["tmpdir"] = None


@app.route("/api/status/<job_id>")
def api_status(job_id):
    job = jobs.get(job_id)
    if not job:
        return jsonify({"status": "error", "error": "Job not found."}), 404
    payload = {
        "status": job["status"],
        "progress": round(job["progress"], 2),
        "error": job.get("error"),
    }
    if job["status"] == "ready":
        payload["download_name"] = job.get("download_name")
    return jsonify(payload)


@app.route("/api/file/<job_id>")
def api_file(job_id):
    job = jobs.get(job_id)
    if not job:
        return jsonify({"error": "Job not found."}), 404
    if job["status"] != "ready":
        return jsonify({"error": "File not ready."}), 409
    tmpdir = job.get("tmpdir")
    name = job.get("download_name")
    if not tmpdir or not name:
        return jsonify({"error": "File missing."}), 410
    path = os.path.join(tmpdir, name)
    if not os.path.exists(path):
        return jsonify({"error": "File missing."}), 410

    def _cleanup():
        try:
            shutil.rmtree(tmpdir, ignore_errors=True)
        finally:
            jobs.pop(job_id, None)

    resp = send_file(path, as_attachment=True, download_name=name, conditional=False)
    resp.call_on_close(_cleanup)
    return resp


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)