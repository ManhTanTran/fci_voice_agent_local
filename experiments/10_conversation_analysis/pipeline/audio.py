"""Tang A1 — giai ma, tach kenh, VAD nang luong, dac trung am hoc.

Chay duoi venv nvidia_asr_nemo (co numpy/scipy/soundfile). Doc luon .wav mu-law 2 kenh.
Moi ham tra ve so tho de tang su kien tinh dac trung barge-in.
"""
from __future__ import annotations
import io, subprocess
import numpy as np

SR = 8000          # telephony goc
FRAME_MS = 25
HOP_MS = 10        # hop min de bat suon nang luong luc onset


def decode_stereo(path: str):
    """mu-law 2 kenh -> (ch_left, ch_right) float32 [-1,1] @ 8kHz. Dung ffmpeg cho chac."""
    cmd = ["ffmpeg", "-v", "error", "-i", path, "-f", "wav",
           "-acodec", "pcm_s16le", "-ar", str(SR), "-ac", "2", "-"]
    raw = subprocess.run(cmd, capture_output=True).stdout
    from scipy.io import wavfile
    _, data = wavfile.read(io.BytesIO(raw))
    x = data.astype(np.float32) / 32768.0
    if x.ndim == 1:                      # phong khi file mono
        x = np.stack([x, x], axis=1)
    return x[:, 0], x[:, 1]


def frames(x: np.ndarray):
    n = int(SR * FRAME_MS / 1000)
    hop = int(SR * HOP_MS / 1000)
    nf = 1 + max(0, (len(x) - n) // hop)
    idx = np.arange(nf) * hop
    return np.stack([x[i:i+n] for i in idx]) if nf else np.empty((0, n)), hop


def energy_db(x: np.ndarray) -> np.ndarray:
    fr, _ = frames(x)
    if len(fr) == 0:
        return np.array([])
    rms = np.sqrt(np.mean(fr**2, axis=1) + 1e-12)
    return 20 * np.log10(rms + 1e-12)


def otsu_threshold(edb: np.ndarray) -> float:
    """Nguong tach speech/silence tren histogram, bo digital-silence <=-100dB."""
    ev = edb[edb > -100]
    if len(ev) < 10:
        return float(np.percentile(edb, 50))
    hist, edges = np.histogram(ev, bins=64)
    p = hist / hist.sum()
    centers = (edges[:-1] + edges[1:]) / 2
    best_t, best_var = centers[0], -1.0
    for k in range(1, len(centers)):
        w0, w1 = p[:k].sum(), p[k:].sum()
        if w0 == 0 or w1 == 0:
            continue
        m0 = (p[:k] * centers[:k]).sum() / w0
        m1 = (p[k:] * centers[k:]).sum() / w1
        var = w0 * w1 * (m0 - m1) ** 2
        if var > best_var:
            best_var, best_t = var, centers[k]
    return float(best_t)


def vad_mask(x: np.ndarray):
    """Tra (mask bool theo frame, nguong dB, energy dB, noise_floor dB)."""
    edb = energy_db(x)
    thr = otsu_threshold(edb)
    floor = float(np.percentile(edb[edb > -100], 15)) if (edb > -100).any() else -90.0
    return edb > thr, thr, edb, floor


def frame_time(i: int) -> float:
    return i * HOP_MS / 1000.0


# ---------- dac trung am hoc tren mot doan [a,b] giay ----------

def _slice(x, a, b):
    return x[max(0, int(a*SR)):min(len(x), int(b*SR))]


def rms_db(x, a, b) -> float:
    seg = _slice(x, a, b)
    if len(seg) == 0:
        return -120.0
    return float(20*np.log10(np.sqrt(np.mean(seg**2)+1e-12)+1e-12))


def zero_crossing_rate(x, a, b) -> float:
    """ZCR cao = nhieu/phu am xat; thap-vua = nguyen am. Giup tach noise vs speech."""
    seg = _slice(x, a, b)
    if len(seg) < 2:
        return 0.0
    return float(np.mean(np.abs(np.diff(np.sign(seg))) > 0))


def spectral_flatness(x, a, b) -> float:
    """Do phang pho: gan 1 = giong nhieu trang; thap = co cau truc harmonic (tieng noi)."""
    seg = _slice(x, a, b)
    if len(seg) < 64:
        return 1.0
    mag = np.abs(np.fft.rfft(seg * np.hanning(len(seg)))) + 1e-10
    gm = np.exp(np.mean(np.log(mag)))
    am = np.mean(mag)
    return float(gm / am)


def onset_slope_db(x, onset_s, win_s=0.12) -> float:
    """Suon nang luong 120ms dau tu onset: dot ngot (duong lon) = chu dong chen."""
    e = energy_db(_slice(x, onset_s, onset_s + win_s))
    if len(e) < 3:
        return 0.0
    return float(e[-1] - e[0])
