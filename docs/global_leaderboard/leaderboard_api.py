from flask import Flask, request, jsonify
from flask_cors import CORS
from filelock import FileLock
import csv, os, time

# ---- settings ----
CSV_PATH = os.environ.get("LEADERBOARD_CSV", "delay_dodge_leaderboard.csv")
TOP_N = int(os.environ.get("TOP_N", "100"))
NAME_MAX = 24
SCORE_MAX = 10_000_000

# simple in-memory throttle (per IP)
POST_WINDOW_SEC = 10
LAST_POST = {}

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})  # allow cross-origin fetch from your game

def _ensure_csv():
    if not os.path.exists(CSV_PATH):
        with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["name", "score"])  # header

def _read_all():
    _ensure_csv()
    rows = []
    with open(CSV_PATH, "r", newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            try:
                rows.append((row["name"], int(row["score"])))
            except Exception:
                pass
    # sort desc by score
    rows.sort(key=lambda t: t[1], reverse=True)
    return rows

def _append(name, score):
    _ensure_csv()
    # atomic-ish write
    lock = FileLock(CSV_PATH + ".lock")
    with lock:
        rows = _read_all()
        rows.append((name, score))
        rows.sort(key=lambda t: t[1], reverse=True)
        rows = rows[:TOP_N]
        # rewrite full file to keep it small & sorted
        with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["name", "score"])
            w.writerows(rows)

@app.get("/leaderboard")
def get_leaderboard():
    rows = _read_all()[:TOP_N]
    return jsonify([{"name": n, "score": s} for n, s in rows])

@app.post("/leaderboard")
def post_leaderboard():
    # basic anti-spam
    ip = request.headers.get("CF-Connecting-IP") or request.headers.get("X-Forwarded-For", request.remote_addr)
    now = time.time()
    last = LAST_POST.get(ip, 0)
    if now - last < POST_WINDOW_SEC:
        return jsonify({"ok": False, "error": "slow_down"}), 429
    LAST_POST[ip] = now

    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "Player").strip()
    score = data.get("score")

    # validate
    if not isinstance(score, int):
        try:
            score = int(score)
        except Exception:
            return jsonify({"ok": False, "error": "invalid_score"}), 400
    name = name.replace(",", " ")[:NAME_MAX]
    score = max(0, min(score, SCORE_MAX))

    try:
        _append(name, score)
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": "server_error"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5057, debug=False)
