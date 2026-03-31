from __future__ import annotations

from pathlib import Path

from src.main.spec.service import build_test_plan_markdown, load_strategy_spec


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def test_build_test_plan_markdown_uses_verification_profile_language() -> None:
    spec = load_strategy_spec(_repo_root())

    markdown = build_test_plan_markdown(spec)
    lowered = markdown.lower()

    assert "default verification profile: `focus.smoke`" in lowered
    assert "validate --json" not in lowered
    assert "focus test --json" not in lowered
    assert "optionforge" not in lowered
