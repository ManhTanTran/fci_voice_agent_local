"""Nạp test case audio tiếng Anh (LibriSpeech dummy của HF — nhỏ, tải nhanh).

Mỗi case = (id, audio float32 mono 16kHz, transcript chuẩn). Dùng để đo WER.
"""

from __future__ import annotations

import io
from dataclasses import dataclass

import numpy as np


@dataclass
class Case:
    id: str
    audio: np.ndarray  # float32 mono 16kHz
    sample_rate: int
    ref: str  # transcript tham chiếu

    @property
    def duration_s(self) -> float:
        return len(self.audio) / self.sample_rate


def load_cases(n: int = 10):
    """Trả về list[Case]. Ném exception nếu không tải được (harness sẽ bắt + báo).

    Tắt auto-decode của `datasets` (Audio(decode=False)) và decode thẳng bằng
    soundfile → tránh phụ thuộc librosa/numba (nặng + dễ vỡ trên arm64).
    """
    import soundfile as sf
    from datasets import Audio, load_dataset

    ds = load_dataset(
        "hf-internal-testing/librispeech_asr_dummy", "clean", split="validation"
    )
    ds = ds.cast_column("audio", Audio(decode=False))  # lấy path/bytes thô

    cases: list[Case] = []
    for i, item in enumerate(ds):
        if i >= n:
            break
        a = item["audio"]
        raw = a.get("bytes")
        if raw:
            arr, sr = sf.read(io.BytesIO(raw), dtype="float32")
        else:
            arr, sr = sf.read(a["path"], dtype="float32")
        if arr.ndim > 1:  # gộp về mono nếu lỡ stereo
            arr = arr.mean(axis=1)
        cases.append(
            Case(
                id=str(item.get("id", f"case{i}")),
                audio=np.asarray(arr, dtype=np.float32),
                sample_rate=int(sr),
                ref=item["text"],
            )
        )
    return cases
