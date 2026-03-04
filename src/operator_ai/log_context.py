from __future__ import annotations

import logging
import os
from contextvars import ContextVar
from dataclasses import dataclass


@dataclass(frozen=True)
class RunContext:
    agent: str
    run_id: str = ""
    depth: int = 0

    def __str__(self) -> str:
        if not self.run_id:
            return f"[{self.agent}]"
        depth_suffix = f":d{self.depth}" if self.depth else ""
        return f"[{self.agent}:{self.run_id}{depth_suffix}]"


_run_context: ContextVar[RunContext | None] = ContextVar("_run_context", default=None)


def set_run_context(agent: str, run_id: str = "", depth: int = 0) -> None:
    _run_context.set(RunContext(agent=agent, run_id=run_id, depth=depth))


def get_run_context() -> RunContext | None:
    return _run_context.get()


def new_run_id() -> str:
    return os.urandom(4).hex()


class RunContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        ctx = _run_context.get()
        record.run_ctx = f"{ctx} " if ctx else ""  # type: ignore[attr-defined]
        return True
