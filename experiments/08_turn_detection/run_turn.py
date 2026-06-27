"""Exp 08 — THÔNG LUỒNG turn-detection (text/event mode) — chạy CẢ SUITE.

Mỗi scenario: nạp luồng sự kiện thoại -> decider.decide() -> chấm INTERRUPT/HOLD +
độ trễ -> tổng hợp ma trận nhầm lẫn. So sánh các bậc decider trên CÙNG tập kịch bản
(paired A/B) để thấy năng lực ngữ nghĩa vá được lỗi nào của VAD năng lượng.

Chọn decider qua FCI_DECIDER:
- energy_vad   : VAD theo năng lượng, mù ngữ nghĩa (baseline yếu, LOCAL).
- semantic_rule: lexicon + nhận biết người nói (baseline mạnh, LOCAL).
- llm_semantic : LLM phán đoán ý định — CHẠY TRÊN DGX (cần model).

Lọc: FCI_SCENARIO=q_n2  (khớp theo tên file). Thư mục: FCI_SCEN_DIR.

Chạy:
  python experiments/08_turn_detection/run_turn.py
  FCI_DECIDER=semantic_rule python experiments/08_turn_detection/run_turn.py
  FCI_DECIDER=llm_semantic uv run python experiments/08_turn_detection/run_turn.py   # DGX
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from fci_voice.sim.turn_decider import build_decider  # noqa: E402
from fci_voice.sim.turn_scenario import load_turn_scenario  # noqa: E402
from fci_voice.sim.turn_scorer import aggregate, score_turn  # noqa: E402

SCEN_DIR = Path(os.getenv("FCI_SCEN_DIR", Path(__file__).parent / "scenarios"))


def _scenario_files(d: Path):
    return sorted(f for f in d.rglob("*.json") if not f.stem.startswith("_"))


def main() -> int:
    which = os.getenv("FCI_DECIDER", "energy_vad").lower()
    only = os.getenv("FCI_SCENARIO", "").strip()

    files = _scenario_files(SCEN_DIR)
    if only:
        files = [f for f in files if only in f.stem]
    if not files:
        print(f"!! không thấy scenario nào ({SCEN_DIR}, filter='{only}')")
        return 2

    llm = None
    if which == "llm_semantic":
        from fci_voice.agent.llm import LLM

        print(">> decider=llm_semantic (Qwen1.5B) — nạp model trên DGX...")
        llm = LLM()
        llm.load()
        print(f">> model loaded on {llm.device_str}\n")
    else:
        print(f">> decider={which} (local)\n")

    decider = build_decider(which, llm=llm)

    verdicts = []
    for f in files:
        scn = load_turn_scenario(f)
        dec = decider.decide(scn)
        v = score_turn(scn, dec)
        verdicts.append(v)
        lat = "" if v.latency_ms is None else f" lat={v.latency_ms:.0f}ms"
        budget = "" if v.within_budget is None else (" ✓budget" if v.within_budget else " ✗budget")
        mark = "OK " if v.correct else "ERR"
        print(
            f"  [{mark}] {scn.id:<26} {scn.category:<8} "
            f"exp={v.expected:<9} got={v.got:<9} {v.confusion_cell}{lat}{budget}"
        )

    _print_suite(verdicts, which)
    # exit 0 nếu accuracy đạt ngưỡng đau (≥85%).
    agg = aggregate(verdicts)
    return 0 if (agg["accuracy"] or 0) >= 0.85 else 1


def _print_suite(verdicts, which):
    agg = aggregate(verdicts)
    c = agg["confusion"]
    print("\n" + "=" * 60)
    print(f"SUITE turn-detection | decider={which} | n={agg['n']}")
    print(f"  accuracy        : {_pct(agg['accuracy'])}   (đích ≥85%)")
    print(f"  confusion       : TP={c['TP']} FP={c['FP']} FN={c['FN']} TN={c['TN']}")
    print(f"  precision(INTR) : {_pct(agg['precision_interrupt'])}   (cao = ít ngắt nhầm)")
    print(f"  recall(INTR)    : {_pct(agg['recall_interrupt'])}   (cao = ít sót ngắt)")
    print(
        f"  latency (synth) : mean={_ms(agg['latency_ms_mean'])} "
        f"p95={_ms(agg['latency_ms_p95'])}  within≤budget={_pct(agg['within_budget_rate'])}"
    )
    print("=" * 60)


def _pct(v):
    return "n/a" if v is None else f"{v*100:.0f}%"


def _ms(v):
    return "n/a" if v is None else f"{v:.0f}ms"


if __name__ == "__main__":
    raise SystemExit(main())
