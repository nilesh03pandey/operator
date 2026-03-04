from __future__ import annotations

from zoneinfo import ZoneInfo

import pytest

from operator_ai.config import (
    Config,
    DefaultsConfig,
    ToolPermissions,
    ensure_shared_symlink,
)


def test_timezone_defaults_to_utc() -> None:
    d = DefaultsConfig(models=["test/model"])
    assert d.timezone == "UTC"


def test_timezone_override() -> None:
    d = DefaultsConfig(models=["test/model"], timezone="America/Vancouver")
    assert d.timezone == "America/Vancouver"


def test_config_tz_returns_zoneinfo() -> None:
    c = Config(defaults={"models": ["test/m"], "timezone": "Europe/London"})
    assert c.tz == ZoneInfo("Europe/London")


def test_config_tz_defaults_to_utc() -> None:
    c = Config(defaults={"models": ["test/m"]})
    assert c.tz == ZoneInfo("UTC")


def test_invalid_timezone_raises() -> None:
    with pytest.raises(ValueError, match="Unknown timezone"):
        DefaultsConfig(models=["test/model"], timezone="Mars/Olympus")


# ── Permissions ──────────────────────────────────────────────


def _cfg(**agent_kwargs) -> Config:
    return Config(defaults={"models": ["test/m"]}, agents={"a": agent_kwargs})


def test_no_permissions_returns_none_filters() -> None:
    c = _cfg()
    assert c.agent_tool_filter("a") is None
    assert c.agent_skill_filter("a") is None


def test_tool_allow_filter() -> None:
    c = _cfg(permissions={"tools": {"allow": ["read_file", "list_files"]}})
    f = c.agent_tool_filter("a")
    assert f is not None
    assert f("read_file") is True
    assert f("run_shell") is False


def test_tool_deny_filter() -> None:
    c = _cfg(permissions={"tools": {"deny": ["run_shell"]}})
    f = c.agent_tool_filter("a")
    assert f is not None
    assert f("read_file") is True
    assert f("run_shell") is False


def test_skill_allow_filter() -> None:
    c = _cfg(permissions={"skills": {"allow": ["deploy"]}})
    f = c.agent_skill_filter("a")
    assert f is not None
    assert f("deploy") is True
    assert f("other") is False


def test_skill_deny_filter() -> None:
    c = _cfg(permissions={"skills": {"deny": ["deploy"]}})
    f = c.agent_skill_filter("a")
    assert f is not None
    assert f("deploy") is False
    assert f("other") is True


def test_allow_and_deny_raises() -> None:
    with pytest.raises(ValueError, match="mutually exclusive"):
        ToolPermissions(allow=["a"], deny=["b"])


def test_unknown_agent_returns_none_filter() -> None:
    c = _cfg(permissions={"tools": {"deny": ["run_shell"]}})
    assert c.agent_tool_filter("nonexistent") is None


def test_empty_permissions_returns_none_filter() -> None:
    c = _cfg(permissions={})
    assert c.agent_tool_filter("a") is None
    assert c.agent_skill_filter("a") is None


# ── Shared symlink ───────────────────────────────────────────


def test_ensure_shared_symlink(tmp_path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    shared = tmp_path / "shared"

    ensure_shared_symlink(workspace, shared)

    link = workspace / "shared"
    assert link.is_symlink()
    assert link.resolve() == shared.resolve()
    assert shared.is_dir()


def test_ensure_shared_symlink_idempotent(tmp_path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    shared = tmp_path / "shared"

    ensure_shared_symlink(workspace, shared)
    ensure_shared_symlink(workspace, shared)  # should not raise

    assert (workspace / "shared").is_symlink()


def test_ensure_shared_symlink_skips_non_symlink(tmp_path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    shared = tmp_path / "shared"
    # Create a real directory at the link target
    (workspace / "shared").mkdir()

    ensure_shared_symlink(workspace, shared)

    # Should not have replaced the real directory
    assert not (workspace / "shared").is_symlink()
    assert (workspace / "shared").is_dir()
