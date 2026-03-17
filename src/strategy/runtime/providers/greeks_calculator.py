from __future__ import annotations

from typing import Any

from src.strategy.domain.value_object.pricing.greeks import GreeksInput

from ..models import CapabilityContribution, OpenPipelineRoles


def _chain_entry(option_chain: Any, selected_contract: Any) -> Any | None:
    return next(
        (
            item
            for item in getattr(option_chain, "entries", ())
            if item.contract.vt_symbol == selected_contract.vt_symbol
        ),
        None,
    )


class _GreeksCalculatorProvider:
    def build(
        self,
        entry: Any,
        full_config: dict[str, Any],
        kernel: Any,
    ) -> CapabilityContribution:
        calculator = getattr(entry, "greeks_calculator", None)
        if calculator is None:
            return CapabilityContribution()

        def greeks_enricher(option_chain: Any, selected_contract: Any) -> Any | None:
            chain_entry = _chain_entry(option_chain, selected_contract)
            if chain_entry is None:
                return None
            implied_volatility = chain_entry.quote.implied_volatility
            if implied_volatility is None or implied_volatility <= 0:
                return None
            return calculator.calculate_greeks(
                GreeksInput(
                    spot_price=option_chain.underlying_price,
                    strike_price=chain_entry.contract.strike_price,
                    time_to_expiry=max(chain_entry.contract.days_to_expiry, 1) / 365.0,
                    risk_free_rate=float(getattr(entry, "risk_free_rate", 0.02) or 0.02),
                    volatility=implied_volatility,
                    option_type=chain_entry.contract.option_type,
                )
            )

        return CapabilityContribution(
            open_pipeline=OpenPipelineRoles(greeks_enricher=greeks_enricher)
        )


PROVIDER = _GreeksCalculatorProvider()
