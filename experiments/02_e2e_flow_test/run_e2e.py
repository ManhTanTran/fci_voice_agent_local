#!/usr/bin/env python3
"""Harness test THÔNG LUỒNG tự động trên dataset tiếng Anh — đo độ "mature".

Các mức (mỗi mức bọc try/except, in rõ thay vì crash):
  E0  dataset sẵn sàng        — tải N case LibriSpeech (audio + transcript)
  E1  STT model load          — faster-whisper, báo device
  E2  STT accuracy (lõi)      — chạy thẳng từng case, đo WER + RTF  ← SỐ MATURE
  E3  qua pipeline Pipecat    — đẩy audio→text qua orchestration (thông luồng thật)

LLM/TTS hiện là MOCK (chưa có model serving) → scorecard ghi rõ "chưa thật".

Chạy:  uv run python experiments/02_e2e_flow_test/run_e2e.py
"""

from __future__ import annotations

import asyncio
import re
import sys
import time
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC = REPO_ROOT / "src"
if SRC.exists() and str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
sys.path.insert(0, str(Path(__file__).resolve().parent))  # để import dataset.py

RESULTS_DIR = Path(__file__).resolve().parent / "results"
N_CASES = 10
_lines: list[str] = []


def out(msg: str = "") -> None:
    print(msg)
    _lines.append(msg)


