#!/usr/bin/env python3
"""Full loop + hội thoại cơ bản — thông luồng HẾT trên DGX.

Các mức (graceful — lỗi in rõ, không crash):
  C0  LLM load                  — Qwen2.5-1.5B-Instruct trên GPU GB10 (torch cu130)
  C1  HỘI THOẠI CƠ BẢN          — mini-dialogue CSKH tiếng Việt 3 lượt (giữ ngữ cảnh)
  C2  FULL LOOP tuần tự         — 1 audio (English) → STT → LLM → TTS → WAV
  C3  FULL CHAIN qua Pipecat    — audio → STT proc → LLM proc → TTS proc (orchestration)

TTS = Piper nếu cài được, không thì WAV placeholder (vòng vẫn khép). Scorecard ghi rõ.

Chạy:  uv run python experiments/03_full_loop_conversation/run_loop.py
"""

from __future__ import annotations

import asyncio
import sys
import time
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
for p in (REPO_ROOT / "src", REPO_ROOT / "experiments" / "02_e2e_flow_test"):
    if p.exists() and str(p) not in sys.path:
        sys.path.insert(0, str(p))

RESULTS_DIR = Path(__file__).resolve().parent / "results"
_lines: list[str] = []


def out(msg: str = "") -> None:
    print(msg)
    _lines.append(msg)


def _synth(text: str, out_wav: str) -> str:
    """Piper nếu được, không thì placeholder. Trả về nhãn loại TTS đã dùng."""
    from fci_voice.tts.piper_tts import placeholder_wav

    try:
        import os

        from fci_voice.tts.piper_tts import PiperTTS

        model = os.getenv("FCI_PIPER_MODEL", "")
        if model and Path(model).exists():
            PiperTTS(model).synthesize(text, out_wav)
            return "piper"
    except Exception:  # noqa: BLE001
        pass
    placeholder_wav(text, out_wav)
    return "placeholder"


def main() -> int:
    out(f"# fci_voice — full loop + hội thoại @ {datetime.now().isoformat(timespec='seconds')}")
    out("")
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    # ---------------- C0 LLM load ----------------
    out("=" * 64)
    out("C0 — LLM LOAD (Qwen2.5-1.5B-Instruct)")
    out("=" * 64)
    llm = None
    try:
        from fci_voice.agent.llm import TransformersLLM

        llm = TransformersLLM(model_name="Qwen/Qwen2.5-1.5B-Instruct")
        t0 = time.perf_counter()
        llm.load()
        out(f"✅ load OK trong {time.perf_counter() - t0:.1f}s — device {llm.device_str}")
    except Exception as e:  # noqa: BLE001
        out(f"❌ FAIL — {type(e).__name__}: {e}")

    # ---------------- C1 hội thoại cơ bản ----------------
    out("")
    out("=" * 64)
    out("C1 — HỘI THOẠI CƠ BẢN (CSKH tiếng Việt, 3 lượt, giữ ngữ cảnh)")
    out("=" * 64)
    c1_ok = False
    if llm:
        try:
            messages = [
                {
                    "role": "system",
                    "content": "Bạn là trợ lý tổng đài CSKH, trả lời NGẮN GỌN, lịch sự, bằng tiếng Việt.",
                }
            ]
            user_turns = [
                "Chào bạn, cửa hàng mình mấy giờ mở cửa?",
                "Thế cuối tuần có mở không?",
                "Ok cảm ơn nhé.",
            ]
            for u in user_turns:
                messages.append({"role": "user", "content": u})
                r = llm.chat(messages, max_new_tokens=80)
                messages.append({"role": "assistant", "content": r.text})
                out(f"  👤 {u}")
                out(f"  🤖 {r.text}   ({r.latency_s:.2f}s)")
            c1_ok = True
        except Exception as e:  # noqa: BLE001
            out(f"❌ FAIL — {type(e).__name__}: {e}")
    else:
        out("⏭️ bỏ qua (thiếu LLM)")

    # ---------------- chuẩn bị STT + 1 audio case ----------------
    stt = None
    case = None
    try:
        from dataset import load_cases

        from fci_voice.stt.faster_whisper_stt import FasterWhisperSTT

        case = load_cases(1)[0]
        stt = FasterWhisperSTT(model_size="base.en").load()
    except Exception as e:  # noqa: BLE001
        out(f"\n(⚠️ chuẩn bị STT/audio lỗi: {type(e).__name__}: {e})")

    # ---------------- C2 full loop tuần tự ----------------
    out("")
    out("=" * 64)
    out("C2 — FULL LOOP TUẦN TỰ (audio → STT → LLM → TTS → WAV)")
    out("=" * 64)
    c2_ok = False
    tts_kind = "—"
    if llm and stt and case:
        try:
            asr = stt.transcribe(case.audio, case.sample_rate)
            out(f"  1) STT  : {asr.text!r}")
            reply = llm.chat(
                [
                    {"role": "system", "content": "You are a concise helpful phone assistant."},
                    {"role": "user", "content": asr.text},
                ],
                max_new_tokens=80,
            )
            out(f"  2) LLM  : {reply.text!r}")
            wav = str(RESULTS_DIR / "loop_reply.wav")
            tts_kind = _synth(reply.text, wav)
            size = Path(wav).stat().st_size
            out(f"  3) TTS  : ghi {wav} ({size} bytes, loại={tts_kind})")
            c2_ok = True
            out("  ✅ vòng khép: audio vào → audio ra")
        except Exception as e:  # noqa: BLE001
            out(f"❌ FAIL — {type(e).__name__}: {e}")
    else:
        out("⏭️ bỏ qua (thiếu LLM/STT/audio)")

    # ---------------- C3 full chain qua Pipecat ----------------
    out("")
    out("=" * 64)
    out("C3 — FULL CHAIN QUA PIPELINE PIPECAT (orchestration)")
    out("=" * 64)
    c3_ok = False
    if llm and stt and case:
        try:
            texts = asyncio.run(_run_chain(case, stt, llm))
            out(f"  text cuối pipeline (LLM reply): {texts!r}")
            c3_ok = bool(texts and texts.strip())
            out("  orchestration STT→LLM→TTS: " + ("✅ PASS" if c3_ok else "⚠️ rỗng"))
        except Exception as e:  # noqa: BLE001
            out(f"❌ FAIL — {type(e).__name__}: {e}")
            out("   (lỗi hé lộ API frame thật pipecat 1.4 → khớp lại processor)")
    else:
        out("⏭️ bỏ qua")

    # ---------------- Scorecard ----------------
    out("")
    out("=" * 64)
    out("SCORECARD — ĐỘ MATURE HỆ THỐNG")
    out("=" * 64)
    out(f"  STT (faster-whisper EN)     : {'✅ thật' if stt else '❌'}")
    out(f"  LLM (Qwen2.5-1.5B, GPU)     : {'✅ thật' if (llm and c1_ok) else '❌'}")
    out(f"  Hội thoại cơ bản đa lượt    : {'✅ giữ ngữ cảnh' if c1_ok else '❌'}")
    out(f"  TTS                         : {'✅ Piper' if tts_kind == 'piper' else ('⚠️ placeholder' if tts_kind == 'placeholder' else '❌')}")
    out(f"  Full loop tuần tự           : {'✅ khép vòng' if c2_ok else '❌'}")
    out(f"  Full chain qua Pipecat      : {'✅ thông luồng' if c3_ok else '❌'}")
    out(f"  Tiếng Việt / 8kHz telephony : ⬜ STT mới English 16kHz (LLM/hội thoại đã vi)")

    report = RESULTS_DIR / f"loop_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    report.write_text("\n".join(_lines) + "\n", encoding="utf-8")
    out("")
    out(f"📄 Báo cáo lưu: {report}")
    return 0


