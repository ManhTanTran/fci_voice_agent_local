"""T2 — cat clip quanh mot moc giay de nghe mot su kien barge-in.

Xuat 3 file: kenh khach, kenh bot, va ban tron stereo (bot trai / khach phai).
Chay:
  python tools/cut_clip.py --call <uuid> --t 79.3 [--win 3] [--audio-dir data/audio_interrupt]
"""
from __future__ import annotations
import argparse, os, sys
import numpy as np
import soundfile as sf
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pipeline import audio as A          # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--call", required=True)
    ap.add_argument("--t", type=float, required=True)
    ap.add_argument("--win", type=float, default=3.0, help="nua cua so giay moi ben")
    ap.add_argument("--audio-dir", default="data/audio_interrupt")
    ap.add_argument("--out", default="experiments/10_conversation_analysis/out/clips")
    args = ap.parse_args()

    path = os.path.join(args.audio_dir, args.call + ".wav")
    if not os.path.isfile(path):
        sys.exit(f"khong thay {path}")
    ch0, ch1 = A.decode_stereo(path)
    # xac dinh kenh bot bang chao truoc de dat trai/phai cho nhat quan
    m0, *_ = A.vad_mask(ch0)
    m1, *_ = A.vad_mask(ch1)
    from pipeline import events as E
    bot_ch = E.assign_bot_channel(m0[:min(len(m0), len(m1))], m1[:min(len(m0), len(m1))])
    ch_bot, ch_cust = (ch0, ch1) if bot_ch == 0 else (ch1, ch0)

    a = max(0, int((args.t - args.win) * A.SR))
    b = int((args.t + args.win) * A.SR)
    cust = ch_cust[a:b]
    bot = ch_bot[a:b]
    n = min(len(cust), len(bot))
    stereo = np.stack([bot[:n], cust[:n]], axis=1)   # trai=bot, phai=khach

    os.makedirs(args.out, exist_ok=True)
    tag = f"{args.call[:8]}_t{args.t:.1f}"
    p_cust = os.path.join(args.out, tag + "_khach.wav")
    p_bot = os.path.join(args.out, tag + "_bot.wav")
    p_mix = os.path.join(args.out, tag + "_stereo.wav")
    sf.write(p_cust, cust, A.SR)
    sf.write(p_bot, bot, A.SR)
    sf.write(p_mix, stereo, A.SR)
    print(f"khach : {p_cust}")
    print(f"bot   : {p_bot}")
    print(f"stereo: {p_mix}  (tai nghe trai=bot phai=khach)")


if __name__ == "__main__":
    main()
