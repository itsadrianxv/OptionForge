from __future__ import annotations

import json
from pathlib import Path
import tomllib

from src.main.focus.service import load_focus_context, refresh_agent_assets


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def test_focus_manifest_uses_workflow_schema() -> None:
    manifest_path = _repo_root() / "focus" / "strategies" / "main" / "strategy.manifest.toml"
    payload = tomllib.loads(manifest_path.read_text(encoding="utf-8"))

    assert "cli" not in payload
    assert "workflow" in payload
    assert payload["workflow"]["runtime_module"] == "src.main.main"
    assert payload["workflow"]["backtest_module"] == "src.backtesting.main"
    assert payload["acceptance"]["default_verification_profile"] == "focus.smoke"
    assert "minimal_test_command" not in payload["acceptance"]


def test_refresh_agent_assets_writes_workflows_assets() -> None:
    context = refresh_agent_assets(_repo_root())

    assert context.workflows_path == _repo_root() / ".focus" / "WORKFLOWS.md"
    assert not (_repo_root() / ".focus" / "COMMANDS.md").exists()
    assert context.manifest.workflow.runtime_module == "src.main.main"
    assert context.manifest.workflow.backtest_module == "src.backtesting.main"

    workflows_markdown = context.workflows_path.read_text(encoding="utf-8").lower()
    assert "optionforge" not in workflows_markdown
    assert "src.cli" not in workflows_markdown

    payload = json.loads(context.context_json_path.read_text(encoding="utf-8"))
    assert "cli" not in payload
    assert "workflows" in payload
    assert "commands" not in payload["generated_docs"]
    assert payload["generated_docs"]["workflows"] == ".focus/WORKFLOWS.md"
    assert payload["acceptance"]["default_verification_profile"] == "focus.smoke"


def test_load_focus_context_exposes_workflow_metadata() -> None:
    context = load_focus_context(_repo_root())

    assert context.manifest.workflow.runtime_module == "src.main.main"
    assert context.manifest.workflow.backtest_module == "src.backtesting.main"
    assert context.manifest.acceptance.default_verification_profile == "focus.smoke"
