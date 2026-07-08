# /// script
# requires-python = ">=3.10"
# dependencies = ["soundfile", "numpy"]
# ///
"""Tool labeling LOCAL cho hội thoại FPT — nghe cả cuộc + từng đoạn, sửa transcript, gắn nhãn barge-in, auto-save.

KHÔNG phải artifact claude.ai — server http local (stdlib), mở trên trình duyệt máy Kỳ.
Chạy 100% ở LOCAL, không cần DGX/GPU — chỉ đọc JSON model + audio đã sync sẵn.

Chạy (uv tự cài dep khai báo ở đầu file, không cần nhớ flag):
  uv run --script label_server.py
  -> mở http://localhost:8010

Dữ liệu:
  audio  : data/audio_interrupt/<cid>.wav        (2 kênh, tất định)
  model  : out/<model>/<cid>.json                (parakeet=default, s5, s6 — cùng VAD)
  gold   : labeling/gold/<cid>.json              (dict key->record, auto-save)
"""
from __future__ import annotations
import io
import json
import os
import re
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

import numpy as np
import soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)                       # experiments/10_conversation_analysis
AUDIO_DIR = os.path.join(ROOT, "data", "audio_interrupt")
OUT_DIR = os.path.join(ROOT, "out")
GOLD_DIR = os.path.join(HERE, "gold")
MODELS = ["parakeet", "s5", "s6"]                  # parakeet = default cho ô gold
DEFAULT_MODEL = "parakeet"
PORT = int(os.environ.get("LABEL_PORT", "8010"))
PAD = 0.15                                         # đệm 2 đầu khi cắt đoạn để nghe trọn

GROUPS = [
    "", "1-ngat-loi-that", "2-backchannel", "3-side-conversation",
    "4-bat-dau-roi-dung", "5-noi-de-toan-bo", "6-tu-khoa-ngat",
]

_AUDIO_CACHE: dict[str, tuple] = {}


# ---------------- data ----------------
def list_calls():
    files = sorted(glob_json(os.path.join(OUT_DIR, DEFAULT_MODEL)))
    rows = []
    for f in files:
        j = json.load(open(f, encoding="utf-8"))
        cid = j["call_id"]
        turns = j.get("turns", [])
        ndig = sum(1 for t in turns if has_digit(t.get("text", "")))
        gold = load_gold(cid)
        ndone = sum(1 for r in gold.values() if r.get("done"))
        rows.append({"call_id": cid, "dur_s": j.get("metrics", {}).get("dur_s"),
                     "n_turn": len(turns), "n_digit": ndig,
                     "n_cand": j.get("metrics", {}).get("n_bargein_cand", 0),
                     "n_done": ndone})
    return rows


def glob_json(d):
    import glob
    return [p for p in glob.glob(os.path.join(d, "*.json")) if not os.path.basename(p).startswith("_")]


def has_digit(text, k=2):
    D = set("khong mot mot hai ba bon tu nam lam sau bay tam chin".split())
    ws = text.lower().split()
    run = best = 0
    for w in ws:
        run = run + 1 if w in D else 0
        best = max(best, run)
    return best >= k


def merged_call(cid):
    per = {}
    for m in MODELS:
        p = os.path.join(OUT_DIR, m, cid + ".json")
        if os.path.isfile(p):
            per[m] = json.load(open(p, encoding="utf-8"))
    base = per.get(DEFAULT_MODEL) or next(iter(per.values()))
    ev_by_onset = {round(e["onset_s"], 2): e for e in base.get("events", [])}
    turns = []
    for r in base["turns"]:
        key = f"{r['spk']}@{r['t0']:.2f}"
        texts = {}
        for m in per:
            match = next((t["text"] for t in per[m]["turns"]
                          if t["spk"] == r["spk"] and round(t["t0"], 2) == round(r["t0"], 2)), None)
            if match is not None:
                texts[m] = match
        ev = None
        if r["spk"] == "cust" and round(r["t0"], 2) in ev_by_onset:
            e = ev_by_onset[round(r["t0"], 2)]
            ev = {"sir": e.get("sir_db"), "dur": e.get("cust_dur_s"),
                  "stop": e.get("bot_stopped"), "lat": e.get("stop_latency_ms")}
        turns.append({"key": key, "spk": r["spk"], "t0": r["t0"], "t1": r.get("t1", r["t0"]),
                      "texts": texts, "ev": ev, "digit": has_digit(texts.get(DEFAULT_MODEL, ""))})
    return {"call_id": cid, "bot_ch": base.get("bot_ch"),
            "dur_s": base.get("metrics", {}).get("dur_s"),
            "models": [m for m in MODELS if m in per],
            "default_model": DEFAULT_MODEL, "turns": turns, "gold": load_gold(cid)}


