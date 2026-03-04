from __future__ import annotations

import contextvars
from typing import Any

from operator_ai.tools.registry import tool

_context_var: contextvars.ContextVar[dict[str, Any]] = contextvars.ContextVar("_messaging_context")


def configure(context: dict[str, Any]) -> None:
    _context_var.set(context)


@tool(
    description="Post a message to a channel. Returns a platform message ID.",
)
async def send_message(channel: str, text: str, thread_id: str = "") -> str:
    """Post a message to a channel.

    Args:
        channel: Channel name or ID (format depends on platform).
        text: Message content (markdown supported).
        thread_id: Optional message ID to reply in a thread (ignored if platform has no threading).
    """
    ctx = _context_var.get({})
    transport = ctx.get("transport")
    if transport is None:
        return "[error: no transport configured for send_message]"

    channel_id = await transport.resolve_channel_id(channel)
    if channel_id is None:
        return f"[error: could not resolve channel '{channel}']"

    try:
        message_id = await transport.send(channel_id, text, thread_id=thread_id or None)
        return message_id
    except Exception as e:
        return f"[error: failed to send message: {e}]"
