"""Kiểu dữ liệu lõi cho module Phát hiện lượt thoại (turn-detection).

Song sinh với `types.py` (tool-calling) nhưng đo một bài toán khác: khi bot ĐANG
NÓI, có sự kiện thoại của người dùng/ngoại cảnh chen vào — hệ phải quyết định
NGẮT LỜI (INTERRUPT, nhường lượt) hay GIỮ LỜI (HOLD, nói tiếp). Xem thiết kế gốc
docs/11_sim_test_system/01_design.md §3-4.

Giai đoạn này chạy TEXT/EVENT-first: sự kiện thoại là (text ASR + mốc thời gian +
người nói), CHƯA render audio. Bộ quyết định chỉ được nhìn các đặc trưng quan sát
được; nhãn `tag`/`expected` là metadata ground-truth để chấm + phân tích, KHÔNG
phải đầu vào (tránh chấm điểm vòng tròn).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

# Hai nhãn quyết định lượt thoại. INTERRUPT là lớp "dương" (hành vi rủi ro: nhường
# lượt) — sai ở đây tốn kém nhất nên đặt làm trục của ma trận nhầm lẫn.
INTERRUPT = "INTERRUPT"
HOLD = "HOLD"

# Người nói trong một sự kiện thoại. Energy-VAD KHÔNG phân biệt được 3 loại này
# (đều là năng lượng âm thanh) → đó chính là nguồn lỗi FP ta muốn đo.
SPK_USER = "user"  # người dùng mục tiêu (đầu dây chính)
SPK_OTHER = "other"  # người bên cạnh / cross-talk (không phải khách mục tiêu)
SPK_NOISE = "noise"  # nhạc / TV / karaoke — ASR có thể nhận nhầm thành lời


@dataclass
class SpeechEvent:
    """1 sự kiện thoại trên trục thời gian, tính từ lúc bot BẮT ĐẦU nói câu hiện tại.

    `tag` là nhãn hành vi ground-truth (backchannel / stop_keyword / side_talk ...)
    DÙNG ĐỂ PHÂN TÍCH, không đưa vào decider.
    """

    speaker: str
    text: str
    t_start_s: float  # mốc bắt đầu nói, giây, so với onset câu bot
    duration_s: float = 0.0
    tag: str = ""


@dataclass
class TurnScenario:
    """Tài sản Vai 1 (Khách hàng) cho bài toán turn-detection.

    `agent_utterance` = câu bot đang nói (agent_context). `events` = luồng sự kiện
    chen vào. `expected` = nhãn đúng cuối cùng. `latency_budget_ms` = ngưỡng tốc độ
    (điểm đau yêu cầu ngắt lời ≤150ms).
    """

    id: str
    category: str  # N1..N6 / noisy_* — nhóm taxonomy
    environment: str  # "quiet" | "noisy"
    agent_utterance: str
    events: list[SpeechEvent]
    expected: str  # INTERRUPT | HOLD
    snr_db: Optional[float] = None  # chỉ môi trường ồn
    latency_budget_ms: int = 150
    note: str = ""


@dataclass
class TurnDecision:
    """Đầu ra của decider: quyết định + thời điểm ra quyết định để đo độ trễ."""

    action: str  # INTERRUPT | HOLD
    # Mốc (ms, so với onset câu bot) decider chốt quyết định INTERRUPT. None nếu HOLD.
    decided_at_ms: Optional[float] = None


@dataclass
class TurnVerdict:
    """Chấm 1 scenario: nhãn đúng/sai + (nếu INTERRUPT đúng) có kịp ngân sách trễ."""

    scenario_id: str
    category: str
    environment: str
    expected: str
    got: str
    correct: bool
    # Độ trễ ngắt lời (ms) so với onset sự kiện kích hoạt — chỉ có nghĩa khi là TP.
    latency_ms: Optional[float] = None
    within_budget: Optional[bool] = None
    detail: str = ""

    @property
    def confusion_cell(self) -> str:
        """Ô ma trận nhầm lẫn với lớp dương = INTERRUPT."""
        if self.expected == INTERRUPT:
            return "TP" if self.got == INTERRUPT else "FN"
        return "FP" if self.got == INTERRUPT else "TN"
