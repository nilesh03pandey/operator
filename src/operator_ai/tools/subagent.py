from __future__ import annotations

import asyncio
import contextvars
from typing import Any

import sys

from operator_a.log_context import get_run_context, new_run_id, set_run_context
from operator_ai.tools.registry import tool
from operator_ai.prompts import load_agent_prompt


MAX_SUBAGENT_DEPTH = 3

_context_var: contextvars.ContextVar[dict[str, Any]] = contextvars.ContextVar("_agent_context")


def configure(context: dict[str, Any]) -> None:
    _context_var.set(context)


@tool(
    description="Spawn a sub-agent to handle a focused sub-task. The sub-agent gets its own conversation and runs to completion. Returns the sub-agent's final response.",
)
async def spawn_agent(task: str, context: str = "", agent: str = None) -> str:
    """Spawn a sub-agent for a focused sub-task.

    Args:
        task: Clear description of what the sub-agent should accomplish.
        context: Optional additional context or data for the sub-agent.
    """

    

    current_context = _context_var.get({})
    depth = current_context.get("depth", 0)
    if depth >= MAX_SUBAGENT_DEPTH:
        return f"[error: max subagent depth ({MAX_SUBAGENT_DEPTH}) reached]"

    system_prompt = (
        "You are a focused sub-agent. Complete the given task and return a clear, "
        "concise result. You have access to the same tools as the parent agent."
    )
    if context:
        system_prompt += f"\n\nAdditional context:\n{context}"

    

    messages: list[dict[str, Any]] = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": task},
    ]

    config = current_context.get("config")
    if not config:
        # or raise error 
        pass

    if agent and isinstance(agent, str):
        agent = agent.strip().lower()
        
        if not agent:
            # empty after strip then skip or log
            pass
        else:
            agent_prompt = load_agent_prompt(config, agent)
            
            if agent_prompt:  
                new_system_content = (f"{agent_prompt}")
                # Safely insert/replace system prompt at the beginning
                if messages and messages[0].get("role") == "system":
                    # Merge into existing system prompt (preserves order)
                    messages[0]["content"] = new_system_content + "\n\n" + messages[0]["content"]
                else:
                    messages.insert(0, {"role": "system", "content": new_system_content})

                # print(f"Applied agent prompt for '{agent}'")
            else:
                # logger.warning(f"No prompt found for agent: {agent}")
                pass


    # Lazy import to avoid circular dependency (agent -> subagent -> agent)
    from operator_ai.agent import run_agent

    parent_ctx = get_run_context()

    async def _child() -> str:
        set_run_context(
            agent=parent_ctx.agent if parent_ctx else "sub",
            run_id=parent_ctx.run_id if parent_ctx else new_run_id(),
            depth=depth + 1,
        )
        return await run_agent(
            messages=messages,
            models=current_context["models"],
            max_iterations=min(current_context.get("max_iterations", 10), 10),
            workspace=current_context.get("workspace", "."),
            depth=depth + 1,
            context_ratio=current_context.get("context_ratio", 0.0),
            max_output_tokens=current_context.get("max_output_tokens"),
            extra_tools=current_context.get("extra_tools"),
            usage=current_context.get("usage"),
            tool_filter=current_context.get("tool_filter"),
            shared_dir=current_context.get("shared_dir"),
        )

    # Run in a copied context so the child's configure() call doesn't
    # overwrite the parent's ContextVars (depth, workspace, etc.).
    return await asyncio.create_task(_child(), context=contextvars.copy_context())
