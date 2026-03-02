"""
日期计算工具类

提供日期计算相关的工具方法，用于期权到期日计算等场景。
"""
from datetime import datetime
from typing import Optional


class DateCalculator:
    """
    日期计算工具类
    
    提供期权到期日解析和天数计算等功能。
    """
    
    @staticmethod
    def parse_expiry_date(expiry_date_str: str) -> Optional[datetime]:
        """
        解析到期日字符串为 datetime 对象
        
        Args:
            expiry_date_str: 到期日字符串（YYMM 格式，如 "2401", "2509"）
            
        Returns:
            datetime 对象（假设到期日是该月的第三个星期五），解析失败返回 None
            
        Note:
            期权标准到期日是每月第三个星期五，简化实现使用该月 15 日作为近似
            
        Examples:
            >>> DateCalculator.parse_expiry_date("2401")
            datetime.datetime(2024, 1, 15, 0, 0)
            >>> DateCalculator.parse_expiry_date("2509")
            datetime.datetime(2025, 9, 15, 0, 0)
        """
        try:
            # 验证格式：应该是 4 位数字
            if not expiry_date_str or len(expiry_date_str) != 4:
                return None
            
            if not expiry_date_str.isdigit():
                return None
            
            # 解析年月
            year_str = expiry_date_str[:2]
            month_str = expiry_date_str[2:]
            
            year = int(year_str)
            month = int(month_str)
            
            # 验证月份有效性
            if month < 1 or month > 12:
                return None
            
            # 转换为完整年份（假设 20xx 年）
            full_year = 2000 + year
            
            # 假设到期日为该月 15 日（简化实现）
            expiry_date = datetime(full_year, month, 15)
            
            return expiry_date
            
        except (ValueError, TypeError):
            return None
    
    @staticmethod
    def calculate_days_to_expiry(
        expiry_date_str: str,
        current_date: datetime
    ) -> Optional[int]:
        """
        计算距离到期天数
        
        Args:
            expiry_date_str: 到期日字符串（YYMM 格式，如 "2401", "2509"）
            current_date: 当前日期
            
        Returns:
            距离到期天数，解析失败返回 None
            
        Examples:
            >>> from datetime import datetime
            >>> DateCalculator.calculate_days_to_expiry("2401", datetime(2023, 12, 1))
            45  # 假设到期日是 2024-01-15
            >>> DateCalculator.calculate_days_to_expiry("2509", datetime(2025, 8, 1))
            45  # 假设到期日是 2025-09-15
        """
        try:
            # 解析到期日
            expiry_date = DateCalculator.parse_expiry_date(expiry_date_str)
            if expiry_date is None:
                return None
            
            # 计算天数差
            delta = expiry_date - current_date
            days = delta.days
            
            return days
            
        except (ValueError, TypeError, AttributeError):
            return None
