"""Cấu hình runtime — đọc từ biến môi trường, KHÔNG hardcode secret.

Giai đoạn smoke chỉ cần vài trường tối thiểu. Mở rộng dần khi cắm model thật.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    # "mock" = giả lập để thông luồng; "local" = cắm model self-host trên DGX.
    mode: str = "mock"
    # Endpoint LLM OpenAI-compatible (vLLM/SGLang) khi mode="local".
    # KHÔNG đặt giá trị mặc định chứa credential thật.
    llm_base_url: str = ""
    llm_model: str = ""
    # Tần số mẫu mục tiêu cho telephony.
    sample_rate: int = 8000

    @classmethod
    def from_env(cls) -> "Config":
        return cls(
            mode=os.getenv("FCI_MODE", "mock"),
            llm_base_url=os.getenv("FCI_LLM_BASE_URL", ""),
            llm_model=os.getenv("FCI_LLM_MODEL", ""),
            sample_rate=int(os.getenv("FCI_SAMPLE_RATE", "8000")),
        )
