# OptionForge

An option strategy scaffold built for coding agents.

This repository now centers on template reuse and agent assets rather than an installable command wrapper. The goal is to keep strategy intent, editable boundaries, and verification evidence explicit so an agent can modify the existing codebase directly.

## Core Assets

- `strategy_spec.toml`
  - intent and acceptance source of truth
- `focus/strategies/*/strategy.manifest.toml`
  - pack, surface, and workflow metadata
- `.focus/context.json`
  - machine-readable current-context contract
- `.focus/SYSTEM_MAP.md`
- `.focus/ACTIVE_SURFACE.md`
- `.focus/TASK_BRIEF.md`
- `.focus/WORKFLOWS.md`
- `.focus/TASK_ROUTER.md`
- `.focus/TEST_MATRIX.md`
- `tests/TEST.md`
  - current strategy verification summary
- `artifacts/validation/latest.json`
  - latest validation artifact

## Default Workflow

1. Read `strategy_spec.toml` and `.focus/context.json`.
2. Edit inside the current editable surface.
3. Refresh focus assets when workflow intent or pack scope changes.
4. Run `focus.smoke` first.
5. Expand to `focus.full`, runtime, or backtest only when the task actually needs that evidence.

## Runtime And Verification Semantics

The `[workflow]` section in `focus/strategies/main/strategy.manifest.toml` defines the current module-level entrypoints:

- `runtime_module`
- `backtest_module`
- `monitor_script`

The `[acceptance]` section defines the default verification profile, selectors, key logs, and key outputs for the current strategy.

## Layout

- `src/main`
  - runtime assembly, focus assets, validation services
- `src/backtesting`
  - backtest config and execution
- `src/strategy`
  - application, domain, infrastructure, and runtime providers
- `src/web`
  - read-only monitoring UI
- `focus`
  - pack and strategy manifests
- `.focus`
  - generated navigation assets
- `tests`
  - strategy, focus, validation, and runtime tests
- `deploy`
  - deploy-main workflow and container deployment entrypoint

## Docs

- `AGENTS.md`
  - repository policy
- `AGENTS_FOCUS.md`
  - agent-first reading, editing, and verification rules
- `docs/slides/OptionForge-internal-share.html`
  - current internal deck

## License

This project is licensed under [GNU Affero General Public License v3.0](LICENSE).
