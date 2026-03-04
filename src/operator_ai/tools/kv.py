from __future__ import annotations

import contextvars
import logging
from typing import Any

from operator_ai.store import get_store
from operator_ai.tools.registry import tool

logger = logging.getLogger("operator.kv")

_context_var: contextvars.ContextVar[dict[str, Any]] = contextvars.ContextVar("_kv_context")


def configure(context: dict[str, Any]) -> None:
    _context_var.set(context)


def _agent() -> str:
    ctx = _context_var.get({})
    agent = ctx.get("agent_name", "")
    if not agent:
        raise ValueError("agent context not configured")
    return agent


@tool(
    description="Get a value from the key-value store. Returns the value or '[not found]' if the key doesn't exist.",
)
async def kv_get(key: str, namespace: str = "") -> str:
    """Get a value by key.

    Args:
        key: The key to look up.
        namespace: Optional namespace for grouping related keys (e.g. job name).
    """
    try:
        agent = _agent()
    except ValueError as e:
        return f"[error: {e}]"

    result = get_store().kv_get(agent, key, ns=namespace)
    if result is None:
        return "[not found]"
    return result


@tool(
    description="Set a key-value pair in the store. Overwrites any existing value for this key.",
)
async def kv_set(key: str, value: str, namespace: str = "", ttl_hours: int = 0) -> str:
    """Store a key-value pair.

    Args:
        key: The key to store.
        value: The value to store (string or JSON).
        namespace: Optional namespace for grouping related keys (e.g. job name).
        ttl_hours: Auto-expire after this many hours. 0 means no expiry.
    """
    try:
        agent = _agent()
    except ValueError as e:
        return f"[error: {e}]"

    get_store().kv_set(agent, key, value, ns=namespace, ttl_hours=ttl_hours or None)
    ttl_msg = f", expires in {ttl_hours}h" if ttl_hours else ""
    ns_msg = f" in '{namespace}'" if namespace else ""
    return f"Stored '{key}'{ns_msg}{ttl_msg}"


@tool(
    description="Delete a key from the key-value store.",
)
async def kv_delete(key: str, namespace: str = "") -> str:
    """Delete a key.

    Args:
        key: The key to delete.
        namespace: Optional namespace.
    """
    try:
        agent = _agent()
    except ValueError as e:
        return f"[error: {e}]"

    if get_store().kv_delete(agent, key, ns=namespace):
        return f"Deleted '{key}'"
    return f"Key '{key}' not found"


@tool(
    description="List keys in the key-value store, optionally filtered by namespace and key prefix.",
)
async def kv_list(namespace: str = "", prefix: str = "") -> str:
    """List stored keys and values.

    Args:
        namespace: Namespace to list. Empty string lists the default namespace.
        prefix: Only return keys starting with this prefix.
    """
    try:
        agent = _agent()
    except ValueError as e:
        return f"[error: {e}]"

    results = get_store().kv_list(agent, ns=namespace, prefix=prefix)
    if not results:
        return "No keys found."

    lines = []
    for r in results:
        exp = f" (expires: {r['expires_at']})" if r.get("expires_at") else ""
        lines.append(f"{r['key']} = {r['value']}{exp}")
    return "\n".join(lines)
