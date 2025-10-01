"""
请求策略管理器

管理各种请求策略的实现
"""

from typing import Dict, Optional, Any
from loguru import logger

from ..base import ISeckillStrategy
from .strategies import (
    DefaultRequestStrategy,
    MixueRequestStrategy,
    KuDiRequestStrategy,
    JDRequestStrategy,
    MTRequestStrategy,
    BWRequestStrategy,
)


class RequestStrategyManager:
    """请求策略管理器"""

    def __init__(self):
        self.strategies: Dict[str, ISeckillStrategy] = {
            "default": DefaultRequestStrategy(),
            "mixue": MixueRequestStrategy({}),
            "kudi": KuDiRequestStrategy({}),
            "jd": JDRequestStrategy(),
            "mt": MTRequestStrategy({}),
            "bw": BWRequestStrategy({}),
        }

    def get_strategy(self, strategy_name: Optional[str]) -> ISeckillStrategy:
        """
        获取请求策略

        Args:
            strategy_name: 策略名称

        Returns:
            请求策略实例
        """
        if strategy_name is None:
            strategy_name = "default"

        if strategy_name not in self.strategies:
            return self.strategies["default"]

        return self.strategies[strategy_name]

    def register_strategy(self, name: str, strategy: ISeckillStrategy):
        """
        注册请求策略

        Args:
            name: 策略名称
            strategy: 策略实例
        """
        self.strategies[name] = strategy
        logger.info(f"注册请求策略: {name}")

    def update_strategy_params(self, strategy_name: str, params: Dict[str, Any]):
        """
        更新策略参数

        Args:
            strategy_name: 策略名称
            params: 策略参数
        """
        if strategy_name in self.strategies:
            strategy_class = type(self.strategies[strategy_name])
            self.strategies[strategy_name] = strategy_class(params)
            logger.info(f"更新策略参数: {strategy_name}")
        else:
            logger.warning(f"未找到策略: {strategy_name}")

    def list_strategies(self) -> list:
        """
        列出所有可用策略

        Returns:
            策略名称列表
        """
        return list(self.strategies.keys())
