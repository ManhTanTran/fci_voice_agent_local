"""Bộ chấm điểm tool-calling 3 tầng (T1/T2/T3) cho text mode.

Tách scorer khỏi env để Vai 3 (Solution-dev) thay đổi tiêu chí chấm mà không
đụng vòng lặp env. Chấm bằng cách đối chiếu Action của bot với nhãn ScenarioTurn.
"""

from __future__ import annotations

from .types import Action, ScenarioTurn, TurnSignal


def _norm(v) -> str:
    """Chuẩn hóa giá trị tham số để so khớp khoan dung (case/space/insensitive)."""
    return str(v).strip().lower()


def _args_match(expected: dict, got: dict) -> bool:
    # Đúng args = MỌI key kỳ vọng đều có mặt và bằng nhau sau chuẩn hóa.
    # Bot được phép thừa key (vd thêm context) — không phạt key thừa ở tầng này.
    for k, v in expected.items():
        if k not in got or _norm(got[k]) != _norm(v):
            return False
    return True


class ToolCallScorer:
    """Chấm 1 lượt theo 3 tầng quyết định -> chọn tool -> trích tham số."""

    def score(self, turn: ScenarioTurn, action: Action) -> TurnSignal:
        expected_call = turn.expected_tool is not None
        got = action.tool_call
        got_call = got is not None
        got_tool = got.name if got else None

        # T1 — quyết định gọi/không-gọi có khớp kỳ vọng không (bắt FN/FP).
        t1 = expected_call == got_call

        t2 = None
        t3 = None
        detail = ""
        if expected_call and got_call:
            # T2 — đúng tên tool.
            t2 = got_tool == turn.expected_tool
            if t2:
                # T3 — đúng tham số (chỉ xét khi đã đúng tool).
                t3 = _args_match(turn.expected_args, got.args)
                if not t3:
                    detail = f"args sai: kỳ vọng={turn.expected_args} nhận={got.args}"
            else:
                detail = f"sai tool: kỳ vọng={turn.expected_tool} nhận={got_tool}"
        elif expected_call and not got_call:
            detail = f"FN: cần gọi {turn.expected_tool} nhưng bot không gọi"
        elif got_call and not expected_call:
            detail = f"FP: không cần tool nhưng bot gọi {got_tool}"

        return TurnSignal(
            turn_index=-1,  # env gán lại đúng index khi step
            t1_decision_ok=t1,
            t2_tool_ok=t2,
            t3_args_ok=t3,
            expected_tool=turn.expected_tool,
            got_tool=got_tool,
            detail=detail,
        )
