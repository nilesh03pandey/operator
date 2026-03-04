from __future__ import annotations

from operator_ai.memory import _parse_harvested_line


def test_parse_harvested_line_rejects_user_scope_when_not_private() -> None:
    parsed = _parse_harvested_line(
        "- [user] Gavin likes espresso",
        user_id="slack:U123",
        agent_name="hermy",
        allow_user_scope=False,
    )
    assert parsed is None


def test_parse_harvested_line_accepts_agent_and_global_when_not_private() -> None:
    parsed_agent = _parse_harvested_line(
        "- [agent] Project uses uv",
        user_id="",
        agent_name="hermy",
        allow_user_scope=False,
    )
    parsed_global = _parse_harvested_line(
        "- [global] Python 3.11 is required",
        user_id="",
        agent_name="hermy",
        allow_user_scope=False,
    )
    assert parsed_agent == ("agent", "hermy", "Project uses uv")
    assert parsed_global == ("global", "global", "Python 3.11 is required")
