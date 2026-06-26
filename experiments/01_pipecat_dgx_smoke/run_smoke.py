#!/usr/bin/env python3
"""Smoke + kiểm kê Pipecat trên DGX (arm64 / GB10).

Trả lời 2 câu hỏi của exp 01:
  1. Pipecat có cài + chạy nổi một vòng tối thiểu trên GB10/arm64 không?
  2. Trong các thành phần ĐÃ KHẢO SÁT, cái nào self-host được trên máy này?

Thiết kế "discovery": mỗi mức bọc try/except, IN RÕ lỗi thật thay vì crash —
vì mục tiêu là kiểm kê hiện trạng, lỗi cũng là thông tin.

Chạy:  uv run python experiments/01_pipecat_dgx_smoke/run_smoke.py
"""

from __future__ import annotations

import asyncio
import importlib
import platform
import sys
from datetime import datetime
from pathlib import Path

# Cho phép import fci_voice cả khi chưa `uv sync` cài editable (src-layout fallback).
REPO_ROOT = Path(__file__).resolve().parents[2]
SRC = REPO_ROOT / "src"
if SRC.exists() and str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

RESULTS_DIR = Path(__file__).resolve().parent / "results"
_lines: list[str] = []


def out(msg: str = "") -> None:
    print(msg)
    _lines.append(msg)


# --------------------------------------------------------------------------- #
# L0 — máy sống: môi trường + import engine
# --------------------------------------------------------------------------- #
def level0_env() -> bool:
    out("=" * 64)
    out("L0 — MÔI TRƯỜNG + IMPORT ENGINE")
    out("=" * 64)
    out(f"python      : {sys.version.split()[0]}")
    out(f"platform    : {platform.platform()}")
    out(f"machine     : {platform.machine()}  (mong đợi aarch64 trên GB10)")
    try:
        import pipecat  # noqa: F401

        ver = getattr(pipecat, "__version__", "?")
        out(f"pipecat     : ✅ import OK, version = {ver}")
        return True
    except Exception as e:  # noqa: BLE001
        out(f"pipecat     : ❌ import FAIL — {type(e).__name__}: {e}")
        return False


# --------------------------------------------------------------------------- #
# L1 — vòng tối thiểu: engine chảy frame + kết thúc sạch
# --------------------------------------------------------------------------- #
def level1_engine() -> bool:
    out("")
    out("=" * 64)
    out("L1 — VÒNG TEXT TỐI THIỂU (engine chảy frame)")
    out("=" * 64)
    try:
        from fci_voice.pipeline.build import run_text_smoke

        seen = asyncio.run(run_text_smoke("xin chào DGX"))
        out(f"text đi qua pipeline: {seen}")
        ok = any("XIN CHÀO" in s.upper() for s in seen)
        out("engine chạy + kết thúc sạch: " + ("✅ PASS" if ok else "⚠️ chạy nhưng output lạ"))
        return ok
    except Exception as e:  # noqa: BLE001
        out(f"❌ FAIL — {type(e).__name__}: {e}")
        out("   (lỗi này hé lộ API Pipecat thật của bản đã cài → khớp lại build.py)")
        return False


# --------------------------------------------------------------------------- #
# L2 — kiểm kê thành phần: thứ nào self-host được trên GB10
# --------------------------------------------------------------------------- #
# (tên hiển thị, module import thử, ↔ layer khảo sát)
PROBES = [
    ("pipecat engine",        "pipecat",                     "—"),
    ("Silero VAD (pipecat)",  "pipecat.audio.vad.silero",    "03"),
    ("turn (pipecat)",        "pipecat.audio.turn",          "05"),
    ("onnxruntime",           "onnxruntime",                 "03/05"),
    ("torch",                 "torch",                       "04/06"),
    ("faster-whisper",        "faster_whisper",              "04"),
    ("NeMo ASR",              "nemo.collections.asr",        "04"),
    ("Piper TTS",             "piper",                       "tts"),
    ("Kokoro TTS",            "kokoro",                      "tts"),
    ("vLLM (LLM serving)",    "vllm",                        "06"),
]


def level2_inventory() -> None:
    out("")
    out("=" * 64)
    out("L2 — KIỂM KÊ THÀNH PHẦN (self-host được gì trên GB10)")
    out("=" * 64)
    out(f"{'thành phần':<22}{'layer':<8}trạng thái")
    out("-" * 64)
    for name, mod, layer in PROBES:
        try:
            importlib.import_module(mod)
            status = "✅ import OK"
        except Exception as e:  # noqa: BLE001
            status = f"❌ {type(e).__name__}"
        out(f"{name:<22}{layer:<8}{status}")

    # chi tiết phần cứng/accelerator
    out("")
    out("Chi tiết accelerator:")
    try:
        import onnxruntime as ort

        out(f"  onnxruntime providers: {ort.get_available_providers()}")
    except Exception as e:  # noqa: BLE001
        out(f"  onnxruntime: chưa có ({type(e).__name__})")
    try:
        import torch

        out(f"  torch {torch.__version__} | cuda.is_available={torch.cuda.is_available()}")
        if torch.cuda.is_available():
            out(f"  torch GPU: {torch.cuda.get_device_name(0)}")
    except Exception as e:  # noqa: BLE001
        out(f"  torch: chưa có ({type(e).__name__})")


def main() -> int:
    out(f"# fci_voice — smoke DGX @ {datetime.now().isoformat(timespec='seconds')}")
    out("")
    l0 = level0_env()
    l1 = level1_engine() if l0 else False
    if l0:
        level2_inventory()

    out("")
    out("=" * 64)
    out("TỔNG KẾT")
    out("=" * 64)
    out(f"L0 môi trường + import engine : {'✅' if l0 else '❌'}")
    out(f"L1 engine chảy frame          : {'✅' if l1 else '❌'}")
    out("L2 kiểm kê                    : xem bảng phía trên")

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    report = RESULTS_DIR / f"smoke_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    report.write_text("\n".join(_lines) + "\n", encoding="utf-8")
    out("")
    out(f"📄 Báo cáo lưu: {report}")
    return 0 if (l0 and l1) else 1


if __name__ == "__main__":
    raise SystemExit(main())