async def _run_chain(case, stt, llm) -> str:
    """audio → [STT proc] → [LLM proc] → [TTS proc] → collect, qua Pipecat."""
    import numpy as np
    from pipecat.frames.frames import EndFrame, Frame, InputAudioRawFrame, TextFrame
    from pipecat.pipeline.pipeline import Pipeline
    from pipecat.pipeline.runner import PipelineRunner
    from pipecat.pipeline.task import PipelineTask
    from pipecat.processors.frame_processor import FrameDirection, FrameProcessor

    from fci_voice.pipeline.mock import CollectProcessor

    class STTProc(FrameProcessor):
        def __init__(self, stt_):
            super().__init__()
            self._stt = stt_
            self._buf = bytearray()

        async def process_frame(self, frame: Frame, direction: FrameDirection) -> None:
            await super().process_frame(frame, direction)
            if isinstance(frame, InputAudioRawFrame):
                self._buf.extend(frame.audio)
                return
            if isinstance(frame, EndFrame):
                audio = np.frombuffer(bytes(self._buf), dtype=np.int16).astype(np.float32) / 32768.0
                await self.push_frame(TextFrame(self._stt.transcribe(audio, 16000).text), direction)
                await self.push_frame(frame, direction)
                return
            await self.push_frame(frame, direction)

    class LLMProc(FrameProcessor):
        def __init__(self, llm_):
            super().__init__()
            self._llm = llm_

        async def process_frame(self, frame: Frame, direction: FrameDirection) -> None:
            await super().process_frame(frame, direction)
            if isinstance(frame, TextFrame):
                reply = self._llm.chat(
                    [
                        {"role": "system", "content": "You are a concise helpful phone assistant."},
                        {"role": "user", "content": frame.text},
                    ],
                    max_new_tokens=80,
                )
                await self.push_frame(TextFrame(reply.text), direction)
            else:
                await self.push_frame(frame, direction)

    class TTSProc(FrameProcessor):
        def __init__(self):
            super().__init__()
            self.wav = str(RESULTS_DIR / "chain_reply.wav")

        async def process_frame(self, frame: Frame, direction: FrameDirection) -> None:
            await super().process_frame(frame, direction)
            if isinstance(frame, TextFrame):
                _synth(frame.text, self.wav)
            await self.push_frame(frame, direction)

    pcm = (np.clip(case.audio, -1, 1) * 32767).astype(np.int16).tobytes()
    collect = CollectProcessor()
    task = PipelineTask(Pipeline([STTProc(stt), LLMProc(llm), TTSProc(), collect]))
    await task.queue_frames(
        [InputAudioRawFrame(audio=pcm, sample_rate=16000, num_channels=1), EndFrame()]
    )
    await PipelineRunner(handle_sigint=False).run(task)
    # text cuối = reply của LLM (TextFrame cuối collector thấy)
    return collect.seen[-1] if collect.seen else ""


if __name__ == "__main__":
    raise SystemExit(main())
