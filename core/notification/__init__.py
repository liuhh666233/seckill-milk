"""
通知模块

提供多种通知服务
"""

from .base import INotificationService, NotificationManager
from .lark import LarkNotificationService
from .wechat import WeChatNotificationService
from .config_manager import NotificationConfigManager

__all__ = [
    "INotificationService",
    "NotificationManager",
    "LarkNotificationService",
    "WeChatNotificationService",
    "NotificationConfigManager",
]
