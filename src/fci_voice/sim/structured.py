"""Structured decoding bước đầu: ép tool-call vào JSON-schema bằng xgrammar.

Ý tưởng: từ danh mục ToolSpec (có enum/pattern), dựng 1 JSON-schema dạng
DISCRIMINATED UNION ({"tool": <enum tên>, "args": {...theo từng tool...}}) cộng
nhánh "none" để bot từ chối gọi. Grammar ép output LUÔN hợp lệ + enum/pattern
đúng — trị tận gốc lỗi free-form (enum ngoài tập, sai cấu trúc, bịa tên tool).

Tham chiếu thiết kế: docs/11_sim_test_system + .agent/skills/05 (constrained decoding).
"""

from __future__ import annotations

import json
import os
import time

from .policy import _grounded, _parse_tool_call  # tái dùng grounding + parser dự phòng
from .types import Action, Observation, ToolCall, ToolSpec


def _arg_field(spec: dict) -> dict:
    """Map ràng buộc 1 tham số -> mảnh JSON-schema."""
    if spec.get("enum"):
        return {"type": "string", "enum": spec["enum"]}
    if spec.get("type") == "number":
        return {"type": "number"}
    if spec.get("pattern"):
        return {"type": "string", "pattern": spec["pattern"]}
    return {"type": "string"}


def build_tool_json_schema(
    tools: list[ToolSpec], allow_none: bool = True, with_reasoning: bool = False
) -> dict:
    """Dựng JSON-schema discriminated-union cho danh mục tool của 1 scenario."""
    branches = []
    for t in tools:
        props = {}
        if with_reasoning:
            props["reasoning"] = {"type": "string"}
        props["tool"] = {"const": t.name}
        args_props = {p: _arg_field(t.schema.get(p, {})) for p in t.params}
        props["args"] = {
            "type": "object",
            "properties": args_props,
            "required": list(t.params),
            "additionalProperties": False,
        }
        required = (["reasoning"] if with_reasoning else []) + ["tool", "args"]
        branches.append(
            {
                "type": "object",
                "properties": props,
                "required": required,
                "additionalProperties": False,
            }
        )
    if allow_none:
        none_props = {}
        if with_reasoning:
            none_props["reasoning"] = {"type": "string"}
        none_props["tool"] = {"const": "none"}
        none_props["args"] = {"type": "object", "properties": {}, "additionalProperties": False}
        branches.append(
            {
                "type": "object",
                "properties": none_props,
                "required": (["reasoning"] if with_reasoning else []) + ["tool", "args"],
                "additionalProperties": False,
            }
        )
    return {"oneOf": branches}


_SYS = (
    "You are a {domain} phone agent. Goal: {goal}.\n"
    "Decide the single best action for the LATEST user turn and output ONE JSON object.\n\n"
    "TOOLS:\n{tools}\n\n"
    'Use {{"tool":"none","args":{{}}}} when NO tool should be called: a greeting, a '
    "general/policy question, small talk, the user refuses to verify, a required value "
    "is missing, or the request is unsupported.\n"
    "Only call a tool when the user clearly asks for that action AND every required value "
    "is present in the conversation. Choose enum values ONLY from the allowed options. "
    'Formats: dob/end_date = ISO "YYYY-MM-DD".'
)


class XGrammarToolPolicy:
    """Policy dùng xgrammar ép tool-call theo JSON-schema của scenario."""

    name = "xgrammar_qwen1.5b"

    def __init__(self, scenario, llm=None, with_reasoning: bool = False):
        if llm is None:
            from ..agent.llm import TransformersLLM

            llm = TransformersLLM()
        self.llm = llm
        self.tools = scenario.tools
        self.domain = scenario.domain
        self.goal = scenario.goal
        self.with_reasoning = with_reasoning
        self.schema = build_tool_json_schema(scenario.tools, with_reasoning=with_reasoning)
        self._compiled = None

    def _ensure_grammar(self):
        if self._compiled is not None:
            return
        import xgrammar as xgr

        tok = self.llm.tokenizer
        vocab = self.llm.model.config.vocab_size
        ti = xgr.TokenizerInfo.from_huggingface(tok, vocab_size=vocab)
        self._xgr = xgr
        self._compiler = xgr.GrammarCompiler(ti)
        self._compiled = self._compiler.compile_json_schema(json.dumps(self.schema))

    def _system(self) -> str:
        lines = []
        for t in self.tools:
            parts = []
            for p in t.params:
                s = t.schema.get(p, {})
                if s.get("enum"):
                    parts.append(f"{p} one of {s['enum']}")
                elif s.get("pattern"):
                    parts.append(f"{p} matching {s['pattern']}")
                else:
                    parts.append(p)
            lines.append(f"- {t.name}({', '.join(parts)}): {t.description}")
        return _SYS.format(domain=self.domain, goal=self.goal, tools="\n".join(lines))

    def act(self, obs: Observation) -> Action:
        self._ensure_grammar()
        lp = self._xgr.contrib.hf.LogitsProcessor(self._compiled)

        messages = [{"role": "system", "content": self._system()}]
        messages += obs.history
        messages.append({"role": "user", "content": obs.latest_user})
        res = self.llm.chat(messages, max_new_tokens=160, logits_processor=[lp])
        if os.getenv("FCI_DEBUG"):
            print(f"      [raw] {res.text!r}")

        # Grammar đảm bảo JSON hợp lệ; vẫn fallback parser nếu có gì bất ngờ.
        try:
            obj = json.loads(res.text)
        except json.JSONDecodeError:
            call = _parse_tool_call(res.text)
            return Action(text="" if call else res.text, tool_call=call, latency_s=res.latency_s)

        tool = obj.get("tool")
        call = None
        if tool and tool != "none":
            call = ToolCall(name=str(tool), args=obj.get("args", {}) or {})
            # Grounding cho param không-enum: grammar ép format đúng, nhưng không
            # đảm bảo ĐÚNG GIÁ TRỊ (vd số tài khoản) -> vẫn chặn bịa slot.
            user_said = " ".join(
                m["content"] for m in obs.history if m.get("role") == "user"
            )
            user_said += " " + obs.latest_user
            spec = next((t for t in self.tools if t.name == call.name), None)
            if not _grounded(call, user_said, spec):
                if os.getenv("FCI_DEBUG"):
                    print(f"      [drop] args không grounded: {call.args}")
                call = None
        return Action(text="", tool_call=call, latency_s=res.latency_s)
