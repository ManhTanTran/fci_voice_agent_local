"""Orchestrate Tang A cho 1 cuoc hoac toan bo. Xuat dossier JSON moi cuoc.

Chay (duoi venv co nemo):
  cd fci_voice_agent
  uv run --project ../nvidia_asr_nemo python -m experiments.10_conversation_analysis.pipeline.run \
      --audio-dir data/audio_interrupt --out experiments/10_conversation_analysis/out
Hoac 1 file:
  ... --audio data/audio_interrupt/<uuid>.wav
"""
from __future__ import annotations
import argparse, glob, json, os, sys, time

# cho phep chay bang -m HOAC truc tiep
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pipeline import audio as A          # noqa: E402
from pipeline import events as E         # noqa: E402


def process_call(asr, path: str) -> dict:
    ch0, ch1 = A.decode_stereo(path)
    dur = len(ch0) / A.SR
    m0, thr0, e0, floor0 = A.vad_mask(ch0)
    m1, thr1, e1, floor1 = A.vad_mask(ch1)
    n = min(len(m0), len(m1))
    m0, m1 = m0[:n], m1[:n]

    bot_ch = E.assign_bot_channel(m0, m1)
    ch_bot, ch_cust = (ch0, ch1) if bot_ch == 0 else (ch1, ch0)
    m_bot, m_cust = (m0, m1) if bot_ch == 0 else (m1, m0)
    floor_cust = floor1 if bot_ch == 0 else floor0

    seg_bot = E.segments_from_mask(m_bot)
    seg_cust = E.segments_from_mask(m_cust)

    # ASR ca hai kenh (theo luot)
    cust_texts = asr.transcribe_segments(ch_cust, seg_cust) if asr else [""]*len(seg_cust)
    bot_texts = asr.transcribe_segments(ch_bot, seg_bot) if asr else [""]*len(seg_bot)

    events = E.build_events(ch_cust, ch_bot, m_cust, m_bot, floor_cust,
                            seg_cust, seg_bot, cust_texts, bot_texts)
    metrics = E.call_metrics(seg_cust, seg_bot, m_cust, m_bot, events, dur)

    return {
        "call_id": os.path.basename(path).replace(".wav", ""),
        "bot_ch": bot_ch,
        "metrics": metrics,
        "turns": _turns(seg_bot, bot_texts, seg_cust, cust_texts),
        "events": events,
    }


def _turns(seg_bot, bot_texts, seg_cust, cust_texts):
    """Dong luot thong nhat 2 ben theo mgio, phuc vu tool timeline."""
    rows = []
    for (s, e), t in zip(seg_bot, bot_texts):
        rows.append({"spk": "bot", "t0": round(s, 2), "t1": round(e, 2), "text": t})
    for (s, e), t in zip(seg_cust, cust_texts):
        rows.append({"spk": "cust", "t0": round(s, 2), "t1": round(e, 2), "text": t})
    return sorted(rows, key=lambda r: r["t0"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--audio")
    ap.add_argument("--audio-dir")
    ap.add_argument("--out", required=True, help="thu muc goc; dossier ghi vao <out>/<stt>/")
    ap.add_argument("--stt", default="fastconformer",
                    choices=["fastconformer", "chunkformer", "parakeet"])
    ap.add_argument("--no-asr", action="store_true", help="bo qua ASR (chi test phan tin hieu)")
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    outdir = os.path.join(args.out, args.stt)   # moi model 1 thu muc rieng, khong de nhau
    os.makedirs(outdir, exist_ok=True)
    if args.audio:
        paths = [args.audio]
    else:
        paths = sorted(p for p in glob.glob(os.path.join(args.audio_dir, "*.wav"))
                       if "(1)" not in p)
    if args.limit:
        paths = paths[:args.limit]

    asr = None
    if not args.no_asr:
        from pipeline.backends import get_asr
        print(f"[run] nap model STT '{args.stt}' ...", file=sys.stderr, flush=True)
        t0 = time.perf_counter()
        asr = get_asr(args.stt)
        print(f"[run] STT '{args.stt}' san sang device={asr.device} ({time.perf_counter()-t0:.1f}s)",
              file=sys.stderr, flush=True)

    index = []
    for i, p in enumerate(paths):
        t0 = time.perf_counter()
        try:
            d = process_call(asr, p)
        except Exception as ex:
            print(f"[run] LOI {os.path.basename(p)}: {ex}", file=sys.stderr)
            continue
        d["stt"] = args.stt
        outp = os.path.join(outdir, d["call_id"] + ".json")
        json.dump(d, open(outp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        m = d["metrics"]
        index.append({"call_id": d["call_id"], **m})
        print(f"[{i+1}/{len(paths)}] {d['call_id'][:8]} "
              f"cand={m['n_bargein_cand']} stop={m['n_bot_stopped']} "
              f"rbmis={m['n_readback_mismatch']} ({time.perf_counter()-t0:.1f}s)",
              file=sys.stderr, flush=True)
    json.dump(index, open(os.path.join(outdir, "_index.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(f"[run] xong {len(index)} cuoc -> {outdir}", file=sys.stderr)


if __name__ == "__main__":
    main()