def load_gold(cid):
    p = os.path.join(GOLD_DIR, cid + ".json")
    return json.load(open(p, encoding="utf-8")) if os.path.isfile(p) else {}


def save_gold_record(cid, key, rec):
    os.makedirs(GOLD_DIR, exist_ok=True)
    g = load_gold(cid)
    g[key] = {**g.get(key, {}), **rec}
    tmp = os.path.join(GOLD_DIR, cid + ".json.tmp")
    json.dump(g, open(tmp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    os.replace(tmp, os.path.join(GOLD_DIR, cid + ".json"))
    return g[key]


def get_audio(cid):
    if cid not in _AUDIO_CACHE:
        wav, sr = sf.read(os.path.join(AUDIO_DIR, cid + ".wav"), dtype="float32", always_2d=True)
        _AUDIO_CACHE[cid] = (wav, sr)
    return _AUDIO_CACHE[cid]


def wav_bytes(data, sr):
    buf = io.BytesIO()
    sf.write(buf, data, sr, format="WAV", subtype="PCM_16")
    return buf.getvalue()


# ---------------- http ----------------
class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, code, body, ctype="application/json", extra=None):
        if isinstance(body, (dict, list)):
            body = json.dumps(body, ensure_ascii=False).encode("utf-8")
        elif isinstance(body, str):
            body = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def _wav(self, data, sr):
        b = wav_bytes(data, sr)
        rng = self.headers.get("Range")
        if rng:  # Range cho <audio> seek được
            mo = re.match(r"bytes=(\d+)-(\d*)", rng)
            a = int(mo.group(1)); z = int(mo.group(2)) if mo.group(2) else len(b) - 1
            z = min(z, len(b) - 1)
            self.send_response(206)
            self.send_header("Content-Type", "audio/wav")
            self.send_header("Accept-Ranges", "bytes")
            self.send_header("Content-Range", f"bytes {a}-{z}/{len(b)}")
            self.send_header("Content-Length", str(z - a + 1))
            self.end_headers()
            self.wfile.write(b[a:z + 1])
        else:
            self.send_response(200)
            self.send_header("Content-Type", "audio/wav")
            self.send_header("Accept-Ranges", "bytes")
            self.send_header("Content-Length", str(len(b)))
            self.end_headers()
            self.wfile.write(b)

    def do_GET(self):
        u = urlparse(self.path)
        p, q = u.path, parse_qs(u.query)
        try:
            if p == "/":
                self._send(200, INDEX_HTML, "text/html; charset=utf-8")
            elif p == "/api/calls":
                self._send(200, list_calls())
            elif p.startswith("/api/call/"):
                self._send(200, merged_call(p.split("/")[-1]))
            elif p.startswith("/audio/"):
                cid = p.split("/")[-1].replace(".wav", "")
                wav, sr = get_audio(cid)
                self._wav(wav, sr)
            elif p.startswith("/seg/"):
                cid = p.split("/")[-1].replace(".wav", "")
                wav, sr = get_audio(cid)
                t0 = max(0.0, float(q["t0"][0]) - PAD); t1 = float(q["t1"][0]) + PAD
                seg = wav[int(t0 * sr):int(t1 * sr)]
                self._wav(seg if len(seg) else np.zeros((sr // 10, wav.shape[1]), "float32"), sr)
            else:
                self._send(404, {"err": "not found"})
        except Exception as e:  # noqa: BLE001
            self._send(500, {"err": f"{type(e).__name__}: {e}"})

    def do_POST(self):
        u = urlparse(self.path)
        n = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(n) or b"{}")
        try:
            if u.path == "/api/save":
                rec = save_gold_record(body["call_id"], body["key"], body["rec"])
                self._send(200, {"ok": True, "rec": rec})
            else:
                self._send(404, {"err": "not found"})
        except Exception as e:  # noqa: BLE001
            self._send(500, {"err": f"{type(e).__name__}: {e}"})


INDEX_HTML = "__INDEX_HTML__"


def main():
    if not os.path.isdir(AUDIO_DIR):
        sys.exit(f"thiếu audio dir {AUDIO_DIR} — sync 36 wav về trước")
    global INDEX_HTML
    with open(os.path.join(HERE, "index.html"), encoding="utf-8") as f:
        INDEX_HTML = f.read().replace("__GROUPS__", json.dumps(GROUPS, ensure_ascii=False))
    srv = ThreadingHTTPServer(("127.0.0.1", PORT), H)
    print(f"[label] http://localhost:{PORT}  (audio={AUDIO_DIR})", flush=True)
    srv.serve_forever()


if __name__ == "__main__":
    main()