def _norm(s: str) -> str:
    """Chuẩn hoá để so WER: chữ thường, bỏ dấu câu, gộp khoảng trắng."""
    s = s.lower()
    s = re.sub(r"[^\w\s]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def main() -> int:
    out(f"# fci_voice — E2E flow test @ {datetime.now().isoformat(timespec='seconds')}")
    out("")

    # ---------------- E0 dataset ----------------
    out("=" * 64)
    out("E0 — DATASET")
    out("=" * 64)
    cases = None
    try:
        from dataset import load_cases

        cases = load_cases(N_CASES)
        total_dur = sum(c.duration_s for c in cases)
        out(f"✅ tải {len(cases)} case, tổng {total_dur:.1f}s audio (LibriSpeech dummy, 16kHz)")
    except Exception as e:  # noqa: BLE001
        out(f"❌ FAIL — {type(e).__name__}: {e}")
        out("   (kiểm tra: datasets cài chưa? egress HF có thông? decode flac/soundfile?)")

    # ---------------- E1 STT load ----------------
    out("")
    out("=" * 64)
    out("E1 — STT MODEL LOAD (faster-whisper)")
    out("=" * 64)
    stt = None
    try:
        from fci_voice.stt.faster_whisper_stt import FasterWhisperSTT

        stt = FasterWhisperSTT(model_size="base.en", device="cpu", compute_type="int8")
        t0 = time.perf_counter()
        stt.load()
        out(f"✅ load model base.en (cpu/int8) trong {time.perf_counter() - t0:.1f}s")
    except Exception as e:  # noqa: BLE001
        out(f"❌ FAIL — {type(e).__name__}: {e}")

    # ---------------- E2 STT accuracy ----------------
    out("")
    out("=" * 64)
    out("E2 — STT ACCURACY (chạy thẳng, đo WER + RTF)  ← SỐ MATURE")
    out("=" * 64)
    wer_corpus = None
    if cases and stt:
        refs, hyps, stt_time, audio_time = [], [], 0.0, 0.0
        for c in cases:
            try:
                r = stt.transcribe(c.audio, c.sample_rate)
                refs.append(_norm(c.ref))
                hyps.append(_norm(r.text))
                stt_time += r.latency_s
                audio_time += c.duration_s
                out(f"  [{c.id}] ref: {c.ref[:48]!r}")
                out(f"  {' ' * (len(c.id) + 4)}hyp: {r.text[:48]!r}")
            except Exception as e:  # noqa: BLE001
                out(f"  [{c.id}] ❌ {type(e).__name__}: {e}")
        try:
            import jiwer

            wer_corpus = jiwer.wer(refs, hyps)
            rtf = stt_time / audio_time if audio_time else float("nan")
            out("")
            out(f"📊 WER corpus = {wer_corpus * 100:.2f}%  ({len(refs)} câu)")
            out(f"📊 RTF       = {rtf:.3f}  (xử lý {stt_time:.1f}s / audio {audio_time:.1f}s, CPU)")
        except Exception as e:  # noqa: BLE001
            out(f"⚠️ không tính được WER — {type(e).__name__}: {e}")
    else:
        out("⏭️ bỏ qua (thiếu dataset hoặc STT)")

    # ---------------- E3 qua pipeline Pipecat ----------------
    out("")
    out("=" * 64)
    out("E3 — THÔNG LUỒNG QUA PIPELINE PIPECAT (audio → STT processor → text)")
    out("=" * 64)
    e3_ok = False
    if cases and stt:
        try:
            e3_text = asyncio.run(_run_pipeline_once(cases[0], stt))
            out(f"text ra khỏi pipeline: {e3_text!r}")
            e3_ok = bool(e3_text and e3_text.strip())
            out("orchestration tải audio→text: " + ("✅ PASS" if e3_ok else "⚠️ rỗng"))
        except Exception as e:  # noqa: BLE001
            out(f"❌ FAIL — {type(e).__name__}: {e}")
            out("   (lỗi hé lộ API frame audio thật của pipecat 1.4 → khớp lại processor)")
    else:
        out("⏭️ bỏ qua (thiếu dataset hoặc STT)")

    # ---------------- Scorecard ----------------
    out("")
    out("=" * 64)
    out("SCORECARD — ĐỘ MATURE HỆ THỐNG")
    out("=" * 64)
    out(f"  VAD / turn (base pipecat)   : ✅ có sẵn (exp01)")
    out(f"  STT (faster-whisper EN)     : {'✅ thật, WER %.2f%%' % (wer_corpus * 100) if wer_corpus is not None else '❌/—'}")
    out(f"  Orchestration (Pipecat)     : {'✅ audio chảy qua' if e3_ok else '❌/—'}")
    out(f"  LLM                         : ⬜ MOCK (chưa có serving)")
    out(f"  TTS                         : ⬜ MOCK (chưa có model)")
    out(f"  Tiếng Việt / 8kHz telephony : ⬜ chưa (mới English 16kHz)")

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    report = RESULTS_DIR / f"e2e_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    report.write_text("\n".join(_lines) + "\n", encoding="utf-8")
    out("")
    out(f"📄 Báo cáo lưu: {report}")
    return 0


async def _run_pipeline_once(case, stt) -> str:
    """Đẩy 1 case audio qua pipeline Pipecat bằng processor STT tự viết.

    Dùng InputAudioRawFrame (audio thật) + TextFrame (output) — tránh phụ thuộc
    internals của WhisperSTTService, chỉ test đúng phần ORCHESTRATION mang frame.
    """
    import numpy as np
    from pipecat.frames.frames import EndFrame, Frame, InputAudioRawFrame, TextFrame
    from pipecat.pipeline.pipeline import Pipeline
    from pipecat.pipeline.runner import PipelineRunner
    from pipecat.pipeline.task import PipelineTask
    from pipecat.processors.frame_processor import FrameDirection, FrameProcessor

    from fci_voice.pipeline.mock import CollectProcessor

    class WhisperFrameProcessor(FrameProcessor):
        def __init__(self, stt_) -> None:
            super().__init__()
            self._stt = stt_
            self._buf = bytearray()

        async def process_frame(self, frame: Frame, direction: FrameDirection) -> None:
            await super().process_frame(frame, direction)
            if isinstance(frame, InputAudioRawFrame):
                self._buf.extend(frame.audio)  # gom audio, không đẩy raw xuống
                return
            if isinstance(frame, EndFrame):
                audio = np.frombuffer(bytes(self._buf), dtype=np.int16).astype(np.float32) / 32768.0
                res = self._stt.transcribe(audio, 16000)
                await self.push_frame(TextFrame(res.text), direction)
                await self.push_frame(frame, direction)
                return
            await self.push_frame(frame, direction)

    pcm = (np.clip(case.audio, -1, 1) * 32767).astype(np.int16).tobytes()
    wproc = WhisperFrameProcessor(stt)
    collect = CollectProcessor()
    task = PipelineTask(Pipeline([wproc, collect]))
    await task.queue_frames(
        [InputAudioRawFrame(audio=pcm, sample_rate=16000, num_channels=1), EndFrame()]
    )
    await PipelineRunner(handle_sigint=False).run(task)
    return " ".join(collect.seen)


if __name__ == "__main__":
    raise SystemExit(main())
