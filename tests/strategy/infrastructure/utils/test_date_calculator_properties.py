"""
DateCalculator 属性测试

使用 Hypothesis 进行基于属性的测试，验证日期计算的正确性。
"""
from datetime import datetime, timedelta
from hypothesis import given, settings, strategies as st

from src.strategy.infrastructure.utils.date_calculator import DateCalculator


# ============================================================================
# Hypothesis 策略定义
# ============================================================================

@st.composite
def yymm_format_strategy(draw):
    """
    生成 YYMM 格式的到期日字符串
    """
    year = draw(st.integers(min_value=24, max_value=29))
    month = draw(st.integers(min_value=1, max_value=12))
    return f"{year:02d}{month:02d}"


@st.composite
def current_date_strategy(draw):
    """
    生成当前日期（2024-2029 年之间）
    """
    year = draw(st.integers(min_value=2024, max_value=2029))
    month = draw(st.integers(min_value=1, max_value=12))
    day = draw(st.integers(min_value=1, max_value=28))  # 使用 28 避免月份天数问题
    hour = draw(st.integers(min_value=0, max_value=23))
    minute = draw(st.integers(min_value=0, max_value=59))
    second = draw(st.integers(min_value=0, max_value=59))
    
    return datetime(year, month, day, hour, minute, second)


# ============================================================================
# 属性 6: 日期计算正确性
# ============================================================================

