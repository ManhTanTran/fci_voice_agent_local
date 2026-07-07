"""T5 — bang tong toan corpus + vai phan bo dac trung, dang markdown.

Chay:
  python tools/summary_md.py --out out --md out/summary.md
"""
from __future__ import annotations
import argparse, glob, json, os, sys
import numpy as np


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="out")
    ap.add_argument("--md", default="out/summary.md")
    args = ap.parse_args()

    dossiers = []
    for jp in sorted(glob.glob(os.path.join(args.out, "*.json"))):
        if os.path.basename(jp).startswith("_"):
            continue
        dossiers.append(json.load(open(jp, encoding="utf-8")))

    all_ev = [e for d in dossiers for e in d["events"]]
    n = len(all_ev)
    def frac(key): return sum(1 for e in all_ev if e.get(key)) / n if n else 0

    L = ["# Tong hop exp10 — boc tach hoi thoai (phan tat dinh)", "",
         f"> {len(dossiers)} cuoc · {n} su kien barge-in ung vien. "
         f"Chua gan nhan barge-in that (de agent/human sau).", "",
         "## 1. Bang moi cuoc", "",
         "| Call | dài(s) | #cand | bot dừng | bot tiếp | lat p50(ms) | rb lệch | có STOP-kw | rỗng |",
         "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for d in sorted(dossiers, key=lambda x: -x["metrics"]["n_bargein_cand"]):
        m = d["metrics"]
        L.append(f"| `{d['call_id'][:8]}` | {m['dur_s']:.0f} | {m['n_bargein_cand']} | "
                 f"{m['n_bot_stopped']} | {m['n_bot_continued']} | "
                 f"{m['stop_latency_p50_ms'] or '—'} | {m['n_readback_mismatch']} | "
                 f"{m['n_has_stopword']} | {m['n_empty_cand']} |")

    tot_cand = sum(d["metrics"]["n_bargein_cand"] for d in dossiers)
    tot_stop = sum(d["metrics"]["n_bot_stopped"] for d in dossiers)
    L += ["", "## 2. Tong va phan bo dac trung", "",
          f"- Tong ung vien barge-in: **{tot_cand}**; bot da dung: **{tot_stop}** "
          f"({tot_stop/tot_cand*100:.0f}%).",
          f"- Ty le co it nhat 1 tu chu so: **{frac('has_digit')*100:.0f}%**.",
          f"- Ty le chi backchannel: **{frac('only_backchannel')*100:.0f}%**.",
          f"- Ty le rong (VAD bat nham, khong co chu): **{frac('is_empty')*100:.0f}%**.",
          f"- Ty le co tu khoa ngat (dung/khoan/cho): **{frac('has_stopword')*100:.0f}%**."]

    # phan bo so tu va SIR de thay truc phan tach
    nw = [e["n_words"] for e in all_ev]
    sir = [e["sir_db"] for e in all_ev if isinstance(e["sir_db"], (int, float))]
    dur = [e["cust_dur_s"] for e in all_ev]
    def q(a, p): return round(float(np.percentile(a, p)), 1) if a else 0
    L += ["", "## 3. Nguong tham khao (chon cat TP/FP)", "",
          "| Dac trung | p10 | p50 | p90 |", "| --- | ---: | ---: | ---: |",
          f"| số từ (n_words) | {q(nw,10)} | {q(nw,50)} | {q(nw,90)} |",
          f"| thời lượng khách (s) | {q(dur,10)} | {q(dur,50)} | {q(dur,90)} |",
          f"| SIR (dB) | {q(sir,10)} | {q(sir,50)} | {q(sir,90)} |",
          "", "> Cách dùng: mở `review_events.csv`, lọc theo các cột trên để thấy cụm "
          "true-positive (nhiều từ, có số) tách khỏi false-positive (rỗng, backchannel, ngắn)."]

    open(args.md, "w", encoding="utf-8").write("\n".join(L) + "\n")
    print(f"[summary] {args.md}", file=sys.stderr)


if __name__ == "__main__":
    main()
