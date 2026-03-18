from __future__ import annotations

from pathlib import Path
import importlib.util
from typing import Any

import pytest


SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "generate_workflow_docs.py"
)


def load_script_module() -> Any:
    spec = importlib.util.spec_from_file_location(
        "visualizing_strategy_workflows.generate_workflow_docs",
        SCRIPT_PATH,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_discover_workflow_files_honors_explicit_application_dir(tmp_path: Path) -> None:
    explicit_app_dir = tmp_path / "src" / "custom_application"
    fallback_app_dir = tmp_path / "src" / "strategy" / "application"
    explicit_app_dir.mkdir(parents=True)
    fallback_app_dir.mkdir(parents=True)

    explicit_workflow = explicit_app_dir / "alpha_workflow.py"
    explicit_workflow.write_text("class AlphaWorkflow:\n    pass\n", encoding="utf-8")
    (explicit_app_dir / "helper.py").write_text("pass\n", encoding="utf-8")
    (explicit_app_dir / "event_bridge.py").write_text("pass\n", encoding="utf-8")
    fallback_workflow = fallback_app_dir / "beta_workflow.py"
    fallback_workflow.write_text("class BetaWorkflow:\n    pass\n", encoding="utf-8")

    module = load_script_module()

    discovered = module.discover_workflow_files(
        project_root=tmp_path,
        application_dir=explicit_app_dir,
        workflow_pattern="*_workflow.py",
    )

    assert discovered == [explicit_workflow]


def test_scaffold_outputs_use_standardized_names(tmp_path: Path) -> None:
    application_dir = tmp_path / "src" / "strategy" / "application"
    application_dir.mkdir(parents=True)
    workflow_file = application_dir / "market_workflow.py"
    workflow_file.write_text("class MarketWorkflow:\n    pass\n", encoding="utf-8")

    module = load_script_module()

    generated = module.scaffold_workflow_docs(
        project_root=tmp_path,
        docs_root=tmp_path / "docs",
        workflow_files=[workflow_file],
    )

    assert len(generated) == 1
    outputs = generated[0]
    assert outputs.slug == "market-workflow"
    assert outputs.markdown_path == tmp_path / "docs" / "workflows" / "market-workflow.md"
    assert outputs.architecture_puml_path == tmp_path / "docs" / "plantuml" / "code" / "market-workflow-architecture.puml"
    assert outputs.data_flow_puml_path == tmp_path / "docs" / "plantuml" / "code" / "market-workflow-data-flow.puml"
    assert outputs.sequence_puml_path == tmp_path / "docs" / "plantuml" / "code" / "market-workflow-sequence.puml"
    assert outputs.architecture_svg_path == tmp_path / "docs" / "plantuml" / "chart" / "market-workflow-architecture.svg"
    assert outputs.data_flow_svg_path == tmp_path / "docs" / "plantuml" / "chart" / "market-workflow-data-flow.svg"
    assert outputs.sequence_svg_path == tmp_path / "docs" / "plantuml" / "chart" / "market-workflow-sequence.svg"
    assert outputs.state_puml_path == tmp_path / "docs" / "plantuml" / "code" / "market-workflow-state.puml"
    assert outputs.state_svg_path == tmp_path / "docs" / "plantuml" / "chart" / "market-workflow-state.svg"

    assert outputs.markdown_path.exists()
    assert outputs.architecture_puml_path.exists()
    assert outputs.data_flow_puml_path.exists()
    assert outputs.sequence_puml_path.exists()
    assert not outputs.state_puml_path.exists()


def test_markdown_scaffold_uses_first_public_method_when_no_on_hook_exists(tmp_path: Path) -> None:
    application_dir = tmp_path / "src" / "strategy" / "application"
    application_dir.mkdir(parents=True)
    workflow_file = application_dir / "subscription_workflow.py"
    workflow_file.write_text(
        (
            "class SubscriptionWorkflow:\n"
            "    def __init__(self, entry):\n"
            "        self.entry = entry\n\n"
            "    def init_subscription_management(self):\n"
            "        return None\n"
        ),
        encoding="utf-8",
    )

    module = load_script_module()
    generated = module.scaffold_workflow_docs(
        project_root=tmp_path,
        docs_root=tmp_path / "docs",
        workflow_files=[workflow_file],
    )

    markdown = generated[0].markdown_path.read_text(encoding="utf-8")
    assert "- Primary entrypoint: `SubscriptionWorkflow.init_subscription_management`" in markdown


def test_render_generated_diagrams_calls_plantuml_with_output_dir(tmp_path: Path) -> None:
    code_dir = tmp_path / "docs" / "plantuml" / "code"
    chart_dir = tmp_path / "docs" / "plantuml" / "chart"
    code_dir.mkdir(parents=True)
    chart_dir.mkdir(parents=True)

    first = code_dir / "lifecycle-workflow-architecture.puml"
    second = code_dir / "lifecycle-workflow-sequence.puml"
    first.write_text("@startuml\n@enduml\n", encoding="utf-8")
    second.write_text("@startuml\n@enduml\n", encoding="utf-8")

    calls: list[list[str]] = []

    def fake_runner(command: list[str], **_: Any) -> None:
        calls.append(command)

    module = load_script_module()
    module.render_plantuml_sources(
        source_files=[first, second],
        chart_dir=chart_dir,
        runner=fake_runner,
    )

    assert calls == [
        ["plantuml", "-tsvg", "-o", str(chart_dir), str(first)],
        ["plantuml", "-tsvg", "-o", str(chart_dir), str(second)],
    ]