class TestDateCalculatorProperties:
    """
    **属性 6: 日期计算正确性**
    
    对于任何有效的 YYMM 格式到期日字符串和当前日期，
    DateCalculator.calculate_days_to_expiry 计算的天数应该等于手动计算的天数差
    （假设到期日为该月 15 日）。
    
    **验证需求: 4.2, 4.5**
    """
    
    @given(yymm_format_strategy(), current_date_strategy())
    @settings(max_examples=100)
    def test_calculate_days_matches_manual_calculation(self, expiry_str, current_date):
        """
        Feature: domain-service-infrastructure-refactoring, Property 6: 日期计算正确性
        
        **Validates: Requirements 4.2, 4.5**
        
        验证计算的天数与手动计算一致
        """
        # 使用 DateCalculator 计算
        calculated_days = DateCalculator.calculate_days_to_expiry(expiry_str, current_date)
        
        # 手动计算
        year = int(expiry_str[:2])
        month = int(expiry_str[2:])
        full_year = 2000 + year
        expiry_date = datetime(full_year, month, 15)
        expected_days = (expiry_date - current_date).days
        
        # 验证一致性
        assert calculated_days == expected_days, (
            f"计算的天数 {calculated_days} 与手动计算 {expected_days} 不一致，"
            f"到期日: {expiry_str}, 当前日期: {current_date}"
        )
    
    @given(yymm_format_strategy(), current_date_strategy())
    @settings(max_examples=100)
    def test_parse_expiry_date_returns_15th_of_month(self, expiry_str, current_date):
        """
        Feature: domain-service-infrastructure-refactoring, Property 6: 日期计算正确性
        
        **Validates: Requirements 4.2**
        
        验证解析的到期日是该月的 15 日
        """
        parsed_date = DateCalculator.parse_expiry_date(expiry_str)
        
        assert parsed_date is not None, f"解析失败: {expiry_str}"
        assert parsed_date.day == 15, (
            f"到期日应为 15 日，实际: {parsed_date.day}，"
            f"到期日字符串: {expiry_str}"
        )
        
        # 验证年月正确
        year = int(expiry_str[:2])
        month = int(expiry_str[2:])
        full_year = 2000 + year
        
        assert parsed_date.year == full_year, (
            f"年份应为 {full_year}，实际: {parsed_date.year}"
        )
        assert parsed_date.month == month, (
            f"月份应为 {month}，实际: {parsed_date.month}"
        )
    
    @given(yymm_format_strategy())
    @settings(max_examples=100)
    def test_parse_expiry_date_is_idempotent(self, expiry_str):
        """
        Feature: domain-service-infrastructure-refactoring, Property 6: 日期计算正确性
        
        **Validates: Requirements 4.2**
        
        验证多次解析返回相同结果（幂等性）
        """
        result1 = DateCalculator.parse_expiry_date(expiry_str)
        result2 = DateCalculator.parse_expiry_date(expiry_str)
        result3 = DateCalculator.parse_expiry_date(expiry_str)
        
        assert result1 == result2 == result3, (
            f"多次解析返回不同结果: {result1}, {result2}, {result3}，"
            f"到期日字符串: {expiry_str}"
        )
    
    @given(yymm_format_strategy(), current_date_strategy())
    @settings(max_examples=100)
    def test_calculate_days_is_idempotent(self, expiry_str, current_date):
        """
        Feature: domain-service-infrastructure-refactoring, Property 6: 日期计算正确性
        
        **Validates: Requirements 4.5**
        
        验证多次计算返回相同结果（幂等性）
        """
        result1 = DateCalculator.calculate_days_to_expiry(expiry_str, current_date)
        result2 = DateCalculator.calculate_days_to_expiry(expiry_str, current_date)
        result3 = DateCalculator.calculate_days_to_expiry(expiry_str, current_date)
        
        assert result1 == result2 == result3, (
            f"多次计算返回不同结果: {result1}, {result2}, {result3}，"
            f"到期日: {expiry_str}, 当前日期: {current_date}"
        )
    
    @given(yymm_format_strategy(), current_date_strategy())
    @settings(max_examples=100)
    def test_days_to_expiry_decreases_with_time(self, expiry_str, current_date):
        """
        Feature: domain-service-infrastructure-refactoring, Property 6: 日期计算正确性
        
        **Validates: Requirements 4.5**
        
        验证随着时间推移，距离到期天数递减
        """
        # 计算当前日期的距离到期天数
        days1 = DateCalculator.calculate_days_to_expiry(expiry_str, current_date)
        
        # 计算一天后的距离到期天数
        next_date = current_date + timedelta(days=1)
        days2 = DateCalculator.calculate_days_to_expiry(expiry_str, next_date)
        
        # 计算一周后的距离到期天数
        week_later = current_date + timedelta(days=7)
        days3 = DateCalculator.calculate_days_to_expiry(expiry_str, week_later)
        
        # 验证天数递减
        if days1 is not None and days2 is not None:
            assert days2 == days1 - 1, (
                f"一天后的天数应减少 1，实际: {days1} -> {days2}，"
                f"到期日: {expiry_str}, 当前日期: {current_date}"
            )
        
        if days1 is not None and days3 is not None:
            assert days3 == days1 - 7, (
                f"一周后的天数应减少 7，实际: {days1} -> {days3}，"
                f"到期日: {expiry_str}, 当前日期: {current_date}"
            )
    
    @given(yymm_format_strategy(), current_date_strategy())
    @settings(max_examples=100)
    def test_calculate_days_consistency_with_parse(self, expiry_str, current_date):
        """
        Feature: domain-service-infrastructure-refactoring, Property 6: 日期计算正确性
        
        **Validates: Requirements 4.2, 4.5**
        
        验证 calculate_days_to_expiry 与 parse_expiry_date 的一致性
        """
        # 使用 calculate_days_to_expiry
        calculated_days = DateCalculator.calculate_days_to_expiry(expiry_str, current_date)
        
        # 使用 parse_expiry_date 然后手动计算
        parsed_date = DateCalculator.parse_expiry_date(expiry_str)
        
        if parsed_date is not None:
            expected_days = (parsed_date - current_date).days
            
            assert calculated_days == expected_days, (
                f"calculate_days_to_expiry 与 parse_expiry_date 计算不一致，"
                f"calculated: {calculated_days}, expected: {expected_days}，"
                f"到期日: {expiry_str}, 当前日期: {current_date}"
            )
    
    @given(yymm_format_strategy())
    @settings(max_examples=100)
    def test_expiry_date_on_15th_gives_zero_days(self, expiry_str):
        """
        Feature: domain-service-infrastructure-refactoring, Property 6: 日期计算正确性
        
        **Validates: Requirements 4.5**
        
        验证当前日期为到期日时，返回 0 天
        """
        # 解析到期日
        expiry_date = DateCalculator.parse_expiry_date(expiry_str)
        
        if expiry_date is not None:
            # 使用到期日作为当前日期
            days = DateCalculator.calculate_days_to_expiry(expiry_str, expiry_date)
            
            assert days == 0, (
                f"到期日当天应返回 0 天，实际: {days}，"
                f"到期日: {expiry_str}, 日期: {expiry_date}"
            )
    
    @given(yymm_format_strategy())
    @settings(max_examples=100)
    def test_one_day_before_expiry_gives_one_day(self, expiry_str):
        """
        Feature: domain-service-infrastructure-refactoring, Property 6: 日期计算正确性
        
        **Validates: Requirements 4.5**
        
        验证到期日前一天返回 1 天
        """
        # 解析到期日
        expiry_date = DateCalculator.parse_expiry_date(expiry_str)
        
        if expiry_date is not None:
            # 到期日前一天
            one_day_before = expiry_date - timedelta(days=1)
            days = DateCalculator.calculate_days_to_expiry(expiry_str, one_day_before)
            
            assert days == 1, (
                f"到期日前一天应返回 1 天，实际: {days}，"
                f"到期日: {expiry_str}, 日期: {one_day_before}"
            )
    
    @given(yymm_format_strategy())
    @settings(max_examples=100)
    def test_one_day_after_expiry_gives_negative_one_day(self, expiry_str):
        """
        Feature: domain-service-infrastructure-refactoring, Property 6: 日期计算正确性
        
        **Validates: Requirements 4.5**
        
        验证到期日后一天返回 -1 天
        """
        # 解析到期日
        expiry_date = DateCalculator.parse_expiry_date(expiry_str)
        
        if expiry_date is not None:
            # 到期日后一天
            one_day_after = expiry_date + timedelta(days=1)
            days = DateCalculator.calculate_days_to_expiry(expiry_str, one_day_after)
            
            assert days == -1, (
                f"到期日后一天应返回 -1 天，实际: {days}，"
                f"到期日: {expiry_str}, 日期: {one_day_after}"
            )
