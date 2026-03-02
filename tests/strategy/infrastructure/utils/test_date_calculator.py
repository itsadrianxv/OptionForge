"""
DateCalculator 单元测试

测试日期计算工具类的功能。
"""
import pytest
from datetime import datetime

from src.strategy.infrastructure.utils.date_calculator import DateCalculator


class TestDateCalculator:
    """DateCalculator 单元测试"""
    
    # parse_expiry_date 测试
    
    def test_parse_expiry_date_valid_format(self):
        """测试有效 YYMM 格式的解析"""
        result = DateCalculator.parse_expiry_date("2401")
        assert result == datetime(2024, 1, 15)
        
        result = DateCalculator.parse_expiry_date("2509")
        assert result == datetime(2025, 9, 15)
        
        result = DateCalculator.parse_expiry_date("2412")
        assert result == datetime(2024, 12, 15)
    
    def test_parse_expiry_date_all_months(self):
        """测试所有月份的解析"""
        for month in range(1, 13):
            expiry_str = f"24{month:02d}"
            result = DateCalculator.parse_expiry_date(expiry_str)
            assert result == datetime(2024, month, 15)
    
    def test_parse_expiry_date_different_years(self):
        """测试不同年份的解析"""
        for year in range(24, 30):
            expiry_str = f"{year:02d}06"
            result = DateCalculator.parse_expiry_date(expiry_str)
            assert result == datetime(2000 + year, 6, 15)
    
    def test_parse_expiry_date_invalid_format(self):
        """测试无效格式返回 None"""
        # 长度不对
        assert DateCalculator.parse_expiry_date("241") is None
        assert DateCalculator.parse_expiry_date("24011") is None
        
        # 包含非数字字符
        assert DateCalculator.parse_expiry_date("24a1") is None
        assert DateCalculator.parse_expiry_date("abcd") is None
        
        # 空字符串
        assert DateCalculator.parse_expiry_date("") is None
    
    def test_parse_expiry_date_invalid_month(self):
        """测试无效月份返回 None"""
        assert DateCalculator.parse_expiry_date("2400") is None  # 月份 0
        assert DateCalculator.parse_expiry_date("2413") is None  # 月份 13
        assert DateCalculator.parse_expiry_date("2499") is None  # 月份 99
    
    # calculate_days_to_expiry 测试
    
    def test_calculate_days_to_expiry_basic(self):
        """测试基本的天数计算"""
        # 2024-01-15 - 2023-12-01 = 45 天
        current_date = datetime(2023, 12, 1)
        result = DateCalculator.calculate_days_to_expiry("2401", current_date)
        assert result == 45
        
        # 2025-09-15 - 2025-08-01 = 45 天
        current_date = datetime(2025, 8, 1)
        result = DateCalculator.calculate_days_to_expiry("2509", current_date)
        assert result == 45
    
    def test_calculate_days_to_expiry_same_month(self):
        """测试当月到期的情况"""
        # 2024-01-15 - 2024-01-01 = 14 天
        current_date = datetime(2024, 1, 1)
        result = DateCalculator.calculate_days_to_expiry("2401", current_date)
        assert result == 14
        
        # 2024-01-15 - 2024-01-10 = 5 天
        current_date = datetime(2024, 1, 10)
        result = DateCalculator.calculate_days_to_expiry("2401", current_date)
        assert result == 5
    
    def test_calculate_days_to_expiry_already_expired(self):
        """测试已过期的情况（负天数）"""
        # 2024-01-15 - 2024-02-01 = -17 天
        current_date = datetime(2024, 2, 1)
        result = DateCalculator.calculate_days_to_expiry("2401", current_date)
        assert result == -17
        
        # 2024-01-15 - 2024-01-20 = -5 天
        current_date = datetime(2024, 1, 20)
        result = DateCalculator.calculate_days_to_expiry("2401", current_date)
        assert result == -5
    
    def test_calculate_days_to_expiry_cross_year(self):
        """测试跨年的情况"""
        # 2025-01-15 - 2024-12-01 = 45 天
        current_date = datetime(2024, 12, 1)
        result = DateCalculator.calculate_days_to_expiry("2501", current_date)
        assert result == 45
        
        # 2025-12-15 - 2025-01-01 = 348 天
        current_date = datetime(2025, 1, 1)
        result = DateCalculator.calculate_days_to_expiry("2512", current_date)
        assert result == 348
    
    def test_calculate_days_to_expiry_with_time(self):
        """测试带时间的日期计算（只计算天数差）"""
        # 2024-01-15 00:00:00 - 2024-01-01 12:30:45
        current_date = datetime(2024, 1, 1, 12, 30, 45)
        result = DateCalculator.calculate_days_to_expiry("2401", current_date)
        # 天数差应该是 13（因为有时间部分）
        assert result == 13
    
    def test_calculate_days_to_expiry_invalid_expiry_str(self):
        """测试无效到期日字符串返回 None"""
        current_date = datetime(2024, 1, 1)
        
        assert DateCalculator.calculate_days_to_expiry("", current_date) is None
        assert DateCalculator.calculate_days_to_expiry("241", current_date) is None
        assert DateCalculator.calculate_days_to_expiry("abcd", current_date) is None
        assert DateCalculator.calculate_days_to_expiry("2400", current_date) is None
        assert DateCalculator.calculate_days_to_expiry("2413", current_date) is None
    
    def test_calculate_days_to_expiry_edge_cases(self):
        """测试边界条件"""
        # 到期日当天
        current_date = datetime(2024, 1, 15)
        result = DateCalculator.calculate_days_to_expiry("2401", current_date)
        assert result == 0
        
        # 到期日前一天
        current_date = datetime(2024, 1, 14)
        result = DateCalculator.calculate_days_to_expiry("2401", current_date)
        assert result == 1
        
        # 到期日后一天
        current_date = datetime(2024, 1, 16)
        result = DateCalculator.calculate_days_to_expiry("2401", current_date)
        assert result == -1
    
    # 综合测试
    
    def test_parse_and_calculate_consistency(self):
        """测试解析和计算的一致性"""
        expiry_str = "2509"
        current_date = datetime(2025, 8, 1)
        
        # 使用 parse_expiry_date 解析
        expiry_date = DateCalculator.parse_expiry_date(expiry_str)
        assert expiry_date is not None
        
        # 手动计算天数
        expected_days = (expiry_date - current_date).days
        
        # 使用 calculate_days_to_expiry 计算
        actual_days = DateCalculator.calculate_days_to_expiry(expiry_str, current_date)
        
        # 验证一致性
        assert actual_days == expected_days
    
    def test_multiple_calculations_with_same_expiry(self):
        """测试同一到期日的多次计算"""
        expiry_str = "2412"
        
        # 不同的当前日期
        dates = [
            datetime(2024, 11, 1),
            datetime(2024, 11, 15),
            datetime(2024, 12, 1),
            datetime(2024, 12, 10),
            datetime(2024, 12, 15),
            datetime(2024, 12, 20),
        ]
        
        for current_date in dates:
            result = DateCalculator.calculate_days_to_expiry(expiry_str, current_date)
            assert result is not None
            
            # 验证计算结果
            expiry_date = datetime(2024, 12, 15)
            expected = (expiry_date - current_date).days
            assert result == expected
