"""Trace + phan loai cac LOAI ISSUE cua STT tren data FCI (so 3 model cheo nhau).

Muc dich: xuat bang chung CU THE (call_id + timestamp + text 3 model) cho tung loai loi,
de dua cho agent khac tim huong cai tien FastConformer.

Khong co ground-truth -> so cheo: FastConformer (Ky) vs ChunkFormer vs Parakeet.
Parakeet lam "tham chieu mem" cho chuoi so (sach nhat), Chunk lam doi chung.

Cac loai issue:
  A. fast_oov_digit   : FastConformer phun '⁇' (OOV) tren luot CO chuoi so  -> loi chi mang
  B. fast_oov_other   : FastConformer phun '⁇' tren luot khong phai chuoi so
  C. chunk_digitgroup : ChunkFormer gom so thanh so-dem (chen nghin/tram/linh) o chuoi ID
  D. para_junk        : Parakeet phun manh rac (dau cau / am tiet cut) tren doan non-speech
  E. fast_diverge     : luot noi dung, FastConformer lech HAN ca 2 model kia (proxy loi fast)

Chay:
  cd fci_voice_agent/experiments/10_conversation_analysis
  python tools/trace_stt_issues.py --out out --report-dir out/issues
Xuat: out/issues/00_summary.md  +  out/issues/<loai>.csv (day du instance)
"""
from __future__ import annotations
import argparse, csv, glob, json, os, re

MODELS = ["fastconformer", "chunkformer", "parakeet"]
OOV = "⁇"  # '⁇' — token unknown NeMo phun ra khi bi acoustic

# tu chu so tieng Viet (ca bien the) + tu 'gom nhom' bac (nghin/tram/...)
DIGIT_WORDS = set("khong không mot một hai ba bon bốn tu tư nam năm lam lăm sau sáu bay bảy "
                  "tam tám chin chín muoi mười".split())
GROUP_WORDS = set("nghin nghìn ngan ngàn tram trăm linh le lẻ".split())


def clean_words(t: str):
    """Bo OOV + dau cau + am tiet cut 1 ky tu -> list tu 'that'."""
    t = t.replace(OOV, " ")
    t = re.sub(r"[.,!?;:—\-]", " ", t.lower())
    return [w for w in t.split() if len(w) >= 2 or w in ("ạ", "à", "ừ", "ơ", "ồ", "à")]


def digit_count(t: str) -> int:
    return sum(1 for w in re.findall(r"\w+", t.lower()) if w in DIGIT_WORDS)


def load(model, out):
    d = {}
    for f in glob.glob(os.path.join(out, model, "*.json")):
        if "_index" in f:
            continue
        j = json.load(open(f, encoding="utf-8"))
        d[j["call_id"]] = j
    return d


def turn_index(j):
    """(spk, round(t0,1)) -> (t0, t1, text). VAD tat dinh nen key trung giua cac model."""
    idx = {}
    for t in j["turns"]:
        idx[(t["spk"], round(t["t0"], 1))] = (t["t0"], t.get("t1", t["t0"]), t["text"])
    return idx


