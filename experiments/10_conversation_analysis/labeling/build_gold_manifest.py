# /// script
# requires-python = ">=3.10"
# dependencies = ["soundfile", "numpy", "scipy"]
# ///
"""Gom gold đã chốt -> (1) manifest NeMo đo WER số trên FPT thật, (2) CSV nhãn barge-in.

Chạy:
  uv run --script build_gold_manifest.py

Đầu ra:
  gold_manifest.jsonl   : {audio_filepath, text, duration} — chỉ turn done + text, cắt kênh người nói, 16k
  gold_bargein.csv      : call_id, key, t0, t1, is_bargein, group  — cho bài turn-detection
  wav/<cid>_<key>.wav   : clip 16k mỗi turn
"""
from __future__ import annotations
import argparse
import csv
import glob
import json
import os

import numpy as np
import soundfile as sf
from scipy.signal import resample_poly

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
AUDIO_DIR = os.path.join(ROOT, "data", "audio_interrupt")
OUT_DIR = os.path.join(ROOT, "out")
GOLD_DIR = os.path.join(HERE, "gold")
WAV_DIR = os.path.join(HERE, "wav")
DEFAULT_MODEL = "parakeet"


BACKCHANNEL = set("dạ vâng ừ ừm à ạ ờ ừa alo lô ok okê okey đúng hử ừhử vầng".split())


def has_digit(text, k=2):
    D = set("khong mot mot hai ba bon tu nam lam sau bay tam chin".split())
    ws = text.lower().split(); run = best = 0
    for w in ws:
        run = run + 1 if w in D else 0
        best = max(best, run)
    return best >= k


def suggest_kind(text, dur, digit):
    if digit:
        return "content"
    t = text.strip().lower(); ws = t.split()
    if not ws or t in (".", "—", ""):
        return "skip"
    if len(ws) <= 2 and (dur < 0.9 or all(w in BACKCHANNEL for w in ws)):
        return "backchannel"
    return "content"


def call_meta(cid):
    """turns {key:(spk,t0,t1,text)} + bot_ch từ JSON model default (cùng VAD với lúc label)."""
    j = json.load(open(os.path.join(OUT_DIR, DEFAULT_MODEL, cid + ".json"), encoding="utf-8"))
    turns = {f"{t['spk']}@{t['t0']:.2f}": (t["spk"], t["t0"], t.get("t1", t["t0"]), t.get("text", ""))
             for t in j["turns"]}
    return turns, j.get("bot_ch", 0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only-done", action="store_true",
                    help="chỉ lấy turn đã tick chốt; mặc định lấy MỌI turn có text")
    args = ap.parse_args()
    os.makedirs(WAV_DIR, exist_ok=True)
    man, brows, krows = [], [], []
    cov = {"content_total": 0, "content_labeled": 0, "backchannel": 0, "skip": 0}
    for gp in sorted(glob.glob(os.path.join(GOLD_DIR, "*.json"))):
        cid = os.path.basename(gp)[:-5]
        gold = json.load(open(gp, encoding="utf-8"))
        if not gold:
            continue
        turns, bot_ch = call_meta(cid)
        # coverage: đếm content-total trên TOÀN turn của cuộc (kind người gắn > gợi ý)
        for key, (spk, t0, t1, ptext) in turns.items():
            k = gold.get(key, {}).get("kind") or suggest_kind(ptext, t1 - t0, has_digit(ptext))
            if k == "content":
                cov["content_total"] += 1
        wav, sr = sf.read(os.path.join(AUDIO_DIR, cid + ".wav"), dtype="float32", always_2d=True)
        for key, rec in gold.items():
            if key not in turns:
                continue
            spk, t0, t1, ptext = turns[key]
            # nhãn barge-in cho MỌI turn có gắn
            if rec.get("is_bargein") is not None or rec.get("group"):
                brows.append([cid, key, f"{t0:.2f}", f"{t1:.2f}",
                              int(bool(rec.get("is_bargein"))), rec.get("group", "")])
            kind = rec.get("kind") or suggest_kind(ptext, t1 - t0, has_digit(ptext))
            # taxonomy phân loại turn (cần-gõ/dạ-vâng/bỏ) — nhãn dùng lại cho VAD/turn-detection
            krows.append([cid, key, spk, f"{t0:.2f}", f"{t1:.2f}", kind, rec.get("text", "").strip()])
            if kind == "backchannel":
                cov["backchannel"] += 1
            elif kind == "skip":
                cov["skip"] += 1
            # manifest WER: CHỈ turn nội dung + có text (backchannel/bỏ loại khỏi thước)
            if kind != "content" or not rec.get("text", "").strip():
                continue
            if args.only_done and not rec.get("done"):
                continue
            cov["content_labeled"] += 1
            ch = bot_ch if spk == "bot" else (1 - bot_ch)
            ch = min(ch, wav.shape[1] - 1)
            seg = wav[int(t0 * sr):int(t1 * sr), ch]
            if len(seg) < sr * 0.1:
                continue
            seg16 = resample_poly(seg, 16000, sr).astype(np.float32) if sr != 16000 else seg
            outp = os.path.join(WAV_DIR, f"{cid[:8]}_{key.replace('@','_')}.wav")
            sf.write(outp, seg16, 16000)
            man.append({"audio_filepath": outp, "text": rec["text"].strip(),
                        "duration": round(len(seg16) / 16000.0, 3)})

    mp = os.path.join(HERE, "gold_manifest.jsonl")
    open(mp, "w", encoding="utf-8").write("\n".join(json.dumps(r, ensure_ascii=False) for r in man) + "\n")
    cp = os.path.join(HERE, "gold_bargein.csv")
    with open(cp, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f); w.writerow(["call_id", "key", "t0", "t1", "is_bargein", "group"]); w.writerows(brows)
    kp = os.path.join(HERE, "gold_kinds.csv")
    with open(kp, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f); w.writerow(["call_id", "key", "spk", "t0", "t1", "kind", "text"]); w.writerows(krows)
    print(f"[gold] manifest={len(man)} turn nội dung -> {mp}", flush=True)
    print(f"[gold] bargein={len(brows)} nhãn -> {cp}", flush=True)
    print(f"[gold] kinds={len(krows)} nhãn phân loại turn (cần-gõ/dạ-vâng/bỏ) -> {kp}", flush=True)
    print(f"[coverage] nội dung đã gõ {cov['content_labeled']}/{cov['content_total']} "
          f"| đế {cov['backchannel']} | bỏ {cov['skip']}  "
          f"(WER chỉ tính trên turn nội dung, không tính đế/bỏ)", flush=True)


if __name__ == "__main__":
    main()
