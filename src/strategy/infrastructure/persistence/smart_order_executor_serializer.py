"""
SmartOrderExecutor 序列化器

负责 SmartOrderExecutor 的序列化和反序列化，将领域对象转换为可持久化格式。
"""
from typing import Dict, Any, Optional

from src.strategy.domain.domain_service.execution.smart_order_executor import SmartOrderExecutor
from src.strategy.domain.value_object.trading.order_execution import OrderExecutionConfig, ManagedOrder


class SmartOrderExecutorSerializer:
    """
    SmartOrderExecutor 序列化器
    
    提供静态方法将 SmartOrderExecutor 实例序列化为字典格式，
    以及从字典反序列化恢复实例。
    
    Examples:
        >>> executor = SmartOrderExecutor(config)
        >>> data = SmartOrderExecutorSerializer.to_dict(executor)
        >>> restored = SmartOrderExecutorSerializer.from_dict(data)
    """
    
    @staticmethod
    def to_dict(executor: SmartOrderExecutor) -> Dict[str, Any]:
        """
        将 SmartOrderExecutor 序列化为字典
        
        Args:
            executor: SmartOrderExecutor 实例
            
        Returns:
            JSON 兼容的字典，包含配置和订单状态
            
        Raises:
            ValueError: 如果 executor 为 None
            
        Examples:
            >>> config = OrderExecutionConfig(timeout_seconds=30)
            >>> executor = SmartOrderExecutor(config)
            >>> data = SmartOrderExecutorSerializer.to_dict(executor)
            >>> data['config']['timeout_seconds']
            30
        """
        if executor is None:
            raise ValueError("executor cannot be None")
        
        return {
            "config": {
                "timeout_seconds": executor.config.timeout_seconds,
                "max_retries": executor.config.max_retries,
                "slippage_ticks": executor.config.slippage_ticks,
                "price_tick": executor.config.price_tick,
            },
            "orders": {
                oid: order.to_dict() for oid, order in executor._orders.items()
            },
        }
    
    @staticmethod
    def from_dict(
        data: Dict[str, Any],
        config: Optional[OrderExecutionConfig] = None
    ) -> SmartOrderExecutor:
        """
        从字典反序列化 SmartOrderExecutor
        
        Args:
            data: 序列化的字典数据
            config: 可选的配置对象，如果为 None 则从 data 中读取
            
        Returns:
            SmartOrderExecutor 实例
            
        Raises:
            ValueError: 如果 data 为 None 或格式无效
            
        Examples:
            >>> data = {
            ...     "config": {"timeout_seconds": 30, "max_retries": 3},
            ...     "orders": {}
            ... }
            >>> executor = SmartOrderExecutorSerializer.from_dict(data)
            >>> executor.config.timeout_seconds
            30
        """
        if data is None:
            raise ValueError("data cannot be None")
        
        # 如果没有提供配置对象，从数据中读取
        if config is None:
            cfg_data = data.get("config", {})
            # 使用默认值处理缺失字段
            defaults = OrderExecutionConfig()
            config = OrderExecutionConfig(
                timeout_seconds=cfg_data.get("timeout_seconds", defaults.timeout_seconds),
                max_retries=cfg_data.get("max_retries", defaults.max_retries),
                slippage_ticks=cfg_data.get("slippage_ticks", defaults.slippage_ticks),
                price_tick=cfg_data.get("price_tick", defaults.price_tick),
            )
        
        # 创建执行器实例
        executor = SmartOrderExecutor(config)
        
        # 恢复订单状态
        for oid, order_data in data.get("orders", {}).items():
            executor._orders[oid] = ManagedOrder.from_dict(order_data)
        
        return executor
