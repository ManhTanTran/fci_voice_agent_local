"""T1 — dung transcript dong thoi gian cho MOT cuoc, dang markdown de doc trong IDE.

Hai ben theo mgio, danh dau su kien barge-in kem dac trung gon. Day so da an.
Chay:
  python tools/timeline_md.py --call <uuid> [--out out]
"""
from __future__ import annotations
import argparse, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pipeline.util import mask_digits   # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--call", required=True)
    ap.add_argument("--out", default="out")
    ap.add_argument("--md", default=None)
    ap.add_argument("--mask", action="store_true", help="an day so (chi dung cho data khach that)")
    args = ap.parse_args()
    mask = mask_digits if args.mask else (lambda s: s)

    d = json.load(open(os.path.join(args.out, args.call + ".json"), encoding="utf-8"))
    m = d["metrics"]
    ev_by_onset = {round(e["onset_s"], 2): e for e in d["events"]}

    L = [f"# Timeline cuoc {args.call[:8]}", "",
         f"> bot = kênh {d['bot_ch']} · dài {m['dur_s']}s · "
         f"{m['n_bargein_cand']} ứng viên barge-in · bot dừng {m['n_bot_stopped']} · "
         f"readback lệch {m['n_readback_mismatch']}",
         "> Cột trái BOT, phải KHÁCH. `[BARGE-IN]` = onset khách khi bot đang nói."
         + (" Dãy số đã ẩn." if args.mask else ""),
         "", "| t (s) | BOT | KHÁCH | cờ sự kiện |", "| ---: | --- | --- | --- |"]
    for r in d["turns"]:
        t = f"{r['t0']:.1f}"
        txt = mask(r["text"]) or "—"
        bot = txt if r["spk"] == "bot" else ""
        cust = txt if r["spk"] == "cust" else ""
        flag = ""
        if r["spk"] == "cust":
            e = ev_by_onset.get(round(r["t0"], 2))
            if e:
                bits = [f"nw={e['n_words']}", f"sir={e['sir_db']}"]
                if e["has_digit"]: bits.append("SỐ")
                if e["has_stopword"]: bits.append("STOP-KW")
                if e["only_backchannel"]: bits.append("b/chan")
                if e["is_empty"]: bits.append("rỗng")
                bits.append("botDừng" if e["bot_stopped"] else "botTIẾP")
                flag = "**[BARGE-IN]** " + " ".join(bits)
        L.append(f"| {t} | {bot} | {cust} | {flag} |")

    out_md = args.md or os.path.join(args.out, "timeline_" + args.call[:8] + ".md")
    open(out_md, "w", encoding="utf-8").write("\n".join(L) + "\n")
    print(f"[timeline] {out_md}", file=sys.stderr)


if __name__ == "__main__":
    main()
