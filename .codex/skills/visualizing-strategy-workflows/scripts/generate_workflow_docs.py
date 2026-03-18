#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
from pathlib import Path
import subprocess
import sys
from typing import Callable, Iterable, NamedTuple, Sequence


DEFAULT_APPLICATION_DIRS = (
    Path("src/application"),
    Path("src/strategy/application"),
)

MANDATORY_DIAGRAM_TYPES = ("architecture", "data-flow", "sequence")


class WorkflowArtifacts(NamedTuple):
    workflow_path: Path
    slug: str
    markdown_path: Path
    architecture_puml_path: Path
    data_flow_puml_path: Path
    sequence_puml_path: Path
    state_puml_path: Path
    architecture_svg_path: Path
    data_flow_svg_path: Path
    sequence_svg_path: Path
    state_svg_path: Path


def resolve_application_dir(project_root: Path, application_dir: Path | None = None) -> Path:
    if application_dir is not None:
        resolved = application_dir if application_dir.is_absolute() else project_root / application_dir
        if not resolved.exists():
            raise FileNotFoundError(f"Application directory not found: {resolved}")
        return resolved

    for candidate in DEFAULT_APPLICATION_DIRS:
        resolved = project_root / candidate
        if resolved.exists():
            return resolved

    searched = ", ".join(str(path) for path in DEFAULT_APPLICATION_DIRS)
    raise FileNotFoundError(f"Could not find an application directory under: {searched}")


def discover_workflow_files(
    project_root: Path,
    application_dir: Path | None = None,
    workflow_pattern: str = "*_workflow.py",
) -> list[Path]:
    resolved_dir = resolve_application_dir(project_root, application_dir)
    return sorted(
        path
        for path in resolved_dir.rglob(workflow_pattern)
        if path.is_file() and path.suffix == ".py"
    )


def slugify_workflow(workflow_path: Path) -> str:
    return workflow_path.stem.replace("_", "-")


def build_workflow_artifacts(workflow_path: Path, docs_root: Path) -> WorkflowArtifacts:
    slug = slugify_workflow(workflow_path)
    workflows_dir = docs_root / "workflows"
    plantuml_code_dir = docs_root / "plantuml" / "code"
    plantuml_chart_dir = docs_root / "plantuml" / "chart"
    return WorkflowArtifacts(
        workflow_path=workflow_path,
        slug=slug,
        markdown_path=workflows_dir / f"{slug}.md",
        architecture_puml_path=plantuml_code_dir / f"{slug}-architecture.puml",
        data_flow_puml_path=plantuml_code_dir / f"{slug}-data-flow.puml",
        sequence_puml_path=plantuml_code_dir / f"{slug}-sequence.puml",
        state_puml_path=plantuml_code_dir / f"{slug}-state.puml",
        architecture_svg_path=plantuml_chart_dir / f"{slug}-architecture.svg",
        data_flow_svg_path=plantuml_chart_dir / f"{slug}-data-flow.svg",
        sequence_svg_path=plantuml_chart_dir / f"{slug}-sequence.svg",
        state_svg_path=plantuml_chart_dir / f"{slug}-state.svg",
    )


def ensure_parent_dirs(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def extract_primary_entrypoint(workflow_path: Path) -> str:
    source = workflow_path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(workflow_path))
    class_nodes = [node for node in tree.body if isinstance(node, ast.ClassDef)]
    if not class_nodes:
        return workflow_path.stem

    workflow_class = class_nodes[0]
    for node in workflow_class.body:
        if isinstance(node, ast.FunctionDef) and node.name.startswith("on_"):
            return f"{workflow_class.name}.{node.name}"
    for node in workflow_class.body:
        if isinstance(node, ast.FunctionDef) and not node.name.startswith("_"):
            return f"{workflow_class.name}.{node.name}"
    return workflow_class.name


def write_if_missing(path: Path, content: str) -> None:
    ensure_parent_dirs(path)
    if not path.exists():
        path.write_text(content, encoding="utf-8")


def render_markdown_skeleton(project_root: Path, artifacts: WorkflowArtifacts) -> str:
    title = artifacts.workflow_path.stem.replace("_", " ").title()
    source_rel = artifacts.workflow_path.relative_to(project_root).as_posix()
    entrypoint = extract_primary_entrypoint(artifacts.workflow_path)
    chart_rel = Path("..") / "plantuml" / "chart"
    architecture_rel = (chart_rel / artifacts.architecture_svg_path.name).as_posix()
    data_flow_rel = (chart_rel / artifacts.data_flow_svg_path.name).as_posix()
    sequence_rel = (chart_rel / artifacts.sequence_svg_path.name).as_posix()
    return f"""# {title}

- Source: `{source_rel}`
- Primary entrypoint: `{entrypoint}`

## Responsibility

TODO: Summarize what this workflow orchestrates in 2-4 short sentences.

## Architecture

![{title} architecture]({architecture_rel})

## Data Flow

![{title} data flow]({data_flow_rel})

## Sequence

![{title} sequence]({sequence_rel})

## Notes

- Key collaborators: TODO
- Inputs: TODO
- Outputs: TODO

<!-- Add a state diagram only when the workflow has meaningful state or mode transitions.
![{title} state]({(chart_rel / artifacts.state_svg_path.name).as_posix()})
-->
"""


