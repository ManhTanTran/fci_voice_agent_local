"""Hệ gym-env giả lập hội thoại (text mode trước) — xem docs/11_sim_test_system.

Lát mỏng bước đầu: Scenario -> GymEnv(reset/step) -> BotPolicy.act -> Scorer 3 tầng.
"""

from __future__ import annotations

from .env import GymEnv
from .policy import BotPolicy, LLMPolicy, RuleBasedPolicy
from .scenario import load_scenario
from .structured import XGrammarToolPolicy, build_tool_json_schema
from .scorer import ToolCallScorer
from .sim_user import AgendaSimUser
from .types import (
    Action,
    EpisodeResult,
    Observation,
    Scenario,
    ScenarioTurn,
    ToolCall,
    ToolSpec,
    TurnSignal,
)

__all__ = [
    "GymEnv",
    "BotPolicy",
    "LLMPolicy",
    "RuleBasedPolicy",
    "XGrammarToolPolicy",
    "build_tool_json_schema",
    "load_scenario",
    "ToolCallScorer",
    "AgendaSimUser",
    "Action",
    "EpisodeResult",
    "Observation",
    "Scenario",
    "ScenarioTurn",
    "ToolCall",
    "ToolSpec",
    "TurnSignal",
]
