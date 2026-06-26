"""Processor giả lập — để THÔNG LUỒNG trước khi có model thật.

Mục đích: chứng minh engine Pipecat chạy được trên máy (đặc biệt arm64/GB10)
bằng một pipeline text tối thiểu, không phụ thuộc model/transport/cloud nào.
Khi có model thật, các processor này được thay bằng STTService/LLMService/...
"""

from __future__ import annotations

from pipecat.frames.frames import Frame, TextFrame
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor


class UpperProcessor(FrameProcessor):
    """Biến đổi văn bản (in hoa) — đại diện cho một mắt xích xử lý."""

    async def process_frame(self, frame: Frame, direction: FrameDirection) -> None:
        await super().process_frame(frame, direction)
        if isinstance(frame, TextFrame):
            await self.push_frame(TextFrame(frame.text.upper()), direction)
        else:
            # frame điều khiển (Start/End/...) phải đẩy tiếp để pipeline kết thúc đúng
            await self.push_frame(frame, direction)


class CollectProcessor(FrameProcessor):
    """Thu lại text đi qua — để test xác nhận luồng chảy đủ chặng."""

    def __init__(self) -> None:
        super().__init__()
        self.seen: list[str] = []

    async def process_frame(self, frame: Frame, direction: FrameDirection) -> None:
        await super().process_frame(frame, direction)
        if isinstance(frame, TextFrame):
            self.seen.append(frame.text)
        await self.push_frame(frame, direction)
