from __future__ import annotations

from pathlib import Path

from src.main.scaffold.catalog import build_scaffold_plan
from src.main.scaffold.generator import scaffold_strategy
from src.main.scaffold.models import CreateOptions


def test_scaffold_plan_copies_docs_directory_for_child_repositories(tmp_path: Path) -> None:
    plan = build_scaffold_plan(
        CreateOptions(
            name="DDD Guardrail Demo",
            destination=tmp_path,
        )
    )

    assert "AGENTS.md" in plan.base_copy_paths
    assert ".codex" in plan.base_copy_paths
    assert "tests" in plan.base_copy_paths
    assert "docs" in plan.base_copy_paths
    assert "doc" not in plan.base_copy_paths


def test_scaffold_strategy_templates_do_not_generate_stateful_services(tmp_path: Path) -> None:
    package_dir = scaffold_strategy("DDD Guardrail Demo", tmp_path)

    indicator_text = (package_dir / "indicator_service.py").read_text(encoding="utf-8")
    signal_text = (package_dir / "signal_service.py").read_text(encoding="utf-8")

    assert "def __init__(" not in indicator_text
    assert "self.config" not in indicator_text
    assert "def __init__(" not in signal_text
    assert "self.option_type" not in signal_text
    assert "self.strike_level" not in signal_text


def test_repo_signal_templates_do_not_ship_stateful_service_defaults() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    indicator_text = (
        repo_root / "src" / "strategy" / "domain" / "domain_service" / "signal" / "indicator_service.py"
    ).read_text(encoding="utf-8")
    signal_text = (
        repo_root / "src" / "strategy" / "domain" / "domain_service" / "signal" / "signal_service.py"
    ).read_text(encoding="utf-8")

    assert "self.config" not in indicator_text
    assert "def __init__(" not in indicator_text
    assert "def __init__(" not in signal_text
