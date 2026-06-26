"""TTS qua Piper (CPU/ONNX) + fallback WAV placeholder.

Piper hay vướng build trên arm64 → nếu không dùng được, ghi WAV im lặng (độ dài
~ theo số từ) để vòng vẫn khép + xác nhận plumbing audio-out. Harness báo rõ thật/placeholder.
"""

from __future__ import annotations

import wave

import numpy as np


class PiperTTS:
    """Lazy-load. Ném exception nếu lib/model chưa sẵn (harness sẽ fallback)."""

    def __init__(self, model_path: str) -> None:
        self.model_path = model_path
        self._voice = None

    def load(self) -> "PiperTTS":
        from piper.voice import PiperVoice

        self._voice = PiperVoice.load(self.model_path)
        return self

    def synthesize(self, text: str, out_wav: str) -> str:
        """Chịu được nhiều biến thể API piper (1.4.x đổi nhiều lần)."""
        if self._voice is None:
            self.load()
        v = self._voice

        # API có sẵn synthesize_wav(text, wav_file)
        if hasattr(v, "synthesize_wav"):
            with wave.open(out_wav, "wb") as wf:
                v.synthesize_wav(text, wf)
            return out_wav

        # API generator: synthesize(text) -> iterable AudioChunk
        chunks = None
        try:
            chunks = list(v.synthesize(text))
        except TypeError:
            chunks = None
        if chunks and hasattr(chunks[0], "audio_int16_bytes"):
            sr = getattr(chunks[0], "sample_rate", 22050)
            data = b"".join(c.audio_int16_bytes for c in chunks)
            with wave.open(out_wav, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(sr)
                wf.writeframes(data)
            return out_wav

        # API cũ: synthesize(text, wav_file)
        with wave.open(out_wav, "wb") as wf:
            v.synthesize(text, wf)
        return out_wav


def placeholder_wav(text: str, out_wav: str, sample_rate: int = 16000) -> str:
    """WAV im lặng độ dài ~ số từ — chỉ để xác nhận plumbing khi chưa có TTS thật."""
    n_words = max(1, len(text.split()))
    n_samples = int(min(8.0, 0.35 * n_words) * sample_rate)
    with wave.open(out_wav, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(np.zeros(n_samples, dtype=np.int16).tobytes())
    return out_wav
