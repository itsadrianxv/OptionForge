from __future__ import annotations

from pathlib import Path
import re
import tomllib


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def test_repository_no_longer_exposes_cli_surface() -> None:
    repo_root = _repo_root()
    pyproject = tomllib.loads((repo_root / "pyproject.toml").read_text(encoding="utf-8"))
    requirements = (repo_root / "requirements.txt").read_text(encoding="utf-8").lower()

    assert "scripts" not in pyproject.get("project", {})
    assert "cli" not in [item.lower() for item in pyproject["project"]["keywords"]]
    assert not (repo_root / "src" / "cli").exists()
    assert "click==" not in requirements
    assert "typer==" not in requirements


def test_repository_assets_do_not_reference_removed_cli_tokens() -> None:
    repo_root = _repo_root()
    excluded_parts = {
        ".git",
        ".venv",
        "__pycache__",
        "temp",
        "artifacts",
        ".codex",
        ".claude",
    }
    excluded_files = {
        "tests/main/focus/test_agent_assets.py",
        "tests/main/test_cli_removal_contract.py",
    }
    patterns = (
        re.compile(r"python -m src\.cli\.app", re.IGNORECASE),
        re.compile(r"src[/\\]cli", re.IGNORECASE),
        re.compile(r"^\[cli\]$", re.IGNORECASE | re.MULTILINE),
        re.compile(r"cli_commands", re.IGNORECASE),
        re.compile(r"minimal_test_command", re.IGNORECASE),
        re.compile(r"\.focus/commands\.md", re.IGNORECASE),
        re.compile(r"\boptionforge\s+(create|init|forge|focus|validate|run|backtest|doctor|examples)\b", re.IGNORECASE),
    )

    matched_files: list[str] = []
    for path in repo_root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in excluded_parts for part in path.parts):
            continue
        if path.suffix.lower() not in {".md", ".toml", ".py", ".ps1", ".txt", ".json", ".html"}:
            continue
        if path.relative_to(repo_root).as_posix() in excluded_files:
            continue

        text = path.read_text(encoding="utf-8")
        if any(pattern.search(text) for pattern in patterns):
            matched_files.append(path.relative_to(repo_root).as_posix())

    assert matched_files == []
