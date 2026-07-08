from __future__ import annotations

import hashlib

import librosa
import numpy as np

from noise_gen import TARGET_SR, mix_at_snr, pink_noise, white_noise


def stable_seed(*parts: object) -> int:
    digest = hashlib.sha256("|".join(map(str, parts)).encode()).hexdigest()
    return int(digest[:8], 16)


def load_audio(path: str) -> np.ndarray:
    wav, _ = librosa.load(path, sr=TARGET_SR, mono=True)
    return wav.astype(np.float32)


def babble_noise(n: int, pool_df, rng: np.random.Generator, current_utt_id: str, k: int = 4) -> np.ndarray:
    pool = pool_df[pool_df.utt_id != current_utt_id]
    if len(pool) == 0:
        return pink_noise(n, rng)

    sample = pool.sample(n=min(k, len(pool)), random_state=int(rng.integers(0, 2**31 - 1)))
    mix = np.zeros(n, dtype=np.float64)
    for path in sample.audio_filepath:
        clip = load_audio(path)
        if clip.size == 0:
            continue
        reps = int(np.ceil(n / clip.size)) + 1
        tiled = np.tile(clip, reps)
        off = int(rng.integers(0, clip.size))
        mix += tiled[off : off + n]
    return mix.astype(np.float32)


def make_noisy(signal: np.ndarray, noise_type: str, snr: int | None, row, pool_df) -> np.ndarray:
    if noise_type == "clean":
        return signal

    rng = np.random.default_rng(stable_seed(row.utt_id, noise_type, snr))
    if noise_type == "white":
        noise = white_noise(signal.size, rng)
    elif noise_type == "pink":
        noise = pink_noise(signal.size, rng)
    elif noise_type == "babble":
        noise = babble_noise(signal.size, pool_df, rng, row.utt_id)
    else:
        raise ValueError(f"Unsupported noise_type: {noise_type}")

    return mix_at_snr(signal, noise, float(snr))
