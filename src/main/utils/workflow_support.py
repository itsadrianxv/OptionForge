from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
import json
from pathlib import Path
import sys
from typing import Any

from dotenv import load_dotenv


@dataclass(frozen=True)
class CheckResult:
    status: str
    title: str
    detail: str


def get_project_root() -> Path:
    return Path(__file__).resolve().parents[3]


def resolve_project_path(path: str | Path, *, repo_root: Path | None = None) -> Path:
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate
    return (repo_root or get_project_root()) / candidate


def display_path(path: str | Path, *, repo_root: Path | None = None) -> str:
    candidate = Path(path)
    root = repo_root or get_project_root()
    try:
        return candidate.resolve().relative_to(root.resolve()).as_posix()
    except Exception:
        return candidate.as_posix()


def ensure_project_root_on_path(repo_root: Path | None = None) -> None:
    project_root = str(repo_root or get_project_root())
    if project_root not in sys.path:
        sys.path.insert(0, project_root)


def load_project_dotenv(repo_root: Path | None = None) -> Path | None:
    root = repo_root or get_project_root()
    env_path = root / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path, override=False)
        return env_path

    load_dotenv(override=False)
    return None


def build_artifact(
    path: str | Path,
    *,
    label: str | None = None,
    kind: str = "file",
    repo_root: Path | None = None,
) -> dict[str, str]:
    rendered_path = display_path(path, repo_root=repo_root)
    return {
        "path": rendered_path,
        "label": label or rendered_path,
        "kind": kind,
    }


def build_error(message: str, *, error_type: str = "error") -> dict[str, str]:
    return {
        "type": error_type,
        "message": message,
    }


def _json_default(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if is_dataclass(value):
        return asdict(value)
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def to_json_text(payload: Mapping[str, Any] | Sequence[Any] | Any) -> str:
    return json.dumps(payload, ensure_ascii=False, default=_json_default)


def write_json_file(path: Path, payload: Mapping[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, default=_json_default) + "\n",
        encoding="utf-8",
    )
    return path


def utc_now_iso() -> str:
    return datetime.now(tz=UTC).isoformat()


def write_verification_artifact(
    category: str,
    *,
    ok: bool,
    workflow: str,
    started_at: str,
    finished_at: str,
    inputs: Mapping[str, Any],
    summary: Mapping[str, Any] | None = None,
    artifacts: Sequence[Mapping[str, Any]] = (),
    errors: Sequence[Mapping[str, Any]] = (),
    repo_root: Path | None = None,
) -> Path:
    root = repo_root or get_project_root()
    target = root / "artifacts" / category / "latest.json"
    payload = {
        "ok": ok,
        "workflow": workflow,
        "started_at": started_at,
        "finished_at": finished_at,
        "inputs": dict(inputs),
        "summary": dict(summary or {}),
        "artifacts": [dict(item) for item in artifacts],
        "errors": [dict(item) for item in errors],
    }
    return write_json_file(target, payload)
