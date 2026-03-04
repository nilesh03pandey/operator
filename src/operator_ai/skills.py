from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


@dataclass
class SkillInfo:
    name: str
    description: str
    location: str
    env: list[str] = field(default_factory=list)
    env_missing: list[str] = field(default_factory=list)


def scan_skills(skills_dir: Path) -> list[SkillInfo]:
    """Scan skills directory, parse SKILL.md frontmatter, return skill metadata."""
    skills: list[SkillInfo] = []
    if not skills_dir.is_dir():
        return skills

    for skill_dir in sorted(skills_dir.iterdir()):
        if not skill_dir.is_dir():
            continue
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            continue
        try:
            frontmatter = parse_frontmatter(skill_md.read_text())
            if frontmatter:
                # Parse env requirements from metadata.env
                metadata = frontmatter.get("metadata") or {}
                env_vars = metadata.get("env") or []
                if isinstance(env_vars, str):
                    env_vars = [env_vars]
                missing = [v for v in env_vars if not os.environ.get(v)]
                if missing:
                    logger.warning(
                        "Skill '%s' missing env vars: %s",
                        frontmatter.get("name", skill_dir.name),
                        ", ".join(missing),
                    )

                skills.append(
                    SkillInfo(
                        name=frontmatter.get("name", skill_dir.name),
                        description=frontmatter.get("description", ""),
                        location=str(skill_md),
                        env=env_vars,
                        env_missing=missing,
                    )
                )
        except Exception as e:
            logger.warning("Failed to parse %s: %s", skill_md, e)
    return skills


def build_skills_prompt(skills: list[SkillInfo]) -> str:
    """Build markdown block for system prompt injection."""
    if not skills:
        return ""
    lines = ["# Available Skills"]
    for s in skills:
        status = f" (missing env: {', '.join(s.env_missing)})" if s.env_missing else ""
        lines.append(f"\n- **{s.name}**: {s.description}{status}")
        lines.append(f"  - Location: `{s.location}`")
    return "\n".join(lines)


def parse_frontmatter(text: str) -> dict[str, Any] | None:
    """Parse YAML frontmatter between --- delimiters."""
    split = _split_frontmatter(text)
    if split is None:
        return None
    frontmatter_text, _ = split
    try:
        parsed = yaml.safe_load(frontmatter_text)
    except yaml.YAMLError:
        return None
    if not isinstance(parsed, dict):
        return None
    return parsed


def extract_body(text: str) -> str:
    """Return the markdown body after the --- frontmatter block."""
    split = _split_frontmatter(text)
    if split is None:
        return text.strip()
    _, body = split
    return body.strip()


def rewrite_frontmatter(path: Path, updates: dict) -> bool:
    """Update specific fields in a file's YAML frontmatter, preserving the body.

    Returns True on success, False if frontmatter couldn't be parsed.
    """
    text = path.read_text()
    fm = parse_frontmatter(text)
    if not fm:
        return False
    fm.update(updates)
    body = extract_body(text)
    new_fm = yaml.dump(fm, default_flow_style=False, sort_keys=False).strip()
    path.write_text(f"---\n{new_fm}\n---\n\n{body}\n")
    return True


def _split_frontmatter(text: str) -> tuple[str, str] | None:
    """Split markdown into (frontmatter, body) when fenced by top-level --- lines."""
    if not text:
        return None

    # Allow UTF-8 BOM at file start.
    normalized = text.lstrip("\ufeff")
    lines = normalized.splitlines()
    if not lines or lines[0].strip() != "---":
        return None

    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            frontmatter = "\n".join(lines[1:idx])
            body = "\n".join(lines[idx + 1 :])
            return frontmatter, body
    return None
