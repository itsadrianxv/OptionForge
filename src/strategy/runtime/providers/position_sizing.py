from __future__ import annotations

from typing import Any

from src.strategy.domain.value_object.risk import PortfolioGreeks

from ..models import CapabilityContribution, ClosePipelineRoles, OpenPipelineRoles


class _PositionSizingProvider:
    def build(
        self,
        entry: Any,
        full_config: dict[str, Any],
        kernel: Any,
    ) -> CapabilityContribution:
        service = getattr(entry, "position_sizing_service", None)
        if service is None:
            return CapabilityContribution()

        def sizing_evaluator(option_chain: Any, selected_contract: Any, greeks_result: Any | None) -> dict[str, Any] | None:
            account_gateway = getattr(entry, "account_gateway", None)
            market_gateway = getattr(entry, "market_gateway", None)
            if account_gateway is None or market_gateway is None or greeks_result is None:
                return None

            account = account_gateway.get_account_snapshot()
            if account is None:
                return None

            contract = market_gateway.get_contract(selected_contract.vt_symbol)
            multiplier = float(getattr(contract, "size", 1) or 1)
            price = max(
                float(getattr(selected_contract, "bid_price", 0.0) or 0.0),
                float(getattr(selected_contract, "ask_price", 0.0) or 0.0),
                0.0,
            )
            if price <= 0:
                return None

            sizing = service.compute_sizing(
                account_balance=float(account.available),
                total_equity=float(account.balance),
                used_margin=max(float(account.balance) - float(account.available), 0.0),
                contract_price=price,
                underlying_price=option_chain.underlying_price,
                strike_price=selected_contract.strike_price,
                option_type=selected_contract.option_type,
                multiplier=multiplier,
                greeks=greeks_result,
                portfolio_greeks=PortfolioGreeks(),
                risk_thresholds=getattr(entry, "risk_thresholds", None),
            )
            return {
                "passed": sizing.passed,
                "final_volume": sizing.final_volume,
                "margin_volume": sizing.margin_volume,
                "usage_volume": sizing.usage_volume,
                "greeks_volume": sizing.greeks_volume,
                "reject_reason": sizing.reject_reason,
                "summary": "浠撲綅璇勪及閫氳繃" if sizing.passed else (sizing.reject_reason or "浠撲綅璇勪及鎷掔粷"),
            }

        def close_volume_planner(position: Any) -> dict[str, Any] | None:
            market_gateway = getattr(entry, "market_gateway", None)
            close_price = 0.0
            if market_gateway is not None:
                tick = market_gateway.get_tick(getattr(position, "vt_symbol", ""))
                close_price = float(getattr(tick, "last_price", 0.0) or 0.0) if tick else 0.0
            if close_price <= 0:
                close_price = float(getattr(position, "open_price", 0.0) or 0.0)

            instruction = service.calculate_close_volume(
                position=position,
                close_price=close_price,
                signal="close_pipeline_plan",
            )
            if instruction is None:
                return None
            return {
                "vt_symbol": instruction.vt_symbol,
                "direction": instruction.direction.value,
                "offset": instruction.offset.value,
                "volume": instruction.volume,
                "price": instruction.price,
            }

        return CapabilityContribution(
            open_pipeline=OpenPipelineRoles(sizing_evaluator=sizing_evaluator),
            close_pipeline=ClosePipelineRoles(close_volume_planner=close_volume_planner),
        )


PROVIDER = _PositionSizingProvider()
