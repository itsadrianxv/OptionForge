"""
IndicatorService - 鎸囨爣璁＄畻棰嗗煙鏈嶅姟锛堟ā鏉匡級

鏈枃浠舵槸妗嗘灦妯℃澘锛屾彁渚涙寚鏍囪绠楁湇鍔＄殑楠ㄦ灦缁撴瀯銆?
浣跨敤鏈ā鏉挎椂锛岃鏍规嵁浣犵殑绛栫暐闇€姹傚疄鐜板叿浣撶殑鎸囨爣璁＄畻閫昏緫銆?

鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺?
  寮€鍙戞寚鍗?
鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺?

1. 鏈被瀹炵幇 IIndicatorService 鎺ュ彛锛岃礋璐ｅ湪姣忔牴 K 绾垮埌杈炬椂璁＄畻鎶€鏈寚鏍囥€?

2. 璁＄畻缁撴灉搴斿啓鍏?instrument.indicators 瀛楀吀锛屼緥濡?
   - instrument.indicators['my_indicator'] = {'value': 42.0, 'signal': True}
   - 閿悕鍜屾暟鎹粨鏋勫畬鍏ㄧ敱浣犺嚜瀹氫箟锛屾鏋朵笉鍋氫换浣曠害鏉熴€?

3. 鍏稿瀷鐨勬寚鏍囪绠楁祦绋?
   a. 浠?instrument.bars (pd.DataFrame) 璇诲彇鍘嗗彶 K 绾挎暟鎹?
   b. 浣跨敤 pandas / numpy / ta-lib 绛夊簱璁＄畻鎸囨爣
   c. 灏嗙粨鏋滃啓鍏?instrument.indicators 瀛楀吀

4. 濡傛灉浣犵殑绛栫暐闇€瑕佸涓寚鏍囷紝寤鸿:
   - 鍦?calculation_service/ 鐩綍涓嬩负姣忎釜鎸囨爣鍒涘缓鐙珛鐨勮绠楁湇鍔?
   - 鍦ㄦ湰绫讳腑鍗忚皟璋冪敤鍚勮绠楁湇鍔?
   - 鎴栬€呯洿鎺ュ湪 calculate_bar() 涓疄鐜版墍鏈夎绠?

5. 鐩存帴鍦ㄦ湰鏂囦欢涓疄鐜颁綘鐨勬寚鏍囪绠楅€昏緫鍗冲彲
"""
from abc import ABC, abstractmethod
from typing import Optional, TYPE_CHECKING

from ...value_object.signal.strategy_contract import (
    IndicatorComputationResult,
    IndicatorContext,
)

if TYPE_CHECKING:
    from ...entity.target_instrument import TargetInstrument


class IIndicatorService(ABC):
    """鎸囨爣璁＄畻鏈嶅姟鎺ュ彛"""

    @abstractmethod
    def calculate_bar(
        self,
        instrument: "TargetInstrument",
        bar: dict,
        context: Optional[IndicatorContext] = None,
    ) -> IndicatorComputationResult:
        """K 绾挎洿鏂版椂鐨勬寚鏍囪绠楅€昏緫"""
        raise NotImplementedError


class IndicatorService(IIndicatorService):
    """
    鎸囨爣璁＄畻鏈嶅姟锛堟ā鏉匡級

    浣跨敤鏃惰鏍规嵁绛栫暐闇€姹?
    1. 淇濇寔鏈嶅姟鏃犵姸鎬侊紝涓嶈鍦ㄥ疄渚嬩笂淇濆瓨鍙彉閰嶇疆
    2. 鍦?calculate_bar() 涓疄鐜版寚鏍囪绠楅€昏緫
    3. 灏嗚绠楃粨鏋滃啓鍏?instrument.indicators 瀛楀吀
    """

    def calculate_bar(
        self,
        instrument: "TargetInstrument",
        bar: dict,
        context: Optional[IndicatorContext] = None,
    ) -> IndicatorComputationResult:
        """
        K 绾挎洿鏂版椂鐨勬寚鏍囪绠楅€昏緫

        TODO: 瀹炵幇浣犵殑鎸囨爣璁＄畻锛屼緥濡?
            bars = instrument.bars
            if len(bars) < 20:
                return

            close = bars['close']
            fast_ema = close.ewm(span=12, adjust=False).mean().iloc[-1]
            slow_ema = close.ewm(span=26, adjust=False).mean().iloc[-1]

            instrument.indicators['ema'] = {
                'fast': float(fast_ema),
                'slow': float(slow_ema),
            }

        Args:
            instrument: 鏍囩殑瀹炰綋锛屽寘鍚巻鍙?K 绾挎暟鎹?(instrument.bars)
            bar: 鏂?K 绾挎暟鎹瓧鍏?(datetime, open, high, low, close, volume)
        """
        summary = "鏈厤缃叿浣撴寚鏍囬€昏緫锛岃繑鍥炵┖鎸囨爣缁撴灉"
        instrument.indicators.setdefault("_contract", {})["indicator_service"] = {
            "service": type(self).__name__,
            "summary": summary,
            "last_bar_dt": bar.get("datetime"),
        }
        if context is not None:
            instrument.indicators["_contract"]["indicator_context"] = {
                "vt_symbol": context.vt_symbol,
                "underlying_price": context.underlying_price,
            }
        return IndicatorComputationResult.noop(summary=summary)

