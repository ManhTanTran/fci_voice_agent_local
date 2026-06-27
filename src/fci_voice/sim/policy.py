"""BotPolicy — interface chuẩn + 2 hiện thực: RuleBased (baseline) và LLM (DGX).

Vai 2 (FCI-bot-dev) sở hữu phần này. Env chỉ gọi `act(observation) -> Action`,
nên sau này bọc bot thật của FCI vào cùng interface mà không sửa env.

- RuleBasedPolicy: baseline deterministic, chạy LOCAL không cần GPU/model —
  dùng để THÔNG LUỒNG + kiểm chứng logic env/scorer.
- LLMPolicy: bọc TransformersLLM (Qwen 1.5B) trên DGX — đây là phép ĐO NĂNG LỰC.
"""

from __future__ import annotations

import json
import os
import re
import time
from typing import Protocol

from .types import Action, Observation, ToolCall


class BotPolicy(Protocol):
    name: str

    def act(self, obs: Observation) -> Action: ...


# --------------------------------------------------------------------------- #
# Baseline: luật regex đơn giản — đủ để chạy thẳng vòng lặp, không cần model.   #
# --------------------------------------------------------------------------- #
class RuleBasedPolicy:
    name = "rule_v0"

    def act(self, obs: Observation) -> Action:
        t0 = time.perf_counter()
        text = obs.latest_user.lower()
        call = None

        # verify_identity: có tên + ngày sinh trong câu.
        m_name = re.search(r"name is ([a-z]+ [a-z]+)", text)
        m_dob = re.search(
            r"(?:dob|date of birth)[^0-9a-z]*([a-z0-9 ,]+\d{4})", text
        )
        if m_name and m_dob:
            call = ToolCall(
                name="verify_identity",
                args={
                    "full_name": m_name.group(1).title(),
                    "dob": _norm_date(m_dob.group(1)),
                },
            )
        else:
            # lock_card: ý định khóa + 4 chữ số cuối.
            m_last4 = re.search(r"(\d{4})", text)
            if "lock" in text and m_last4:
                call = ToolCall(
                    name="lock_card", args={"card_last4": m_last4.group(1)}
                )

        reply = "Sure, let me help with that." if call else "Okay, noted. Anything else?"
        return Action(text=reply, tool_call=call, latency_s=time.perf_counter() - t0)


def _norm_date(raw: str) -> str:
    """Đổi 'march 5th 1990' -> '1990-03-05' để khớp nhãn chuẩn ISO."""
    months = {
        "january": "01", "february": "02", "march": "03", "april": "04",
        "may": "05", "june": "06", "july": "07", "august": "08",
        "september": "09", "october": "10", "november": "11", "december": "12",
    }
    s = raw.lower().replace(",", " ")
    mon = next((months[w] for w in s.split() if w in months), None)
    nums = re.findall(r"\d+", s)
    day = next((n for n in nums if len(n) <= 2), None)
    year = next((n for n in nums if len(n) == 4), None)
    if mon and day and year:
        return f"{year}-{mon}-{int(day):02d}"
    return raw.strip()


# --------------------------------------------------------------------------- #
# LLM policy: prompt tool-calling, parse JSON từ output. Chạy trên DGX (GPU).   #
# --------------------------------------------------------------------------- #
_SYS_TMPL = (
    "You are a {domain} phone agent. Goal: {goal}.\n\n"
    "TOOLS:\n{tools}\n\n"
    "RULES:\n"
    "1. To use a tool, reply with ONLY a single-line JSON object: "
    '{{"tool":"<name>","args":{{...}}}} — nothing else on the line.\n'
    "2. Otherwise reply with ONE short plain sentence. NEVER mix JSON and prose.\n"
    "3. Call a tool ONLY when the user clearly asks for that action AND you already "
    "have EVERY required parameter value. If a value is missing, do NOT call a tool — "
    "ask for it in plain text.\n"
    "4. NEVER call a tool on a greeting, a general/policy question, or small talk.\n"
    "5. When the user gives a clear action request together with all needed values, "
    "you MUST emit the tool JSON (do not just chat).\n"
    "6. Formats: dob = ISO \"YYYY-MM-DD\"; card_last4 = the 4 digits only; "
    "account_id = exactly as the user said it.\n"
    "7. Emit AT MOST ONE tool call per reply. NEVER invent or use placeholder values "
    "(like \"DOB\" or \"CardLast4\"); if you do not have a real value, ask for it instead.\n\n"
    "EXAMPLES:\n"
    "User: Hi, I lost my card, please lock it.\n"
    "Assistant: Of course — first I need to verify you. What is your full name and "
    "date of birth?\n"
    "User: It's Jane Doe, born February 9th 1992.\n"
    'Assistant: {{"tool":"verify_identity","args":{{"full_name":"Jane Doe","dob":"1992-02-09"}}}}\n'
    "User: Lock the card ending 1234.\n"
    'Assistant: {{"tool":"lock_card","args":{{"card_last4":"1234"}}}}\n'
    "User: What's my balance, account AC-7000?\n"
    'Assistant: {{"tool":"get_balance","args":{{"account_id":"AC-7000"}}}}'
)


