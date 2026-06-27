"""Adapter LLM dùng HuggingFace transformers (chạy GPU GB10 qua torch cu130).

Model nhỏ open-source (mặc định Qwen2.5-1.5B-Instruct) để test hội thoại cơ bản.
Lazy-load. `chat(messages)` nhận list {"role","content"} → giữ được ngữ cảnh đa lượt.
"""

from __future__ import annotations

import time
from dataclasses import dataclass


@dataclass
class LLMResult:
    text: str
    latency_s: float


class TransformersLLM:
    def __init__(
        self,
        model_name: str = "Qwen/Qwen2.5-1.5B-Instruct",
        device: str | None = None,
    ) -> None:
        self.model_name = model_name
        self.device = device
        self.device_str = None
        self._tok = None
        self._model = None

    def load(self) -> "TransformersLLM":
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer

        self.device = self.device or ("cuda" if torch.cuda.is_available() else "cpu")
        dtype = torch.float16 if self.device == "cuda" else torch.float32
        self._tok = AutoTokenizer.from_pretrained(self.model_name)
        self._model = AutoModelForCausalLM.from_pretrained(
            self.model_name, torch_dtype=dtype
        ).to(self.device)
        self.device_str = f"{self.device}/{dtype}"
        return self

    # Truy cập tokenizer/model cho structured decoding (xgrammar cần vocab + tokenizer).
    @property
    def tokenizer(self):
        if self._tok is None:
            self.load()
        return self._tok

    @property
    def model(self):
        if self._model is None:
            self.load()
        return self._model

    def chat(
        self,
        messages: list[dict],
        max_new_tokens: int = 96,
        logits_processor=None,
    ) -> LLMResult:
        import torch

        if self._model is None:
            self.load()
        prompt = self._tok.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        inputs = self._tok([prompt], return_tensors="pt").to(self.device)
        gen_kw = dict(max_new_tokens=max_new_tokens, do_sample=False)
        if logits_processor is not None:
            gen_kw["logits_processor"] = logits_processor  # ép grammar khi có
        t0 = time.perf_counter()
        with torch.no_grad():
            out = self._model.generate(**inputs, **gen_kw)
        gen = out[0][inputs.input_ids.shape[1] :]
        resp = self._tok.decode(gen, skip_special_tokens=True).strip()
        return LLMResult(text=resp, latency_s=time.perf_counter() - t0)
