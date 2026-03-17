from __future__ import annotations

from typing import Any

from src.strategy.domain.value_object.signal.strategy_contract import OptionSelectionPreference, SignalDecision

from ..models import CapabilityContribution, OpenPipelineRoles


class _OptionSelectorProvider:
    def build(
        self,
        entry: Any,
        full_config: dict[str, Any],
        kernel: Any,
    ) -> CapabilityContribution:
        service = getattr(entry, "option_selector_service", None)
        if service is None:
            return CapabilityContribution()

        def contract_selector(signal: SignalDecision, option_chain: Any) -> Any | None:
            preference = signal.selection_preference or OptionSelectionPreference(
                option_type="call",
                strike_level=getattr(entry, "strike_level", 1),
            )
            if preference.combination_type:
                logger = getattr(entry, "logger", None)
                if logger is not None:
                    logger.info(
                        f"缁勫悎鍋忓ソ {preference.combination_type} 宸茶瘑鍒紝褰撳墠楠ㄦ灦浠呰褰曞亸濂斤紝涓嶅浐鍖栧鑵挎墽琛?"
                    )
                return None

            option_type = preference.option_type or "call"
            if preference.target_delta is not None and hasattr(service, "select_by_delta_from_chain"):
                return service.select_by_delta_from_chain(
                    option_chain,
                    option_type=option_type,
                    target_delta=preference.target_delta,
                    greeks_data={},
                    log_func=getattr(getattr(entry, "logger", None), "info", None),
                )

            return service.select_option_from_chain(
                option_chain,
                option_type=option_type,
                strike_level=preference.strike_level or getattr(entry, "strike_level", 1),
                log_func=getattr(getattr(entry, "logger", None), "info", None),
            )

        return CapabilityContribution(
            open_pipeline=OpenPipelineRoles(contract_selector=contract_selector)
        )


PROVIDER = _OptionSelectorProvider()
