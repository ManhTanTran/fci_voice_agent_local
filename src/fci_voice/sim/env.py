"""Gym-env — môi trường giả lập text mode, lộ ra reset()/step() chuẩn hóa.

Sở hữu của Vai 3 (Solution-dev): giữ scenario + sim-user + world-state + scorer.
Không biết nội tại policy — chỉ gửi Observation, nhận Action (xem 02_gym_env_and_roles §4.2).
"""

from __future__ import annotations

import json

from .scorer import ToolCallScorer
from .sim_user import AgendaSimUser
from .types import Action, EpisodeResult, Observation, Scenario, TurnSignal


class GymEnv:
    def __init__(
        self,
        scenario: Scenario,
        sim_user: AgendaSimUser | None = None,
        scorer: ToolCallScorer | None = None,
    ) -> None:
        self.scenario = scenario
        self.sim_user = sim_user or AgendaSimUser(scenario)
        self.scorer = scorer or ToolCallScorer()
        self._idx = 0
        self._history: list[dict] = []
        self._executed: list[str] = []
        self._signals: list[TurnSignal] = []
        self._total_latency = 0.0

    # --- khởi tạo: nạp trạng thái, trả quan sát đầu tiên ---
    def reset(self) -> Observation:
        self._idx = 0
        self._history = []
        self._executed = []
        self._signals = []
        self._total_latency = 0.0
        return self._build_obs()

    def _build_obs(self) -> Observation:
        latest = self.sim_user.utterance(self._idx, self._history)
        return Observation(
            turn_index=self._idx,
            latest_user=latest,
            history=list(self._history),
            tools=self.scenario.tools,
        )

    # --- 1 lượt: chấm -> cập nhật world -> sinh lượt mới -> kiểm tra dừng ---
    def step(self, action: Action) -> tuple[Observation | None, TurnSignal, bool]:
        turn = self.sim_user.turn(self._idx)

        # Bước 1 — chấm điểm action so với nhãn chuẩn lượt hiện tại.
        signal = self.scorer.score(turn, action)
        signal.turn_index = self._idx
        self._signals.append(signal)
        self._total_latency += action.latency_s

        # Bước 2 — cập nhật world: ghi nhận tool đã thực thi.
        if action.tool_call is not None:
            self._executed.append(action.tool_call.name)

        # Lưu lịch sử hội thoại để lượt sau bot có ngữ cảnh.
        # Lượt có tool: ghi đúng JSON như format bot ĐƯỢC YÊU CẦU sinh ra,
        # tránh dạy model nhái một format lạ (bug history cũ -> model copy '[tool:...]').
        self._history.append({"role": "user", "content": turn.user})
        if action.tool_call is not None:
            bot_say = json.dumps(
                {"tool": action.tool_call.name, "args": action.tool_call.args}
            )
        else:
            bot_say = action.text
        self._history.append({"role": "assistant", "content": bot_say})

        # Bước 3 — sang lượt kế.
        self._idx += 1

        # Bước 4 — kiểm tra kết thúc episode.
        done = self._idx >= self.sim_user.num_turns()
        obs = None if done else self._build_obs()
        return obs, signal, done

    def result(self) -> EpisodeResult:
        # Mục tiêu coi là đạt khi mọi required_tool đều đã được gọi (đúng tên).
        goal = all(t in self._executed for t in self.scenario.required_tools)
        return EpisodeResult(
            scenario_id=self.scenario.id,
            signals=list(self._signals),
            executed_tools=list(self._executed),
            goal_success=goal,
            total_latency_s=self._total_latency,
        )