class LLMPolicy:
    name = "llm_qwen1.5b"

    def __init__(
        self,
        llm=None,
        model_name: str = "Qwen/Qwen2.5-1.5B-Instruct",
        domain: str = "bank",
        goal: str = "assist the caller",
    ):
        # Lazy import để máy không có torch vẫn import được module.
        if llm is None:
            from ..agent.llm import TransformersLLM

            llm = TransformersLLM(model_name=model_name)
        self.llm = llm
        self.domain = domain
        self.goal = goal

    @classmethod
    def for_scenario(cls, scenario, **kw) -> "LLMPolicy":
        # Lấy đúng domain/goal từ scenario để system prompt sát nghiệp vụ.
        return cls(domain=scenario.domain, goal=scenario.goal, **kw)

    def _system(self, obs: Observation) -> str:
        tools = "\n".join(
            f"- {t.name}({', '.join(t.params)}): {t.description}" for t in obs.tools
        )
        return _SYS_TMPL.format(domain=self.domain, goal=self.goal, tools=tools)

    def act(self, obs: Observation) -> Action:
        messages = [{"role": "system", "content": self._system(obs)}]
        messages += obs.history
        messages.append({"role": "user", "content": obs.latest_user})
        res = self.llm.chat(messages, max_new_tokens=96)
        if os.getenv("FCI_DEBUG"):
            print(f"      [raw] {res.text!r}")
        call = _parse_tool_call(res.text)

        # Slot-grounding: bỏ call nếu giá trị args KHÔNG có trong lời người dùng
        # (chống model bịa slot / nhái giá trị few-shot — vd "AC-7000", "Customer Name").
        if call is not None:
            user_said = " ".join(
                m["content"] for m in obs.history if m.get("role") == "user"
            )
            user_said += " " + obs.latest_user
            spec = next((t for t in obs.tools if t.name == call.name), None)
            if not _grounded(call, user_said, spec):
                if os.getenv("FCI_DEBUG"):
                    print(f"      [drop] args không grounded: {call.args}")
                call = None

        text = "" if call else res.text
        return Action(text=text, tool_call=call, latency_s=res.latency_s)


def _grounded(call: ToolCall, user_text: str, spec=None) -> bool:
    """Mọi giá trị arg phải bám vào lời người dùng: cụm số (>=3 chữ số) hoặc 1 token chữ.

    BỎ QUA param kiểu enum: giá trị canonical thường KHÁC từ bề mặt
    ("dollars"->USD, "France"->FR) nên grounding bề mặt không áp được —
    membership của enum sẽ do structured decoding (grammar) đảm bảo.
    """
    text = user_text.lower()
    digits_only = re.sub(r"\D", "", text)
    enum_params = set((spec.schema if spec else {}).keys()) & {
        k for k, s in (spec.schema if spec else {}).items() if s.get("enum")
    }
    for k, v in call.args.items():
        if k in enum_params:
            continue
        sv = str(v).lower()
        num_runs = re.findall(r"\d{3,}", sv)  # năm sinh, last4, mã tài khoản
        if num_runs:
            if not all(d in text or d in digits_only for d in num_runs):
                return False
        else:
            toks = [t for t in re.findall(r"[a-zA-Z]+", sv) if len(t) >= 3]
            if toks and not any(t in text for t in toks):
                return False
    return True


def _parse_tool_call(out: str) -> ToolCall | None:
    """Lấy object JSON {"tool":...,"args":...} TOP-LEVEL ĐẦU TIÊN hợp lệ.

    Quét cân-bằng-ngoặc thay vì regex tham lam: nếu model lỡ in nhiều dòng JSON
    (vd lên kế hoạch nhiều tool), ta chỉ nhận lời gọi đầu tiên — đúng "1 lượt 1 hành động".
    """
    start = out.find("{")
    while start != -1:
        depth = 0
        for i in range(start, len(out)):
            if out[i] == "{":
                depth += 1
            elif out[i] == "}":
                depth -= 1
                if depth == 0:
                    blob = out[start : i + 1]
                    try:
                        obj = json.loads(blob)
                    except json.JSONDecodeError:
                        obj = None
                    if isinstance(obj, dict) and obj.get("tool"):
                        args = obj.get("args") or {}
                        return ToolCall(
                            name=str(obj["tool"]),
                            args=args if isinstance(args, dict) else {},
                        )
                    break  # object này hỏng -> nhảy tới '{' kế tiếp
        start = out.find("{", start + 1)
    return None
