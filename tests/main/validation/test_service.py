from __future__ import annotations

import json
from pathlib import Path

from src.main.validation.service import collect_validation_results, write_verification_artifact


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def test_collect_validation_results_resolves_repo_relative_config() -> None:
    _, summary, artifacts, error_count, warning_count = collect_validation_results(
        repo_root=_repo_root(),
        config=Path("config/strategy_config.toml"),
    )

    assert summary["config"] == "config/strategy_config.toml"
    assert error_count >= 0
    assert warning_count >= 0
    assert artifacts


def test_write_verification_artifact_uses_workflow_field(tmp_path: Path) -> None:
    artifact_path = write_verification_artifact(
        "validation",
        ok=True,
        workflow="validation",
        started_at="2026-03-31T00:00:00+00:00",
        finished_at="2026-03-31T00:01:00+00:00",
        inputs={"config": "config/strategy_config.toml"},
        summary={"error_count": 0, "warning_count": 0},
        repo_root=tmp_path,
    )

    payload = json.loads(artifact_path.read_text(encoding="utf-8"))
    assert payload["workflow"] == "validation"
    assert "command" not in payload
    assert payload["ok"] is True
