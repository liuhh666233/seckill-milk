"""
通知基类

定义通知服务的抽象接口
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from loguru import logger


class INotificationService(ABC):
    """通知服务接口"""

    @abstractmethod
    def send_message(self, message: str, **kwargs) -> bool:
        """
        发送消息

        Args:
            message: 消息内容
            **kwargs: 其他参数

        Returns:
            是否发送成功
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """
        检查服务是否可用

        Returns:
            是否可用
        """
        pass


class NotificationManager:
    """通知管理器"""

    def __init__(self):
        self.services: Dict[str, INotificationService] = {}
        self.default_service: Optional[str] = None

    def register_service(
        self, name: str, service: INotificationService, is_default: bool = False
    ):
        """
        注册通知服务

        Args:
            name: 服务名称
            service: 通知服务实例
            is_default: 是否为默认服务
        """
        self.services[name] = service
        if is_default or self.default_service is None:
            self.default_service = name
        logger.info(f"注册通知服务: {name}")

    def send_message(
        self, message: str, service_name: Optional[str] = None, **kwargs
    ) -> bool:
        """
        发送消息

        Args:
            message: 消息内容
            service_name: 服务名称，None则使用默认服务
            **kwargs: 其他参数

        Returns:
            是否发送成功
        """
        if service_name is None:
            service_name = self.default_service

        if service_name not in self.services:
            logger.error(f"未找到通知服务: {service_name}")
            return False

        service = self.services[service_name]
        if not service.is_available():
            logger.warning(f"通知服务不可用: {service_name}")
            return False

        try:
            return service.send_message(message, **kwargs)
        except Exception as e:
            logger.error(f"发送消息失败: {e}")
            return False

    def notify_task_result(
        self, task_info: Dict[str, Any], result: Dict[str, Any]
    ) -> bool:
        """
        通知任务结果

        Args:
            task_info: 任务信息
            result: 任务结果

        Returns:
            是否通知成功
        """
        message = f"任务: {task_info}\n\n任务结果: {result}"
        return self.send_message(message)

    def get_available_services(self) -> list:
        """
        获取可用的通知服务列表

        Returns:
            可用服务名称列表
        """
        return [
            name for name, service in self.services.items() if service.is_available()
        ]
