"""T3 — gom moi su kien barge-in ung vien tu cac dossier thanh MOT bang review.

Xuat CSV (mo bang LibreOffice/Excel/loc duoc) + moi dong 1 su kien, day du dac trung,
va cot nhan de TRONG cho human/agent dien sau. Day so trong transcript da an (PII).

Chay:
  python tools/review_queue.py --out out --csv out/review_events.csv
"""
from __future__ import annotations
import argparse, csv, glob, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pipeline.util import mask_digits   # noqa: E402

# Data audio_interrupt la tester tu test, KHONG phai khach that -> mac dinh KHONG mask,
# de transcript ro rang phuc vu doc hieu. Bat --mask chi khi gap data khach that.

# thu tu cot toi uu cho quet mat: dinh danh -> tin hieu quyet dinh -> hanh vi -> text -> nhan
COLS = [
    "call_id", "onset_s",
    # timing
    "cust_dur_s", "overlap_dur_s", "into_bot_s", "gap_before_s",
    # acoustic
    "cust_rms_db", "sir_db", "cust_snr_db", "onset_slope_db", "zcr", "spec_flatness",
    # content (tat dinh)
    "n_words", "has_digit", "has_stopword", "only_backchannel", "is_empty",
    # behavior that cua bot
    "bot_stopped", "stop_latency_ms", "readback_mismatch",
    # text (an so)
    "cust_text", "bot_text",
    # nhan de trong
    "label_is_bargein", "label_group", "label_note",
    # tien nghe: lenh cat clip
    "listen_cmd",
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="out", help="thu muc dossier JSON")
    ap.add_argument("--csv", default="out/review_events.csv")
    ap.add_argument("--mask", action="store_true", help="an day so (chi dung cho data khach that)")
    args = ap.parse_args()
    mask = mask_digits if args.mask else (lambda s: s)

    rows = []
    for jp in sorted(glob.glob(os.path.join(args.out, "*.json"))):
        if os.path.basename(jp).startswith("_"):
            continue
        d = json.load(open(jp, encoding="utf-8"))
        cid = d["call_id"]
        for e in d["events"]:
            r = {k: e.get(k, "") for k in COLS}
            r["call_id"] = cid
            r["cust_text"] = mask(e.get("cust_text", ""))
            r["bot_text"] = mask(e.get("bot_text", ""))
            r["listen_cmd"] = f"python tools/cut_clip.py --call {cid} --t {e['onset_s']}"
            for b in ("has_digit", "has_stopword", "only_backchannel", "is_empty",
                      "bot_stopped", "readback_mismatch"):
                r[b] = 1 if e.get(b) else 0
            rows.append(r)

    with open(args.csv, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLS)
        w.writeheader()
        w.writerows(rows)
    print(f"[review] {len(rows)} su kien -> {args.csv}", file=sys.stderr)


if __name__ == "__main__":
    main()
