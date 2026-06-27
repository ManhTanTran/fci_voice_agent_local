"""Exp 05 — THÔNG LUỒNG gym-env (text mode / tool-calling) — chạy CẢ SUITE.

Vòng lặp mỗi scenario: env.reset() -> [bot.act(obs) -> env.step(action)]* -> scorecard.
Chạy hết scenarios/*.json rồi tổng hợp -> số liệu so sánh giữa các policy/phiên bản.

Chọn policy qua FCI_POLICY:
- rule (mặc định): RuleBasedPolicy baseline, LOCAL, không cần GPU/model.
- llm: LLMPolicy (Qwen 1.5B) — chạy trên DGX để ĐO NĂNG LỰC bot thật.

Lọc 1 scenario:  FCI_SCENARIO=card_lock_en  (khớp theo tên file, không cần .json)

Chạy:
  python experiments/05_gym_env_text_smoke/run_gym_text.py
  FCI_POLICY=llm uv run python experiments/05_gym_env_text_smoke/run_gym_text.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from fci_voice.sim import GymEnv, RuleBasedPolicy, load_scenario  # noqa: E402

# Thư mục scenario: mặc định của exp05, override bằng FCI_SCEN_DIR (vd suite khó exp06).
SCEN_DIR = Path(os.getenv("FCI_SCEN_DIR", Path(__file__).parent / "scenarios"))


def _scenario_files(d: Path):
    # Bỏ file KHÔNG phải scenario: danh mục tool dùng chung (tools_*), file _*.
    return sorted(
        f for f in d.glob("*.json") if not f.stem.startswith(("tools", "_"))
    )


def build_policy(which: str, scenario):
    if which == "llm":
        from fci_voice.sim import LLMPolicy

        p = LLMPolicy.for_scenario(scenario)
        return p
    return RuleBasedPolicy()


def run_episode(policy, scenario, verbose: bool = True):
    env = GymEnv(scenario)
    obs = env.reset()
    done = False
    while not done:
        action = policy.act(obs)
        obs, sig, done = env.step(action)
        if verbose:
            mark = "PASS" if sig.turn_pass else "FAIL"
            tool = sig.got_tool or "—"
            line = (
                f"   [turn {sig.turn_index}] {mark} "
                f"T1={int(sig.t1_decision_ok)} T2={_b(sig.t2_tool_ok)} "
                f"T3={_b(sig.t3_args_ok)} | got={tool}"
            )
            if sig.detail:
                line += f"  ({sig.detail})"
            print(line)
    return env.result()


def main() -> int:
    which = os.getenv("FCI_POLICY", "rule").lower()
    only = os.getenv("FCI_SCENARIO", "").strip()

    files = _scenario_files(SCEN_DIR)
    if only:
        files = [f for f in files if only in f.stem]
    if not files:
        print(f"!! không thấy scenario nào ({SCEN_DIR}, filter='{only}')")
        return 2

    # Nạp LLM 1 lần dùng chung cho mọi scenario (free-form + xgrammar đều cần).
    shared_llm = None
    if which in ("llm", "xgrammar"):
        from fci_voice.sim import LLMPolicy

        print(f">> policy={which} (Qwen1.5B) — đang nạp model trên DGX...")
        tmp = LLMPolicy()
        tmp.llm.load()
        shared_llm = tmp.llm
        print(f">> model loaded on {tmp.llm.device_str}\n")
    else:
        print(">> policy=RuleBased (baseline, local)\n")

    reasoning = os.getenv("FCI_REASONING", "").lower() in ("1", "true", "yes")

    results = []
    for f in files:
        scen = load_scenario(f)
        if which == "llm":
            from fci_voice.sim import LLMPolicy

            policy = LLMPolicy.for_scenario(scen, llm=shared_llm)
        elif which == "xgrammar":
            from fci_voice.sim import XGrammarToolPolicy

            policy = XGrammarToolPolicy(scen, llm=shared_llm, with_reasoning=reasoning)
        else:
            policy = RuleBasedPolicy()
        print(f"=== {scen.id} | policy={policy.name} ===")
        res = run_episode(policy, scen)
        rates = res.tier_rates()
        print(
            f"   -> goal={res.goal_success} "
            f"T1={_pct(rates['T1_decision'])} T2={_pct(rates['T2_tool'])} "
            f"T3={_pct(rates['T3_args'])} turn_pass={_pct(rates['turn_pass'])} "
            f"lat={res.total_latency_s*1000:.0f}ms\n"
        )
        results.append((scen.id, res, rates))

    _print_suite(results)
    # exit 0 nếu mọi scenario đạt goal.
    return 0 if all(r.goal_success for _, r, _ in results) else 1


def _print_suite(results):
    n = len(results)
    goals = sum(1 for _, r, _ in results if r.goal_success)
    all_turn = [s.turn_pass for _, r, _ in results for s in r.signals]
    macro_pass = _mean([rt["turn_pass"] for _, _, rt in results])
    print("=" * 56)
    print(f"SUITE: {n} scenario | goal_success {goals}/{n}")
    print(f"  micro turn_pass : {_pct(_mean([1.0 if x else 0.0 for x in all_turn]))} "
          f"({sum(all_turn)}/{len(all_turn)} lượt)")
    print(f"  macro turn_pass : {_pct(macro_pass)} (trung bình theo scenario)")
    print("=" * 56)


def _mean(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else None


def _b(v):
    return "—" if v is None else int(v)


def _pct(v):
    return "n/a" if v is None else f"{v*100:.0f}%"


if __name__ == "__main__":
    raise SystemExit(main())