def render_architecture_template(artifacts: WorkflowArtifacts) -> str:
    title = artifacts.workflow_path.stem.replace("_", " ").title()
    workflow_name = artifacts.workflow_path.stem.replace("_", " ").title()
    return f"""@startuml
title {title} - Architecture
skinparam shadowing false
skinparam componentStyle rectangle

package "Workflow" {{
  component "{workflow_name}" as workflow
}}

package "Collaborators" {{
  component "TODO: add key collaborator" as collaborator
}}

workflow --> collaborator : TODO
@enduml
"""


def render_data_flow_template(artifacts: WorkflowArtifacts) -> str:
    title = artifacts.workflow_path.stem.replace("_", " ").title()
    workflow_name = artifacts.workflow_path.stem.replace("_", " ").title()
    return f"""@startuml
title {title} - Data Flow
skinparam shadowing false

rectangle "Input\\nTODO" as input
rectangle "{workflow_name}" as workflow
rectangle "Output\\nTODO" as output

input --> workflow : TODO
workflow --> output : TODO
@enduml
"""


def render_sequence_template(artifacts: WorkflowArtifacts) -> str:
    title = artifacts.workflow_path.stem.replace("_", " ").title()
    workflow_name = artifacts.workflow_path.stem.replace("_", " ").title()
    return f"""@startuml
title {title} - Sequence
autonumber

participant "Caller" as caller
participant "{workflow_name}" as workflow
participant "TODO collaborator" as collaborator

caller -> workflow : TODO entrypoint
workflow -> collaborator : TODO
collaborator --> workflow : TODO
workflow --> caller : TODO result
@enduml
"""


def scaffold_workflow_docs(
    project_root: Path,
    docs_root: Path,
    workflow_files: Sequence[Path],
) -> list[WorkflowArtifacts]:
    resolved_docs_root = docs_root if docs_root.is_absolute() else project_root / docs_root
    artifacts_list: list[WorkflowArtifacts] = []

    for workflow_file in workflow_files:
        artifacts = build_workflow_artifacts(workflow_file, resolved_docs_root)
        artifacts_list.append(artifacts)
        write_if_missing(artifacts.markdown_path, render_markdown_skeleton(project_root, artifacts))
        write_if_missing(artifacts.architecture_puml_path, render_architecture_template(artifacts))
        write_if_missing(artifacts.data_flow_puml_path, render_data_flow_template(artifacts))
        write_if_missing(artifacts.sequence_puml_path, render_sequence_template(artifacts))

    return artifacts_list


def iter_renderable_sources(artifacts_list: Iterable[WorkflowArtifacts]) -> list[Path]:
    source_files: list[Path] = []
    for artifacts in artifacts_list:
        source_files.extend(
            [
                artifacts.architecture_puml_path,
                artifacts.data_flow_puml_path,
                artifacts.sequence_puml_path,
            ]
        )
        if artifacts.state_puml_path.exists():
            source_files.append(artifacts.state_puml_path)
    return source_files


def render_plantuml_sources(
    source_files: Sequence[Path],
    chart_dir: Path,
    runner: Callable[..., object] | None = None,
) -> None:
    chart_dir.mkdir(parents=True, exist_ok=True)
    run = runner or subprocess.run
    for source_file in source_files:
        run(
            ["plantuml", "-tsvg", "-o", str(chart_dir), str(source_file)],
            check=True,
        )


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scaffold and optionally render workflow visualization docs.",
    )
    parser.add_argument("--project-root", required=True, help="Repository root")
    parser.add_argument(
        "--application-dir",
        help="Explicit application directory override",
    )
    parser.add_argument(
        "--docs-root",
        default="docs",
        help="Documentation root relative to project root",
    )
    parser.add_argument(
        "--workflow-pattern",
        default="*_workflow.py",
        help="File glob used to detect workflow files",
    )
    parser.add_argument(
        "--render",
        action="store_true",
        help="Render discovered PlantUML sources to SVG",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    project_root = Path(args.project_root).resolve()
    application_dir = Path(args.application_dir) if args.application_dir else None
    docs_root = Path(args.docs_root)

    workflow_files = discover_workflow_files(
        project_root=project_root,
        application_dir=application_dir,
        workflow_pattern=args.workflow_pattern,
    )
    if not workflow_files:
        raise FileNotFoundError("No workflow files matched the requested pattern.")

    artifacts_list = scaffold_workflow_docs(
        project_root=project_root,
        docs_root=docs_root,
        workflow_files=workflow_files,
    )

    if args.render:
        resolved_docs_root = docs_root if docs_root.is_absolute() else project_root / docs_root
        render_plantuml_sources(
            source_files=iter_renderable_sources(artifacts_list),
            chart_dir=resolved_docs_root / "plantuml" / "chart",
        )

    print(f"Generated workflow docs for {len(artifacts_list)} workflow file(s).")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1)
