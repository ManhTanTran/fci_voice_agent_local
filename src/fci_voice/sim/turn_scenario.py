"""Nạp TurnScenario từ file JSON (Vai 1 - Khách hàng sở hữu)."""

from __future__ import annotations

import json
from pathlib import Path

from .turn_types import SpeechEvent, TurnScenario


def load_turn_scenario(path: str | Path) -> TurnScenario:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    events = [
        SpeechEvent(
            speaker=e["speaker"],
            text=e.get("text", ""),
            t_start_s=float(e["t_start_s"]),
            duration_s=float(e.get("duration_s", 0.0)),
            tag=e.get("tag", ""),
        )
        for e in data["events"]
    ]
    return TurnScenario(
        id=data["id"],
        category=data["category"],
        environment=data.get("environment", "quiet"),
        agent_utterance=data["agent_utterance"],
        events=events,
        expected=data["expected"],
        snr_db=data.get("snr_db"),
        latency_budget_ms=int(data.get("latency_budget_ms", 150)),
        note=data.get("note", ""),
    )
