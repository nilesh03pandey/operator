"""Shared prompt assembly helpers for chat and job system prompts."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from operator_ai.config import OPERATOR_DIR, Config
from operator_ai.skills import build_skills_prompt, scan_skills

PROMPTS_DIR = Path(__file__).parent
SYSTEM_PROMPT_PATH = OPERATOR_DIR / "SYSTEM.md"
SKILLS_DIR = OPERATOR_DIR / "skills"


def load_prompt(name: str) -> str:
    """Load a bundled prompt template from the prompts/ package directory."""
    path = PROMPTS_DIR / name
    return path.read_text().strip()


def load_system_prompt() -> str:
    """Load SYSTEM.md from disk, creating it from the bundled default if missing."""
    if not SYSTEM_PROMPT_PATH.exists():
        SYSTEM_PROMPT_PATH.parent.mkdir(parents=True, exist_ok=True)
        SYSTEM_PROMPT_PATH.write_text(load_prompt("system.md"))
    return SYSTEM_PROMPT_PATH.read_text().strip()


def load_agent_prompt(config: Config, agent_name: str) -> str:
    """Load AGENT.md verbatim. Returns empty string if the file doesn't exist."""
    agent_md = config.agent_prompt_path(agent_name)
    if agent_md.exists():
        return agent_md.read_text().strip()
    return ""


def load_skills_prompt(skills_dir: Path = SKILLS_DIR) -> str:
    """Load available-skill metadata as markdown for system prompt injection."""
    return build_skills_prompt(scan_skills(skills_dir))


def assemble_system_prompt(
    config: Config,
    agent_name: str,
    context_sections: Iterable[str] = (),
    *,
    pinned_memory_lines: Iterable[str] = (),
    transport_extra: str = "",
    skills_dir: Path = SKILLS_DIR,
) -> str:
    """Assemble the runtime system prompt with shared ordering for chat and jobs."""
    parts: list[str] = [
        load_system_prompt(),
        load_agent_prompt(config, agent_name),
    ]

    parts.extend(section.strip() for section in context_sections if section and section.strip())

    pinned_lines = [line for line in pinned_memory_lines if line]
    if pinned_lines:
        parts.append("# Pinned Memories\n\n" + "\n".join(pinned_lines))

    skills_prompt = load_skills_prompt(skills_dir)
    if skills_prompt:
        parts.append(skills_prompt)

    if transport_extra.strip():
        parts.append(transport_extra.strip())

    return "\n\n".join(part for part in parts if part)