def jaccard(a, b):
    sa, sb = set(a), set(b)
    if not sa and not sb:
        return 1.0
    return len(sa & sb) / max(1, len(sa | sb))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="out")
    ap.add_argument("--report-dir", default="out/issues")
    ap.add_argument("--topn", type=int, default=20, help="so vi du in trong summary moi loai")
    args = ap.parse_args()

    data = {m: load(m, args.out) for m in MODELS}
    common = sorted(set(data[MODELS[0]]) & set(data[MODELS[1]]) & set(data[MODELS[2]]))
    if not common:
        raise SystemExit(f"Khong tim thay du 3 model trong {args.out}/ (can fastconformer+chunkformer+parakeet)")

    buckets = {k: [] for k in
               ["A_fast_oov_digit", "B_fast_oov_other", "C_chunk_digitgroup", "D_para_junk", "E_fast_diverge"]}

    for c in common:
        ti = {m: turn_index(data[m][c]) for m in MODELS}
        keys = set().union(*[set(ti[m]) for m in MODELS])
        for k in sorted(keys, key=lambda x: x[1]):
            spk, _ = k
            f_t0, f_t1, f_raw = ti["fastconformer"].get(k, (k[1], k[1], ""))
            _, _, ch_raw = ti["chunkformer"].get(k, (0, 0, ""))
            _, _, pa_raw = ti["parakeet"].get(k, (0, 0, ""))
            dur = round(f_t1 - f_t0, 2)
            row = {"call_id": c, "spk": spk, "t0": round(f_t0, 1), "dur_s": dur,
                   "fast": f_raw.strip(), "chunk": ch_raw.strip(), "parakeet": pa_raw.strip()}

            # ngu canh chuoi so: lay max digit-count giua chunk & parakeet (fast hay hong nen khong dung)
            is_digit_ctx = max(digit_count(ch_raw), digit_count(pa_raw)) >= 3

            # A/B: fast phun OOV
            if OOV in f_raw:
                row2 = dict(row, n_oov=f_raw.count(OOV))
                buckets["A_fast_oov_digit" if is_digit_ctx else "B_fast_oov_other"].append(row2)

            # C: chunk gom so (co GROUP_WORDS) ma parakeet khong, tren ngu canh so
            if is_digit_ctx:
                ch_grp = [w for w in re.findall(r"\w+", ch_raw.lower()) if w in GROUP_WORDS]
                pa_grp = [w for w in re.findall(r"\w+", pa_raw.lower()) if w in GROUP_WORDS]
                if ch_grp and not pa_grp:
                    buckets["C_chunk_digitgroup"].append(dict(row, chunk_group="+".join(ch_grp)))

            # D: parakeet rac (raw co ky tu nhung lam sach thanh rong) + 2 CTC deu rong
            fw, cw, pw = clean_words(f_raw), clean_words(ch_raw), clean_words(pa_raw)
            if pa_raw.strip() and not pw and not fw and not cw:
                buckets["D_para_junk"].append(row)

            # E: luot noi dung — chunk & parakeet dong thuan (>=3 tu, jaccard cao) ma fast lech han
            if len(cw) >= 3 and len(pw) >= 3 and jaccard(cw, pw) >= 0.5 and OOV not in f_raw:
                if jaccard(fw, cw) < 0.3 and jaccard(fw, pw) < 0.3:
                    buckets["E_fast_diverge"].append(dict(row, jac_fast_ref=round(max(jaccard(fw, cw), jaccard(fw, pw)), 2)))

    os.makedirs(args.report_dir, exist_ok=True)

    # ---- CSV day du moi loai ----
    for name, rows in buckets.items():
        if not rows:
            continue
        cols = list(rows[0].keys())
        with open(os.path.join(args.report_dir, f"{name}.csv"), "w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=cols)
            w.writeheader()
            w.writerows(rows)

    # ---- summary markdown ----
    desc = {
        "A_fast_oov_digit": "FastConformer phun `⁇` (OOV) tren luot CO chuoi so — mat han day so (loi chi mang)",
        "B_fast_oov_other": "FastConformer phun `⁇` tren luot khong phai chuoi so",
        "C_chunk_digitgroup": "ChunkFormer gom so thanh so-dem (chen nghin/tram/linh) trong chuoi ID",
        "D_para_junk": "Parakeet phun manh rac tren doan non-speech (2 model CTC deu rong)",
        "E_fast_diverge": "Luot noi dung: FastConformer lech HAN ca ChunkFormer + Parakeet (proxy loi fast)",
    }
    lines = ["# Trace issue STT tren data FCI\n",
             f"Nguon: `{args.out}/` · {len(common)} cuoc · so 3 model cheo nhau (khong co ground-truth).",
             "Moi loai co file CSV day du kem: `<loai>.csv` (call_id, spk, t0, dur_s, text 3 model).\n",
             "## Tong so instance moi loai\n",
             "| Loai | Mo ta | So luot | So call dinh |",
             "|---|---|---|---|"]
    for name in buckets:
        rows = buckets[name]
        ncall = len(set(r["call_id"] for r in rows))
        lines.append(f"| `{name}` | {desc[name]} | {len(rows)} | {ncall} |")

    for name in buckets:
        rows = buckets[name]
        if not rows:
            continue
        lines.append(f"\n## {name} — {desc[name]}")
        # top call theo so instance
        by_call = {}
        for r in rows:
            by_call.setdefault(r["call_id"], 0)
            by_call[r["call_id"]] += 1
        top_calls = sorted(by_call.items(), key=lambda x: -x[1])[:8]
        lines.append("**Call dinh nhieu nhat:** " +
                     " · ".join(f"`{cid}` ({n})" for cid, n in top_calls))
        lines.append(f"\n**{min(args.topn, len(rows))} vi du (nghe bang cut_clip.py --call <id> --t <t0>):**\n")
        for r in rows[:args.topn]:
            lines.append(f"- `{r['call_id']}` · {r['spk']} @ {r['t0']}s (dur {r['dur_s']}s)")
            lines.append(f"    - fast: `{r['fast'] or '(rong)'}`")
            lines.append(f"    - chun: `{r['chunk'] or '(rong)'}`")
            lines.append(f"    - para: `{r['parakeet'] or '(rong)'}`")

    open(os.path.join(args.report_dir, "00_summary.md"), "w", encoding="utf-8").write("\n".join(lines))
    print(f"[trace] xong. Tong instance moi loai:")
    for name in buckets:
        print(f"  {name:22} {len(buckets[name]):4}  ({len(set(r['call_id'] for r in buckets[name]))} call)")
    print(f"[trace] bao cao -> {args.report_dir}/00_summary.md  + CSV moi loai")


if __name__ == "__main__":
    main()
