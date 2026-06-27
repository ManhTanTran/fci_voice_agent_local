"""Chấm điểm turn-detection: ma trận nhầm lẫn INTERRUPT/HOLD + độ trễ ngắt lời.

Trục đo bám đúng 2 điểm đau của hệ thực tế:
  - Độ chính xác (accuracy) — mục tiêu ≥85% (hiện ~76%).
  - Độ trễ ngắt lời (latency) — mục tiêu ≤150ms (hiện ~280ms), chỉ tính trên TP.

Lớp dương = INTERRUPT:
  - FP (ngắt nhầm): bot đang nói thì nhường lượt do backchannel/side-talk/nhiễu →
    cắt lời khách vô cớ, trải nghiệm tệ.
  - FN (sót ngắt): khách thật sự muốn ngắt mà bot nói tiếp → khách bực, nói đè.
"""

from __future__ import annotations

from .turn_types import INTERRUPT, SpeechEvent, TurnDecision, TurnScenario, TurnVerdict


def _trigger_onset_ms(scn: TurnScenario) -> float:
    """Mốc onset (ms) của sự kiện ĐÁNG LẼ kích hoạt ngắt — sự kiện user đầu tiên.

    Dùng làm gốc đo độ trễ: ngắt lời nhanh = chốt INTERRUPT sớm sau khi khách bắt
    đầu nói. Nếu không có sự kiện user (ca toàn nhiễu) thì lấy sự kiện đầu tiên.
    """
    users = [e for e in scn.events if e.speaker == "user"]
    pool = users if users else scn.events
    return min((e.t_start_s for e in pool), default=0.0) * 1000.0


def score_turn(scn: TurnScenario, dec: TurnDecision) -> TurnVerdict:
    correct = dec.action == scn.expected
    latency_ms = None
    within_budget = None

    # Độ trễ chỉ có nghĩa khi NGẮT ĐÚNG (TP): đo từ lúc khách bắt đầu nói tới lúc chốt.
    if scn.expected == INTERRUPT and dec.action == INTERRUPT and dec.decided_at_ms is not None:
        latency_ms = max(0.0, dec.decided_at_ms - _trigger_onset_ms(scn))
        within_budget = latency_ms <= scn.latency_budget_ms

    cell = {
        (True, INTERRUPT): "ngat dung (TP)",
        (False, INTERRUPT): "sot ngat (FN)",
    }
    detail = ""
    if not correct:
        detail = "ngat nham (FP)" if scn.expected != INTERRUPT else "sot ngat (FN)"

    return TurnVerdict(
        scenario_id=scn.id,
        category=scn.category,
        environment=scn.environment,
        expected=scn.expected,
        got=dec.action,
        correct=correct,
        latency_ms=latency_ms,
        within_budget=within_budget,
        detail=detail,
    )


def aggregate(verdicts: list[TurnVerdict]) -> dict:
    """Tổng hợp ma trận nhầm lẫn + accuracy + thống kê độ trễ trên tập TP."""
    cells = {"TP": 0, "FP": 0, "FN": 0, "TN": 0}
    for v in verdicts:
        cells[v.confusion_cell] += 1

    n = len(verdicts)
    acc = sum(1 for v in verdicts if v.correct) / n if n else None

    tp = cells["TP"]
    prec = tp / (tp + cells["FP"]) if (tp + cells["FP"]) else None
    rec = tp / (tp + cells["FN"]) if (tp + cells["FN"]) else None

    lat = [v.latency_ms for v in verdicts if v.latency_ms is not None]
    within = [v.within_budget for v in verdicts if v.within_budget is not None]
    lat_mean = sum(lat) / len(lat) if lat else None
    lat_p95 = sorted(lat)[max(0, round(0.95 * len(lat)) - 1)] if lat else None
    within_rate = sum(1 for w in within if w) / len(within) if within else None

    return {
        "n": n,
        "accuracy": acc,
        "confusion": cells,
        "precision_interrupt": prec,  # cao = ít ngắt nhầm (FP thấp)
        "recall_interrupt": rec,  # cao = ít sót ngắt (FN thấp)
        "latency_ms_mean": lat_mean,
        "latency_ms_p95": lat_p95,
        "within_budget_rate": within_rate,
    }
