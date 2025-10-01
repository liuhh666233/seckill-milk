"""
加密策略管理器

管理各种加密策略的实现
"""

from typing import Dict, Optional, Any
from loguru import logger

from ..base import IEncryptionStrategy
from .strategies import (
    DefaultEncryptionStrategy,
    MixueEncryptionStrategy,
    KuDiEncryptionStrategy,
)


class EncryptionStrategyManager:
    """加密策略管理器"""

    def __init__(self):
        self.strategies: Dict[str, IEncryptionStrategy] = {
            "default": DefaultEncryptionStrategy(),
            "mixue": MixueEncryptionStrategy({}),
            "kudi": KuDiEncryptionStrategy({}),
        }

    def get_strategy(self, strategy_name: Optional[str]) -> IEncryptionStrategy:
        """
        获取加密策略

        Args:
            strategy_name: 策略名称

        Returns:
            加密策略实例
        """
        if strategy_name is None:
            strategy_name = "default"

        if strategy_name not in self.strategies:
            logger.warning(f"未找到加密策略: {strategy_name}，使用默认策略")
            return self.strategies["default"]

        return self.strategies[strategy_name]

    def register_strategy(self, name: str, strategy: IEncryptionStrategy):
        """
        注册加密策略

        Args:
            name: 策略名称
            strategy: 策略实例
        """
        self.strategies[name] = strategy
        logger.info(f"注册加密策略: {name}")

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
