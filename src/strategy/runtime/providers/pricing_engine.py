from __future__ import annotations

from typing import Any

from src.strategy.domain.value_object.pricing.pricing import ExerciseStyle, PricingInput

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


class _PricingEngineProvider:
    def build(
        self,
        entry: Any,
        full_config: dict[str, Any],
        kernel: Any,
    ) -> CapabilityContribution:
        engine = getattr(entry, "pricing_engine", None)
        if engine is None:
            return CapabilityContribution()

        def pricing_enricher(option_chain: Any, selected_contract: Any, greeks_result: Any | None = None) -> dict[str, Any] | None:
            chain_entry = _chain_entry(option_chain, selected_contract)
            if chain_entry is None:
                return None
            implied_volatility = chain_entry.quote.implied_volatility
            if implied_volatility is None or implied_volatility <= 0:
                return None

            pricing_result = engine.price(
                PricingInput(
                    spot_price=option_chain.underlying_price,
                    strike_price=chain_entry.contract.strike_price,
                    time_to_expiry=max(chain_entry.contract.days_to_expiry, 1) / 365.0,
                    risk_free_rate=float(getattr(entry, "risk_free_rate", 0.02) or 0.02),
                    volatility=implied_volatility,
                    option_type=chain_entry.contract.option_type,
                    exercise_style=ExerciseStyle.AMERICAN,
                )
            )

            return {
                "quote_last_price": chain_entry.quote.last_price,
                "quote_bid_price": chain_entry.quote.bid_price,
                "quote_ask_price": chain_entry.quote.ask_price,
                "implied_volatility": implied_volatility,
                "theoretical_price": getattr(pricing_result, "price", None),
                "pricing_model": getattr(pricing_result, "model_used", ""),
                "delta": getattr(greeks_result, "delta", None),
                "gamma": getattr(greeks_result, "gamma", None),
                "theta": getattr(greeks_result, "theta", None),
                "vega": getattr(greeks_result, "vega", None),
            }

        return CapabilityContribution(
            open_pipeline=OpenPipelineRoles(pricing_enricher=pricing_enricher)
        )


PROVIDER = _PricingEngineProvider()
