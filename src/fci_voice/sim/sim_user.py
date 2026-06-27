"""Sim-user — cấu phần BÊN TRONG gym-env sinh lượt thoại kế tiếp của người dùng.

Bản đầu (v1) chạy AGENDA-BASED: trả thẳng câu kịch bản đã viết sẵn, deterministic,
rẻ, dễ kiểm chứng. Đây là chủ ý để THÔNG LUỒNG vòng lặp env trước.

TECH-DEBT (v2): bọc thêm LLM diễn đạt lại bề mặt câu thoại (giữ nguyên agenda/nhãn)
để tăng độ đa dạng ngôn ngữ — xem docs/11_sim_test_system/01_design.md §6 (sim-to-real).
"""

from __future__ import annotations

from .types import Scenario, ScenarioTurn


class AgendaSimUser:
    """Phát lần lượt từng câu trong agenda của scenario, không phụ thuộc history."""

    def __init__(self, scenario: Scenario) -> None:
        self._agenda = scenario.agenda

    def num_turns(self) -> int:
        return len(self._agenda)

    def turn(self, index: int) -> ScenarioTurn:
        return self._agenda[index]

    def utterance(self, index: int, history: list[dict]) -> str:
        # history nhận vào để v2 (LLM) dùng làm ngữ cảnh; v1 bỏ qua.
        return self._agenda[index].user
