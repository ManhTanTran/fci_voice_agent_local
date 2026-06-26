#!/usr/bin/env python3
"""Full loop TIẾNG ANH hết lượt + đo latency TỪNG STEP + TTS Piper thật.

Vòng: audio (English) → STT → LLM → TTS → WAV (tiếng thật).
Đo riêng latency mỗi chặng; chạy N case lấy trung bình; xác nhận cả qua Pipecat.

Chạy:  uv run python experiments/04_english_e2e_latency/run_e2e_en.py
"""

from __future__ import annotations

import statistics
import sys
import time
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
for p in (REPO_ROOT / "src", REPO_ROOT / "experiments" / "02_e2e_flow_test"):
    if p.exists() and str(p) not in sys.path:
        sys.path.insert(0, str(p))

RESULTS_DIR = Path(__file__).resolve().parent / "results"
N_CASES = 3
MAX_NEW_TOKENS = 64  # chặn để latency LLM bị giới hạn, so sánh được
_lines: list[str] = []

PIPER_REPO = "rhasspy/piper-voices"
PIPER_ONNX = "en/en_US/lessac/medium/en_US-lessac-medium.onnx"
SYS_PROMPT = "You are a concise, helpful phone assistant. Reply in one short sentence."


def out(msg: str = "") -> None:
    print(msg)
    _lines.append(msg)


def ensure_voice() -> str:
    """Tải voice Piper English thật (nếu chưa cache). Trả về path .onnx."""
    from huggingface_hub import hf_hub_download

    onnx = hf_hub_download(PIPER_REPO, PIPER_ONNX)
    hf_hub_download(PIPER_REPO, PIPER_ONNX + ".json")  # config cạnh .onnx
    return onnx


def main() -> int:
    out(f"# fci_voice — English full loop + latency @ {datetime.now().isoformat(timespec='seconds')}")
    out("")
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    # ---- nạp 3 thành phần ----
    out("=" * 70)
    out("NẠP THÀNH PHẦN")
    out("=" * 70)
    from dataset import load_cases

    from fci_voice.agent.llm import TransformersLLM
    from fci_voice.stt.faster_whisper_stt import FasterWhisperSTT
    from fci_voice.tts.piper_tts import PiperTTS, placeholder_wav

    cases = load_cases(N_CASES)
    out(f"  dataset: {len(cases)} case English (LibriSpeech, 16kHz)")

    t = time.perf_counter()
    stt = FasterWhisperSTT(model_size="base.en").load()
    out(f"  STT  faster-whisper base.en (cpu/int8)  — load {time.perf_counter() - t:.1f}s")

    t = time.perf_counter()
    llm = TransformersLLM(model_name="Qwen/Qwen2.5-1.5B-Instruct").load()
    out(f"  LLM  Qwen2.5-1.5B-Instruct ({llm.device_str}) — load {time.perf_counter() - t:.1f}s")

    tts = None
    tts_kind = "placeholder"
    try:
        t = time.perf_counter()
        voice = ensure_voice()
        tts = PiperTTS(voice).load()
        tts_kind = "piper"
        out(f"  TTS  Piper en_US-lessac-medium          — load {time.perf_counter() - t:.1f}s")
    except Exception as e:  # noqa: BLE001
        out(f"  TTS  ⚠️ Piper KHÔNG dùng được ({type(e).__name__}: {e}) → fallback placeholder")

    # warmup LLM (loại nhiễu lần đầu khỏi số latency)
    llm.chat([{"role": "user", "content": "hi"}], max_new_tokens=8)

    # ---- chạy N case, đo latency từng step ----
    out("")
    out("=" * 70)
    out("FULL LOOP TỪNG CASE (latency mỗi step, ms)")
    out("=" * 70)
    out(f"  {'case':<20}{'audio(s)':>9}{'STT':>8}{'LLM':>8}{'TTS':>8}{'tổng':>8}")
    out("  " + "-" * 66)
    agg = {"stt": [], "llm": [], "tts": [], "total": []}
    for i, c in enumerate(cases):
        r_stt = stt.transcribe(c.audio, c.sample_rate)
        r_llm = llm.chat(
            [{"role": "system", "content": SYS_PROMPT}, {"role": "user", "content": r_stt.text}],
            max_new_tokens=MAX_NEW_TOKENS,
        )
        wav = str(RESULTS_DIR / f"reply_{i}.wav")
        t = time.perf_counter()
        if tts is not None:
            try:
                tts.synthesize(r_llm.text, wav)
            except Exception as e:  # noqa: BLE001
                out(f"    (TTS case {i} lỗi: {type(e).__name__}: {e} → placeholder)")
                placeholder_wav(r_llm.text, wav)
                tts_kind = "placeholder"
        else:
            placeholder_wav(r_llm.text, wav)
        tts_s = time.perf_counter() - t

        total = r_stt.latency_s + r_llm.latency_s + tts_s
        agg["stt"].append(r_stt.latency_s * 1000)
        agg["llm"].append(r_llm.latency_s * 1000)
        agg["tts"].append(tts_s * 1000)
        agg["total"].append(total * 1000)
        out(
            f"  {c.id:<20}{c.duration_s:>9.1f}{r_stt.latency_s * 1000:>8.0f}"
            f"{r_llm.latency_s * 1000:>8.0f}{tts_s * 1000:>8.0f}{total * 1000:>8.0f}"
        )

    out("  " + "-" * 66)
    out(
        f"  {'TRUNG BÌNH':<20}{'':>9}{statistics.mean(agg['stt']):>8.0f}"
        f"{statistics.mean(agg['llm']):>8.0f}{statistics.mean(agg['tts']):>8.0f}"
        f"{statistics.mean(agg['total']):>8.0f}"
    )

    # ví dụ 1 lượt cụ thể
    out("")
    out("VÍ DỤ 1 LƯỢT:")
    ex = cases[0]
    r1 = stt.transcribe(ex.audio, ex.sample_rate)
    r2 = llm.chat(
        [{"role": "system", "content": SYS_PROMPT}, {"role": "user", "content": r1.text}],
        max_new_tokens=MAX_NEW_TOKENS,
    )
    out(f"  🎧 audio  → STT: {r1.text!r}")
    out(f"  🤖 LLM    → {r2.text!r}")
    out(f"  🔊 TTS    → results/reply_0.wav (loại={tts_kind})")

    # ---- xác nhận qua Pipecat ----
    out("")
    out("=" * 70)
    out("QUA PIPELINE PIPECAT (xác nhận orchestration)")
    out("=" * 70)
    import asyncio

    try:
        text, t_chain = asyncio.run(_run_chain(cases[0], stt, llm))
        out(f"  reply ra cuối pipeline: {text!r}")
        out(f"  ✅ thông luồng qua orchestration — tổng {t_chain * 1000:.0f}ms")
    except Exception as e:  # noqa: BLE001
        out(f"  ❌ {type(e).__name__}: {e}")

    # ---- scorecard ----
    out("")
    out("=" * 70)
    out("SCORECARD — FULL LOOP ENGLISH")
    out("=" * 70)
    out(f"  STT (faster-whisper base.en, CPU)  : ✅ ~{statistics.mean(agg['stt']):.0f}ms")
    out(f"  LLM (Qwen2.5-1.5B, GPU GB10)       : ✅ ~{statistics.mean(agg['llm']):.0f}ms / {MAX_NEW_TOKENS} tok")
    out(f"  TTS ({'Piper thật' if tts_kind == 'piper' else 'placeholder'})".ljust(37) + f": {'✅' if tts_kind == 'piper' else '⚠️'} ~{statistics.mean(agg['tts']):.0f}ms")
    out(f"  Full loop end-to-end (trung bình)  : ✅ ~{statistics.mean(agg['total']):.0f}ms")

    report = RESULTS_DIR / f"en_loop_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    report.write_text("\n".join(_lines) + "\n", encoding="utf-8")
    out("")
    out(f"📄 Báo cáo lưu: {report}")
    return 0


