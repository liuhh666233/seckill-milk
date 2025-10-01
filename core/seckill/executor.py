"""
秒杀执行器

从原有的multiuserseckill.py重构而来
"""

import threading
import time
import random
import asyncio
from datetime import datetime, date, timedelta
from typing import Dict, Optional, List

from curl_cffi import requests
from loguru import logger

from strategies import RequestStrategyManager
from utils import TimeSynchronizer, ProxyManager, print_time_cost
from config import UserConfig, SeckillConfig
from core.notification import NotificationConfigManager


class SeckillExecutor:
    """秒杀执行器"""

    def __init__(
        self,
        user_config: UserConfig,
        global_config: SeckillConfig,
        time_diff: float = 0.0,
        notification_manager: Optional[NotificationConfigManager] = None,
    ):
        self.user_config = user_config
        self.global_config = global_config
        self.time_diff = time_diff
        self.notification_manager = (
            notification_manager or NotificationConfigManager().initialize_services()
        )

        # 基础配置
        self.cookie_id = user_config.cookie_id
        self.cookie_name = user_config.cookie_name
        self.account_name = user_config.account_name
        self.max_attempts = user_config.max_attempts
        self.thread_count = user_config.thread_count
        self.start_time = global_config.start_time

        # 请求配置
        self._headers = {
            **user_config.headers,
            user_config.cookie_name: user_config.cookie_id,
        }

        self._data = user_config.data
        self._base_url = user_config.basurl

        # 控制标志
        self.attempts = 0
        self.stop_flag = threading.Event()
        self.key_value = user_config.key_value
        self.key_message = user_config.key_message

        # 策略管理
        self.strategy_manager = RequestStrategyManager()
        if user_config.strategy_flag and user_config.strategy_params:
            self.strategy_manager.update_strategy_params(
                user_config.strategy_flag, user_config.strategy_params
            )

        # 代理管理
        self.proxy_manager = ProxyManager(global_config.proxies)
        self.proxy_flag = user_config.proxy_flag

        # 时间同步
        self.time_synchronizer = TimeSynchronizer()

    def get_formatted_proxy(self) -> Optional[Dict[str, str]]:
        """从代理列表中随机选择一个代理并格式化"""
        if not self.proxy_manager.is_proxy_available():
            return None
        return self.proxy_manager.get_random_proxy()

    async def post_seckill_url(self) -> dict:
        """使用异步生成器实现精确时间控制的秒杀请求"""
        result = None

        # 使用异步生成器按精确间隔产生请求
        async for request_result in self._request_generator():
            result = request_result
            if result and result.get("success"):
                return result

        # 如果所有请求都失败，返回最后一个结果
        return result or {
            "success": False,
            "message": "秒杀失败",
            "details": f"尝试了 {self.max_attempts} 次",
            "failure_reason": f"达到最大尝试次数 ({self.max_attempts}) 仍未成功",
        }

    async def _request_generator(self):
        """异步生成器，按精确间隔产生请求（不受请求执行时间影响）"""
        request_interval = self.user_config.request_interval
        start_time = time.time()

        # 预先创建所有请求任务
        request_tasks = []
        for attempt in range(self.max_attempts):
            # 计算精确的目标时间点
            target_time = start_time + (attempt * request_interval)

            # 等待到精确的目标时间点
            current_time = time.time()
            if current_time < target_time:
                await asyncio.sleep(target_time - current_time)

            if not self._should_stop():
                request_task = asyncio.create_task(self._make_request())
                request_tasks.append(request_task)

        for i, request_task in enumerate(request_tasks):
            if self._should_stop():
                break
            try:
                response = await request_task
                result = self._handle_response(response)
                self.attempts += 1
                yield result
            except Exception as e:
                self._handle_error(e)
                self.attempts += 1
                yield None

    def _should_stop(self) -> bool:
        """检查是否应该停止请求"""
        if self.stop_flag.is_set():
            return True
        if self.attempts >= self.max_attempts:
            logger.error(
                f"[{self.account_name}] 达到最大尝试次数 ({self.max_attempts})，停止请求"
            )
            self.stop_flag.set()
            return True
        return False

    def _prepare_request(self) -> tuple[str, Dict, Dict]:
        """准备请求参数"""
        current_time = str(int(time.time() * 1000))
        strategy = self.strategy_manager.get_strategy(self.user_config.strategy_flag)
        return strategy.prepare_request(
            datetime.now(), self._data, self._headers, self._base_url
        )

    @print_time_cost
    async def _make_request(self) -> requests.Response:
        """异步发送请求"""
        url, process_data, headers = self._prepare_request()
        proxies = self.get_formatted_proxy()
        if self._should_stop():
            return None
        logger.info(f"[{self.account_name}] 发送请求")
        try:
            async with requests.AsyncSession() as session:
                response = await session.get(
                    url,
                    headers=headers,
                    proxies=proxies,
                    timeout=1,
                )
                return response
        except asyncio.TimeoutError:
            raise RequestError("请求超时")
        except Exception as e:
            raise RequestError(f"请求失败: {str(e)}")

    def _handle_response(self, response: requests.Response) -> dict:
        """处理响应并返回结果"""
        try:
            strategy = self.strategy_manager.get_strategy(
                self.user_config.strategy_flag
            )
            response_data = strategy.process_response(response)
            message = response_data.get(self.key_message, "")

            logger.debug(f"[{self.account_name}] 响应: {message}")

            if self.key_value in message.lower():
                logger.info(f"[{self.account_name}] 成功完成请求")
                return {
                    "success": True,
                    "message": message,
                    "details": f"成功完成秒杀",
                    "failure_reason": None,
                }
            else:
                logger.warning(f"[{self.account_name}] 意外响应: {message}")
                return {
                    "success": False,
                    "message": f"意外响应: {message}",
                    "details": f"尝试了 {self.attempts} 次",
                    "failure_reason": "服务器返回意外响应",
                }

        except Exception as e:
            raise ResponseError(f"处理响应失败: {str(e)}")

    def _handle_error(self, error: Exception) -> None:
        """处理错误"""
        if isinstance(error, (RequestError, ResponseError)):
            logger.error(f"[{self.account_name}] {str(error)}")
        else:
            logger.error(f"[{self.account_name}] 意外错误: {str(error)}")

        logger.info(
            f"[{self.account_name}] 尝试 {self.attempts}/{self.max_attempts} 失败，重试中..."
        )

    async def start_seckill(self) -> None:
        """异步开始秒杀"""
        # 等待到指定开始时间
        self.time_synchronizer.wait_for_time(self.start_time, self.time_diff)

        # 记录实际开始时间
        actual_start_time = time.time()
        actual_start_datetime = datetime.fromtimestamp(
            actual_start_time + self.time_diff
        )
        logger.info(
            f"[{self.account_name}] 实际开始时间: {actual_start_datetime.strftime('%Y-%m-%d %H:%M:%S.%f')}"
        )
        result = await self.post_seckill_url()
        self._send_notification(result)

    def run(self) -> None:
        """运行秒杀"""
        thread_id = threading.current_thread().ident
        logger.info(
            f"[{self.account_name}] 线程{thread_id} 等待开始时间: {self.start_time}"
        )

        # 刷新代理列表
        if self.proxy_flag:
            self.proxy_manager.refresh_proxies()

        # 使用异步执行
        asyncio.run(self._run_async())

        thread_id = threading.current_thread().ident
        logger.info(f"[{self.account_name}] 线程{thread_id} 秒杀完成")

    async def _run_async(self) -> None:
        """单协程执行，保证精确时间控制"""
        # 只创建一个任务，不使用并发，确保时间控制精确
        await self.start_seckill()

    def _send_notification(self, result: dict) -> None:
        """统一发送通知"""
        task_info = {
            "account_name": self.account_name,
            "description": f"秒杀任务 - {self.account_name}",
            "start_time": self.start_time.strftime("%H:%M:%S.%f"),
        }

        if not result:
            result = {
                "success": False,
                "message": "秒杀失败",
                "details": f"尝试了 {self.max_attempts} 次",
                "failure_reason": f"达到最大尝试次数 ({self.max_attempts}) 仍未成功",
            }

        self.notification_manager.notify_task_result(task_info, result)


class RequestError(Exception):
    """请求错误"""

    pass


class ResponseError(Exception):
    """响应处理错误"""

    pass
