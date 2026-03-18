# Lifecycle Workflow

- Source: `src/strategy/application/lifecycle_workflow.py`
- Primary entrypoint: `LifecycleWorkflow.on_init`

## Responsibility

`LifecycleWorkflow` bootstraps the strategy host from configuration into a runnable process. It assembles services and infrastructure, restores or warms runtime state, and owns the transition from construction to running and finally to shutdown.

## Architecture

![Lifecycle Workflow architecture](../plantuml/chart/lifecycle-workflow-architecture.svg)

## Data Flow

![Lifecycle Workflow data flow](../plantuml/chart/lifecycle-workflow-data-flow.svg)

## Sequence

![Lifecycle Workflow sequence](../plantuml/chart/lifecycle-workflow-sequence.svg)

## State

![Lifecycle Workflow state](../plantuml/chart/lifecycle-workflow-state.svg)

## Notes

- Key collaborators: `ConfigLoader`, subscription workflow delegation, domain services, gateways, persistence stack, monitor, bar pipeline, Feishu alert handler.
- Inputs: `entry.setting`, strategy TOML files, persisted snapshots, OMS state, historical bars.
- Outputs: initialized services and gateways, restored aggregates, warmed strategy state, registered alerts, saved snapshot on shutdown.