async def _run_chain(case, stt, llm):
    """audio → STT proc → LLM proc → collect, qua Pipecat. Trả (reply, tổng_giây)."""
    import numpy as np
    from pipecat.frames.frames import EndFrame, Frame, InputAudioRawFrame, TextFrame
    from pipecat.pipeline.pipeline import Pipeline
    from pipecat.pipeline.runner import PipelineRunner
    from pipecat.pipeline.task import PipelineTask
    from pipecat.processors.frame_processor import FrameDirection, FrameProcessor

    from fci_voice.pipeline.mock import CollectProcessor

    class STTProc(FrameProcessor):
        def __init__(self, s):
            super().__init__()
            self._s = s
            self._buf = bytearray()

        async def process_frame(self, frame: Frame, direction: FrameDirection) -> None:
            await super().process_frame(frame, direction)
            if isinstance(frame, InputAudioRawFrame):
                self._buf.extend(frame.audio)
                return
            if isinstance(frame, EndFrame):
                a = np.frombuffer(bytes(self._buf), dtype=np.int16).astype(np.float32) / 32768.0
                await self.push_frame(TextFrame(self._s.transcribe(a, 16000).text), direction)
                await self.push_frame(frame, direction)
                return
            await self.push_frame(frame, direction)

    class LLMProc(FrameProcessor):
        def __init__(self, m):
            super().__init__()
            self._m = m

        async def process_frame(self, frame: Frame, direction: FrameDirection) -> None:
            await super().process_frame(frame, direction)
            if isinstance(frame, TextFrame):
                rep = self._m.chat(
                    [{"role": "system", "content": SYS_PROMPT}, {"role": "user", "content": frame.text}],
                    max_new_tokens=MAX_NEW_TOKENS,
                )
                await self.push_frame(TextFrame(rep.text), direction)
            else:
                await self.push_frame(frame, direction)

    pcm = (np.clip(case.audio, -1, 1) * 32767).astype(np.int16).tobytes()
    collect = CollectProcessor()
    task = PipelineTask(Pipeline([STTProc(stt), LLMProc(llm), collect]))
    t0 = time.perf_counter()
    await task.queue_frames(
        [InputAudioRawFrame(audio=pcm, sample_rate=16000, num_channels=1), EndFrame()]
    )
    await PipelineRunner(handle_sigint=False).run(task)
    return (collect.seen[-1] if collect.seen else ""), time.perf_counter() - t0


if __name__ == "__main__":
    raise SystemExit(main())
