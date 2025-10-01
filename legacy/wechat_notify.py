# from wechatpy import WeChatClient
# from wechatpy.client.api import WeChatMessage
from datetime import datetime, timedelta
import requests
import json
import os
from typing import Dict, Any, Optional
from loguru import logger
from send_message_to_lark import send_message


class NotificationManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    # def __init__(self):
    #     if not hasattr(self, "initialized"):
    #         self.notifier = None
    #         self.users = {}
    #         # self.load_config()
    #         self.initialized = True

    # def load_config(self):
    #     """加载配置"""
    #     try:
    #         with open("notify_config.json", "r", encoding="utf-8") as f:
    #             config = json.load(f)

    #         self.notifier = WechatNotifier(
    #             app_id=config.get("app_id"),
    #             app_secret=config.get("app_secret"),
    #             template_id=config.get("template_id"),
    #         )
    #         self.users = config.get("users", {})

    #     except Exception as e:
    #         logger.error(f"加载通知配置失败: {str(e)}")

    def notify_task_result(
        self, task_info: Dict[str, Any], result: Dict[str, Any]
    ) -> None:
        """通知任务结果"""
        send_message(
            environ="SECKILL", message=f"任务: {task_info}\n\n任务结果: {result}"
        )
