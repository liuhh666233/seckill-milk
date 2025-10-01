"""
秒杀核心模块

提供秒杀执行器和多用户管理功能
"""

from .executor import SeckillExecutor
from .manager import SeckillManager

__all__ = ["SeckillExecutor", "SeckillManager"]
