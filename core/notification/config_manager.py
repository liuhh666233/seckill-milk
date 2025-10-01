"""
通知配置管理器

负责从配置文件加载和初始化通知服务
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional
from loguru import logger

from .base import NotificationManager
from .lark import LarkNotificationService
from .wechat import WeChatNotificationService


class NotificationConfigManager:
    """通知配置管理器"""

    def __init__(self, config_file: str = "configs/notification.json"):
        self.config_file = Path(config_file)
        self.notification_manager = NotificationManager()

    def load_config(self) -> Dict[str, Any]:
        """加载通知配置"""
        try:
            if not self.config_file.exists():
                logger.warning(f"通知配置文件不存在: {self.config_file}")
                return {}

            with open(self.config_file, "r", encoding="utf-8") as f:
                config = json.load(f)

            logger.info(f"加载通知配置: {self.config_file}")
            return config
        except Exception as e:
            logger.error(f"加载通知配置失败: {e}")
            return {}

    def initialize_services(self) -> NotificationManager:
        """初始化通知服务"""
        config = self.load_config()

        if not config:
            logger.warning("通知配置为空，跳过服务初始化")
            return self.notification_manager

        # 获取默认服务名称
        default_service = config.get("default_service")
        services_config = config.get("services", {})

        # 注册服务
        for service_name, service_config in services_config.items():
            if not service_config.get("enabled", True):
                logger.info(f"跳过禁用的通知服务: {service_name}")
                continue

            try:
                service = self._create_service(service_name, service_config)
                if service:
                    is_default = service_name == default_service
                    self.notification_manager.register_service(
                        service_name, service, is_default=is_default
                    )
                    logger.info(f"注册通知服务: {service_name} (默认: {is_default})")
            except Exception as e:
                logger.error(f"注册通知服务失败 {service_name}: {e}")

        return self.notification_manager

    def _create_service(self, service_name: str, service_config: Dict[str, Any]):
        """创建通知服务实例"""
        service_type = service_config.get("type")

        if service_type == "lark":
            return LarkNotificationService(
                webhook_url=service_config.get("webhook_url", ""),
                secret=service_config.get("secret", ""),
            )
        elif service_type == "wechat":
            return WeChatNotificationService(
                app_id=service_config.get("app_id", ""),
                app_secret=service_config.get("app_secret", ""),
                template_id=service_config.get("template_id", ""),
            )
        else:
            logger.error(f"不支持的通知服务类型: {service_type}")
            return None

    def get_available_services(self) -> list:
        """获取可用的通知服务列表"""
        return self.notification_manager.get_available_services()

    def send_message(
        self, message: str, service_name: Optional[str] = None, **kwargs
    ) -> bool:
        """发送消息"""
        return self.notification_manager.send_message(message, service_name, **kwargs)

    def notify_task_result(
        self, task_info: Dict[str, Any], result: Dict[str, Any]
    ) -> bool:
        """通知任务结果"""
        return self.notification_manager.notify_task_result(task_info, result)
