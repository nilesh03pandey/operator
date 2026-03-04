from __future__ import annotations

import inspect
import re
from collections.abc import Callable
from typing import Any, get_type_hints

_TOOLS: list[ToolDef] = []


class ToolDef:
    def __init__(self, func: Callable[..., Any], description: str):
        self.func = func
        self.name = func.__name__
        self.description = description
        self.parameters = _build_parameters(func)

    def to_openai_tool(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


def tool(description: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        _TOOLS.append(ToolDef(func, description))
        return func

    return decorator


def get_tools() -> list[ToolDef]:
    return list(_TOOLS)


# --- schema generation from type hints + docstring ---

_TYPE_MAP: dict[type, str] = {
    str: "string",
    int: "integer",
    float: "number",
    bool: "boolean",
}


def _build_parameters(func: Callable[..., Any]) -> dict[str, Any]:
    hints = get_type_hints(func)
    sig = inspect.signature(func)
    doc_args = _parse_docstring_args(func.__doc__ or "")

    properties: dict[str, Any] = {}
    required: list[str] = []

    for param_name, param in sig.parameters.items():
        if param_name in ("self", "cls"):
            continue
        hint = hints.get(param_name, str)
        json_type = _TYPE_MAP.get(hint, "string")
        prop: dict[str, Any] = {"type": json_type}
        if param_name in doc_args:
            prop["description"] = doc_args[param_name]
        properties[param_name] = prop
        if param.default is inspect.Parameter.empty:
            required.append(param_name)

    schema: dict[str, Any] = {
        "type": "object",
        "properties": properties,
        "additionalProperties": False,
    }
    if required:
        schema["required"] = required
    return schema


def _parse_docstring_args(docstring: str) -> dict[str, str]:
    """Parse 'Args:' section from a Google-style docstring."""
    result: dict[str, str] = {}
    in_args = False
    for line in docstring.split("\n"):
        stripped = line.strip()
        if stripped.lower().startswith("args:"):
            in_args = True
            continue
        if in_args:
            if stripped == "" or (not line.startswith(" ") and ":" not in stripped):
                break
            m = re.match(r"\s*(\w+)\s*(?:\(.*?\))?\s*:\s*(.*)", line)
            if m:
                result[m.group(1)] = m.group(2).strip()
    return result
