"""Ráp pipeline. Giai đoạn smoke: chỉ một pipeline text tối thiểu.

Về sau `build_voice_pipeline(services)` sẽ ghép STT→turn→agent→guardrail→TTS
từ các adapter thật. Hiện chừa chữ ký để mở rộng, chưa hiện thực.
"""

from __future__ import annotations

from pipecat.frames.frames import EndFrame, TextFrame
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineTask

from .mock import CollectProcessor, UpperProcessor


async def run_text_smoke(text: str = "xin chào DGX") -> list[str]:
    """Chạy một pipeline text tối thiểu, trả về list text đã đi qua.

    Chứng minh engine Pipecat khởi tạo + chảy frame + kết thúc sạch trên máy hiện tại.
    """
    upper = UpperProcessor()
    collect = CollectProcessor()

    pipeline = Pipeline([upper, collect])
    task = PipelineTask(pipeline)
    await task.queue_frames([TextFrame(text), EndFrame()])

    # handle_sigint=False: an toàn khi chạy trong script/headless (không cướp SIGINT)
    runner = PipelineRunner(handle_sigint=False)
    await runner.run(task)

    return collect.seen
