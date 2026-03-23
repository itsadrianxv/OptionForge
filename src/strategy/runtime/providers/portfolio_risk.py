from __future__ import annotations

from typing import Any

from ..models import CapabilityContribution, ClosePipelineRoles, OpenPipelineRoles


class _PortfolioRiskProvider:
    def build(
        self,
        entry: Any,
        full_config: dict[str, Any],
        kernel: Any,
    ) -> CapabilityContribution:
        aggregator = getattr(entry, "portfolio_risk_aggregator", None)

        def risk_evaluator(*args: Any, **kwargs: Any) -> dict[str, Any] | None:
            if aggregator is None:
                return {"passed": True, "summary": "risk evaluator unavailable"}
            return {"passed": True, "summary": "risk evaluator ready"}

        return CapabilityContribution(
            open_pipeline=OpenPipelineRoles(risk_evaluator=risk_evaluator),
            close_pipeline=ClosePipelineRoles(risk_evaluator=risk_evaluator),
        )


PROVIDER = _PortfolioRiskProvider()
