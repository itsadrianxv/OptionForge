from __future__ import annotations

from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def test_ddd_guardrail_docs_and_skills_exist() -> None:
    repo_root = _repo_root()
    agents_text = (repo_root / "AGENTS.md").read_text(encoding="utf-8")

    assert (repo_root / "docs" / "architecture" / "ddd-constitution.md").exists()
    assert (repo_root / "docs" / "architecture" / "context-map.md").exists()
    assert (repo_root / "docs" / "architecture" / "refactor-catalog.md").exists()
    assert (repo_root / ".codex" / "skills" / "ddd-coding-guard" / "SKILL.md").exists()
    assert (repo_root / ".codex" / "skills" / "ddd-refactor-coach" / "SKILL.md").exists()
    assert "ddd-coding-guard" in agents_text
    assert "ddd-refactor-coach" in agents_text
    assert "src/strategy/**" in agents_text


def test_ddd_guardrail_prompt_eval_suite_uses_real_repository_smells() -> None:
    repo_root = _repo_root()
    cases_dir = repo_root / "tests" / "agent-skills" / "cases"
    rubrics_dir = repo_root / "tests" / "agent-skills" / "rubrics"

    case_names = sorted(path.name for path in cases_dir.glob("*.md"))

    assert 6 <= len(case_names) <= 8
    assert "coding-guard-domain-infra-leak.md" in case_names
    assert "coding-guard-gateway-business-rule.md" in case_names
    assert "coding-guard-scaffold-stateful-service.md" in case_names
    assert "refactor-coach-domain-infra-leak.md" in case_names
    assert "refactor-coach-strategy-entry-bloat.md" in case_names
    assert "refactor-coach-refuse-big-bang.md" in case_names
    assert (rubrics_dir / "trigger-correctness.md").exists()
    assert (rubrics_dir / "boundary-judgment.md").exists()
    assert (rubrics_dir / "intervention-quality.md").exists()
    assert (rubrics_dir / "migration-quality.md").exists()
