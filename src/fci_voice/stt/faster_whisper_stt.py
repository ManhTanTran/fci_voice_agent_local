"""Adapter STT dùng faster-whisper (CTranslate2).

Chọn faster-whisper vì chạy tốt trên CPU (int8) — KHÔNG cần torch/CUDA, hợp với
GB10 (onnxruntime/torch chưa cấu hình GPU). Tiếng Anh để đo độ mature ban đầu;
tiếng Việt/telephony 8kHz là bước sau (cần resample + model vi).
"""

from __future__ import annotations

import time
from dataclasses import dataclass

import numpy as np


@dataclass
class STTResult:
    text: str
    latency_s: float


class FasterWhisperSTT:
    """Lazy-load để import package không kéo theo model nặng."""

    def __init__(
        self,
        model_size: str = "base.en",
        device: str = "cpu",
        compute_type: str = "int8",
    ) -> None:
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self._model = None

    def load(self) -> "FasterWhisperSTT":
        from faster_whisper import WhisperModel

        self._model = WhisperModel(
            self.model_size, device=self.device, compute_type=self.compute_type
        )
        return self

    def transcribe(
        self, audio: np.ndarray, sample_rate: int = 16000, language: str = "en"
    ) -> STTResult:
        """audio: mono float32 [-1,1]. faster-whisper kỳ vọng 16kHz."""
        if self._model is None:
            self.load()
        audio = np.asarray(audio, dtype=np.float32)
        if sample_rate != 16000:
            # v1 chưa resample (LibriSpeech sẵn 16kHz). Telephony 8kHz xử lý ở bước sau.
            raise ValueError(
                f"faster-whisper cần 16kHz, nhận {sample_rate}Hz — cần resample (bước sau)"
            )
        t0 = time.perf_counter()
        segments, _ = self._model.transcribe(audio, language=language, beam_size=1)
        text = "".join(seg.text for seg in segments).strip()
        return STTResult(text=text, latency_s=time.perf_counter() - t0)
