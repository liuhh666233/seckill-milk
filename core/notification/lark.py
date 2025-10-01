"""
飞书通知服务

提供飞书群消息通知功能
"""

import requests
import hashlib
import base64
import hmac
import time
from typing import Dict, Any
from loguru import logger

from .base import INotificationService


class LarkNotificationService(INotificationService):
    """飞书通知服务"""

    def __init__(self, webhook_url: str, secret: str):
        self.webhook_url = webhook_url
        self.secret = secret

    def _gen_sign(self, timestamp: int, secret: str) -> str:
        """生成签名"""
        string_to_sign = f"{timestamp}\n{secret}"
        hmac_code = hmac.new(
            string_to_sign.encode("utf-8"), digestmod=hashlib.sha256
        ).digest()
        return base64.b64encode(hmac_code).decode("utf-8")

    def send_message(self, message: str, **kwargs) -> bool:
        """
        发送飞书消息

        Args:
            message: 消息内容
            **kwargs: 其他参数

        Returns:
            是否发送成功
        """
        try:
            timestamp = int(time.time())
            sign = self._gen_sign(timestamp, self.secret)

            content = {
                "timestamp": str(timestamp),
                "sign": str(sign),
                "msg_type": "text",
                "content": {"text": message},
            }

            result = requests.post(self.webhook_url, json=content, timeout=10)

            if result.status_code == 200:
                logger.info("飞书消息发送成功")
                return True
            else:
                logger.error(f"飞书消息发送失败: {result.status_code} - {result.text}")
                return False

        except Exception as e:
            logger.error(f"发送飞书消息失败: {e}")
            return False

    def is_available(self) -> bool:
        """
        检查飞书服务是否可用

        Returns:
            是否可用
        """
        return bool(self.webhook_url and self.secret)

    @classmethod
    def from_config(cls, config: Dict[str, str]) -> "LarkNotificationService":
        """
        从配置创建实例

        Args:
            config: 配置字典

        Returns:
            飞书通知服务实例
        """
        return cls(
            webhook_url=config.get("webhook_url", ""), secret=config.get("secret", "")
        )
