"""Kiểu dữ liệu lõi cho hệ gym-env (text mode / tool-calling trước).

Tách riêng types để mọi cấu phần (env, scorer, policy, sim-user) cùng nói chung
một "ngôn ngữ" — env không phụ thuộc nội tại của policy (xem 02_gym_env_and_roles).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ToolSpec:
    """Đặc tả 1 công cụ nghiệp vụ mà bot ĐƯỢC PHÉP gọi trong scenario.

    `schema` (tùy chọn) mang ràng buộc từng tham số để (1) dựng grammar cho
    structured decoding, (2) tạo case khó bẻ gãy free-form JSON:
      schema = {param: {"type": "string|number", "enum": [...], "pattern": "regex"}}
    """

    name: str
    description: str
    params: list[str] = field(default_factory=list)
    schema: dict = field(default_factory=dict)


@dataclass
class ScenarioTurn:
    """1 lượt trong agenda của sim-user: câu người dùng + nhãn chuẩn kỳ vọng."""

    user: str
    expected_tool: Optional[str]  # None = lượt này KHÔNG kỳ vọng gọi tool nào
    expected_args: dict = field(default_factory=dict)
    note: str = ""


@dataclass
class Scenario:
    """Tài sản của Vai 1 (Khách hàng): nghiệp vụ + persona + mục tiêu + agenda."""

    id: str
    domain: str
    persona: str
    goal: str
    language: str
    tools: list[ToolSpec]
    agenda: list[ScenarioTurn]
    # Tool bắt buộc phải được gọi đúng để coi là hoàn thành mục tiêu cuộc gọi.
    required_tools: list[str] = field(default_factory=list)


@dataclass
class ToolCall:
    name: str
    args: dict = field(default_factory=dict)


@dataclass
class Observation:
    """Thứ bot NHÌN THẤY tại 1 lượt — env chỉ đưa quan sát, không lộ nhãn chuẩn."""

    turn_index: int
    latest_user: str
    history: list[dict]  # [{"role","content"}] các lượt trước
    tools: list[ToolSpec]


@dataclass
class Action:
    """Phản hồi của bot: câu thoại + (tùy chọn) 1 lời gọi hàm nghiệp vụ."""

    text: str = ""
    tool_call: Optional[ToolCall] = None
    latency_s: float = 0.0


@dataclass
class TurnSignal:
    """Điểm 3 tầng cho 1 lượt (xem docs/06_llm_agent/03_tool_calling_stages)."""

    turn_index: int
    t1_decision_ok: bool  # quyết-định-gọi-hay-không có khớp kỳ vọng không
    t2_tool_ok: Optional[bool]  # đúng tên tool (chỉ tính khi cả 2 bên đều gọi)
    t3_args_ok: Optional[bool]  # đúng tham số (chỉ tính khi T2 đúng)
    expected_tool: Optional[str]
    got_tool: Optional[str]
    detail: str = ""

    @property
    def turn_pass(self) -> bool:
        # Lượt PASS = quyết định đúng VÀ (nếu cần gọi) đúng tool + đúng args.
        if not self.t1_decision_ok:
            return False
        if self.expected_tool is None:
            return True
        return bool(self.t2_tool_ok) and bool(self.t3_args_ok)


@dataclass
class EpisodeResult:
    scenario_id: str
    signals: list[TurnSignal]
    executed_tools: list[str]
    goal_success: bool
    total_latency_s: float = 0.0

    def tier_rates(self) -> dict:
        """Tỷ lệ đúng từng tầng, tính trên mẫu hợp lệ của tầng đó."""
        t1 = [s.t1_decision_ok for s in self.signals]
        t2 = [s.t2_tool_ok for s in self.signals if s.t2_tool_ok is not None]
        t3 = [s.t3_args_ok for s in self.signals if s.t3_args_ok is not None]
        rate = lambda xs: (sum(1 for x in xs if x) / len(xs)) if xs else None
        return {
            "T1_decision": rate(t1),
            "T2_tool": rate(t2),
            "T3_args": rate(t3),
            "turn_pass": rate([s.turn_pass for s in self.signals]),
        }
