"""Bộ sinh nhiễu TẤT ĐỊNH (deterministic) + trộn theo SNR chính xác.

Mọi hàm sinh nhiễu nhận `rng` (numpy Generator có seed cố định) hoặc seed int,
nên cùng input -> cùng output, tái lập 100%. Đây là điều kiện để nhãn
(noise_type, snr_db) là ground-truth-by-construction và verifier tái lập được.
"""
from __future__ import annotations

import numpy as np


TARGET_SR = 16_000  # PhoWhisper ăn 16kHz mono; chuẩn hoá 1 lần ở loader


# ---------------------------------------------------------------------------
# Sinh các loại nhiễu (mỗi hàm trả mảng float32 cùng độ dài n)
# ---------------------------------------------------------------------------
def white_noise(n: int, rng: np.random.Generator) -> np.ndarray:
    """Nhiễu trắng: Gaussian phổ phẳng. Baseline đơn giản nhất."""
    return rng.standard_normal(n).astype(np.float32)


def pink_noise(n: int, rng: np.random.Generator) -> np.ndarray:
    """Nhiễu hồng (1/f): năng lượng giảm theo tần số, giống ồn nền môi trường
    (quạt, điều hoà, hiss) hơn nhiễu trắng. Sinh bằng cách nặn phổ trắng
    theo 1/sqrt(f) trong miền tần số rồi biến đổi ngược -> tất định theo rng.
    """
    white = rng.standard_normal(n)
    # FFT thực; scale mỗi bin theo 1/sqrt(f) (f=0 giữ nguyên để tránh chia 0)
    spectrum = np.fft.rfft(white)
    freqs = np.arange(spectrum.size)
    scale = np.ones_like(freqs, dtype=np.float64)
    scale[1:] = 1.0 / np.sqrt(freqs[1:])
    pink = np.fft.irfft(spectrum * scale, n=n)
    return pink.astype(np.float32)


def babble_noise(n: int, others: list[np.ndarray], rng: np.random.Generator) -> np.ndarray:
    """Babble = nhiều giọng người chồng lên nhau (giống quán đông, tổng đài ồn).
    Trộn nhiều clip speech KHÁC (không phải clip đang chấm) với offset ngẫu nhiên
    nhưng có seed -> tất định. Đây là loại nhiễu sát thực tế voice-agent nhất
    trong 3 loại synthetic ở đây.
    """
    if not others:
        # fallback: không có clip khác thì coi như pink (ghi rõ ở manifest vẫn babble)
        return pink_noise(n, rng)
    mix = np.zeros(n, dtype=np.float64)
    # chọn tối đa 6 giọng nền để tiếng "babble" đủ dày mà không quá nặng
    k = min(6, len(others))
    idxs = rng.choice(len(others), size=k, replace=False)
    for i in idxs:
        clip = others[i]
        if clip.size == 0:
            continue
        # lặp clip cho đủ dài rồi cắt tại offset ngẫu nhiên -> phủ kín n mẫu
        reps = int(np.ceil(n / clip.size)) + 1
        tiled = np.tile(clip, reps)
        off = int(rng.integers(0, clip.size))
        seg = tiled[off:off + n]
        mix += seg.astype(np.float64)
    return mix.astype(np.float32)


# ---------------------------------------------------------------------------
# Trộn theo SNR chính xác
# ---------------------------------------------------------------------------
def _rms(x: np.ndarray) -> float:
    """Root-mean-square = căn công suất trung bình. Dùng làm thước năng lượng."""
    return float(np.sqrt(np.mean(np.square(x, dtype=np.float64)) + 1e-12))


def mix_at_snr(signal: np.ndarray, noise: np.ndarray, snr_db: float) -> np.ndarray:
    """Trộn signal + noise sao cho đạt ĐÚNG SNR mục tiêu.

    SNR_dB = 10*log10(P_signal / P_noise). Giữ nguyên signal, scale noise:
        P_noise_target = P_signal / 10^(SNR/10)
        gain = sqrt(P_noise_target) / rms(noise)
    Nhờ đó nhãn snr_db là chính xác tuyệt đối (ground-truth-by-construction).
    """
    n = min(signal.size, noise.size)
    sig = signal[:n].astype(np.float64)
    noi = noise[:n].astype(np.float64)

    p_sig = np.mean(np.square(sig)) + 1e-12
    p_noi_target = p_sig / (10.0 ** (snr_db / 10.0))
    gain = np.sqrt(p_noi_target) / (_rms(noi) + 1e-12)
    mixed = sig + gain * noi

    # chống clip: nếu vượt [-1,1] thì scale cả tín hiệu về an toàn (giữ SNR vì
    # scale đồng đều signal+noise không đổi tỉ lệ công suất)
    peak = np.max(np.abs(mixed)) + 1e-12
    if peak > 0.99:
        mixed = mixed * (0.99 / peak)
    return mixed.astype(np.float32)


def make_noise(noise_type: str, n: int, seed: int, others: list[np.ndarray] | None = None) -> np.ndarray:
    """Factory tất định: (noise_type, seed) -> mảng nhiễu độ dài n.
    Seed suy từ nội dung nên cùng clip+điều kiện luôn ra cùng nhiễu.
    """
    rng = np.random.default_rng(seed)
    if noise_type == "white":
        return white_noise(n, rng)
    if noise_type == "pink":
        return pink_noise(n, rng)
    if noise_type == "babble":
        return babble_noise(n, others or [], rng)
    raise ValueError(f"noise_type không hỗ trợ: {noise_type}")
