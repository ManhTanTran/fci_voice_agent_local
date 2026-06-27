"""Nạp Scenario từ file JSON (Vai 1 sở hữu — data thuần, không phải code).

Dùng JSON stdlib để KHÔNG thêm dependency (pyyaml). Một scenario = nghiệp vụ +
persona + mục tiêu + danh mục tool + agenda lượt-thoại-có-nhãn.

Hỗ trợ:
- `tools` inline HOẶC `tools_ref`: tên file JSON (cùng thư mục) chứa danh mục tool
  dùng chung — tránh lặp block tool lớn ở mỗi scenario khó.
- Mỗi tham số tool có thể là chuỗi (chỉ tên) hoặc object {name,type,enum,pattern}
  để mang ràng buộc cho structured decoding + tạo case khó.
"""

from __future__ import annotations

import json
from pathlib import Path

from .types import Scenario, ScenarioTurn, ToolSpec


def _parse_tool(t: dict) -> ToolSpec:
    params: list[str] = []
    schema: dict = {}
    for p in t.get("params", []):
        if isinstance(p, str):
            params.append(p)
        else:  # object: {name, type?, enum?, pattern?}
            name = p["name"]
            params.append(name)
            spec = {k: p[k] for k in ("type", "enum", "pattern") if k in p}
            if spec:
                schema[name] = spec
    return ToolSpec(
        name=t["name"], description=t.get("description", ""), params=params, schema=schema
    )


def _load_tools(data: dict, base: Path) -> list[ToolSpec]:
    if "tools_ref" in data:
        ref = json.loads((base / data["tools_ref"]).read_text(encoding="utf-8"))
        raw = ref["tools"] if isinstance(ref, dict) else ref
    else:
        raw = data.get("tools", [])
    return [_parse_tool(t) for t in raw]


def load_scenario(path: str | Path) -> Scenario:
    path = Path(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    tools = _load_tools(data, path.parent)
    agenda = [
        ScenarioTurn(
            user=t["user"],
            expected_tool=t["expected"].get("tool"),
            expected_args=t["expected"].get("args", {}),
            note=t.get("note", ""),
        )
        for t in data["agenda"]
    ]
    return Scenario(
        id=data["id"],
        domain=data["domain"],
        persona=data["persona"],
        goal=data["goal"],
        language=data.get("language", "en"),
        tools=tools,
        agenda=agenda,
        required_tools=data.get("success", {}).get("required_tools", []),
    )
