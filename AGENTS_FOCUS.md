# AGENTS_FOCUS.md

This document defines the current agent-first workflow for this repository.

It does not replace `AGENTS.md`. `AGENTS.md` remains the policy file for worktrees, merge rules, deployment verification, and cleanup.

## Default Workflow

The default loop is:

1. Read `strategy_spec.toml`.
2. Read `.focus/context.json`.
3. Stay inside the editable surface unless there is a concrete reason to expand.
4. Refresh generated focus assets when workflow intent, pack scope, or shared navigation changes.
5. Run verification in this order:
   - `focus.smoke`
   - `focus.full` only when the smoke profile is insufficient
   - runtime or backtest workflows only when the task truly needs execution evidence

The repository no longer relies on an installable command-line wrapper. Treat the focus manifest and generated assets as the source for module-level runtime and verification entrypoints.

## Source Of Truth

Use these assets in order:

1. `strategy_spec.toml`
2. `.focus/context.json`
3. `.focus/SYSTEM_MAP.md`
4. `.focus/TASK_BRIEF.md`
5. `.focus/WORKFLOWS.md`
6. `.focus/TASK_ROUTER.md`
7. `.focus/TEST_MATRIX.md`
8. `tests/TEST.md`
9. `artifacts/validation/latest.json`

If generated assets drift from the spec, update the generator/source layer and refresh the agent assets instead of hand-maintaining the generated files.

## Editing Boundaries

- `editable`
  - default edit surface
- `reference`
  - context only unless the task truly requires expansion
- `frozen`
  - do not edit unless the task is explicitly about repository policy or asset generation

When you must expand scope:

1. Explain why the editable surface is insufficient.
2. Expand by the smallest possible step.
3. Record the expansion in the delivery summary.

## Verification Profiles

- `focus.smoke`
  - default verification profile
  - runs the current focus selectors with the smoke keyword filter
- `focus.full`
  - full runnable selector set for the current focus
- `runtime`
  - use only for runtime lifecycle or monitoring work
- `backtest`
  - use only when behavior or parameter effects need execution evidence

Structured evidence is written to `artifacts/validation/latest.json` and other refreshed asset files. Do not claim completion from code inspection alone.

## Anti-Patterns

Do not:

- bypass `strategy_spec.toml` when changing intent or pack scope
- hand-edit generated `.focus/*` files unless the task is about the generator
- widen scope without a concrete reason
- reintroduce command-wrapper abstractions around runtime or verification flows
- move domain or infrastructure responsibilities into generic coordinators

## Delivery Checklist

Every delivery should state:

1. which source-of-truth assets were consulted
2. which surface was edited
3. which verification profiles or execution workflows ran
4. whether `tests/TEST.md` or `artifacts/*/latest.json` changed
5. any remaining risks or skipped checks
