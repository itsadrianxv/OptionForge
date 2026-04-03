# Agent Skill Eval Suite

This directory holds prompt-eval assets for the OptionsForge DDD guardrail skills.

## Goals

- keep the new skills grounded in real family code smells
- preserve RED/GREEN/REFACTOR evidence when the skills evolve
- make manual or semi-automated eval reruns cheap

## Layout

- `cases/*.md`: prompt fixtures and expected behavior
- `rubrics/*.md`: scoring guides
- `baselines/*.md`: RED-phase notes captured before the skills existed

## Current v1 Scope

The suite focuses on:
- domain-to-infrastructure leakage
- business-rule leakage into adapter-like code
- `StrategyEntry` / workflow bloat
- stateful scaffold-generated domain services
- refusal of big-bang refactors

## How To Use

1. Pick a case file.
2. Run the prompt in a Codex session against the repository.
3. Score the response with all rubric files.
4. Compare against the RED baseline notes if the skill behavior changes.

v1 is intentionally repo-local and mostly manual. The assets are structured so an automated harness can be added later without rewriting the cases.
