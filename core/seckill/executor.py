"""
秒杀执行器

从原有的multiuserseckill.py重构而来
"""

import threading
import time
import random
from datetime import datetime, date, timedelta
from typing import Dict, Optional, List

from curl_cffi import requests
from loguru import logger

from strategies import RequestStrategyManager
from utils import TimeSynchronizer, ProxyManager
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
        self.notification_manager = notification_manager or NotificationConfigManager().initialize_services()

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

    def post_seckill_url(self) -> None:
        """执行秒杀请求"""
        while not self._should_stop():
            try:
                response = self._make_request()
                self._handle_response(response)
            except Exception as e:
                self._handle_error(e)

            self.attempts += 1
            if self._should_stop():
                break

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

    def _make_request(self) -> requests.Response:
        """发送请求"""
        url, process_data, headers = self._prepare_request()
        proxies = self.get_formatted_proxy()

        try:
            response = requests.get(
                url,
                headers=headers,
                proxies=proxies,
                timeout=1,
            )
            print(response.text)
            return response
        except requests.Timeout:
            raise RequestError("请求超时")
        except requests.RequestException as e:
            raise RequestError(f"请求失败: {str(e)}")

    def _handle_response(self, response: requests.Response) -> None:
        """处理响应"""
        try:
            strategy = self.strategy_manager.get_strategy(
                self.user_config.strategy_flag
            )
            response_data = strategy.process_response(response)
            message = response_data.get(self.key_message, "")

            logger.debug(f"[{self.account_name}] 响应: {message}")

            if self.key_value in message.lower():
                logger.info(f"[{self.account_name}] 成功完成请求")
                self.stop_flag.set()
                self.notification_manager.notify_task_result(
                    {"account_name": self.account_name, "message": message},
                    {"success": True, "message": message},
                )
            else:
                logger.warning(f"[{self.account_name}] 意外响应: {message}")

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

    def start_seckill(self) -> None:
        """开始秒杀"""
        # 等待到指定开始时间
        self.time_synchronizer.wait_for_time(self.start_time, self.time_diff)

        # 记录实际开始时间
        actual_start_time = time.time()
        actual_start_datetime = datetime.fromtimestamp(
            actual_start_time + self.time_diff
        )
        logger.info(
            f"[{self.account_name}] 实际开始时间: {actual_start_datetime.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}"
        )

        # 立即开始第一次请求，不等待
        try:
            self.post_seckill_url()
        except Exception as e:
            logger.error(f"[{self.account_name}] 首次请求失败: {e}")

        # 继续循环执行后续请求
        while not self.stop_flag.is_set():
            try:
                self.post_seckill_url()
            except Exception as e:
                logger.error(f"[{self.account_name}] 请求失败: {e}")

            # 只有在没有成功的情况下才等待，减少成功情况下的延迟
            if not self.stop_flag.is_set():
                time.sleep(0.1)

    def run(self) -> None:
        """运行秒杀"""
        logger.info(f"[{self.account_name}] 等待开始时间: {self.start_time}")

        # 刷新代理列表
        if self.proxy_flag:
            self.proxy_manager.refresh_proxies()

        seckill_threads: List[threading.Thread] = []
        for _ in range(self.thread_count):
            t = threading.Thread(target=self.start_seckill)
            t.start()
            seckill_threads.append(t)

        for t in seckill_threads:
            t.join()

        # 检查是否成功完成
        if not self.stop_flag.is_set():
            # 如果所有线程都结束了但stop_flag未设置，说明失败了
            failure_reason = f"达到最大尝试次数 ({self.max_attempts}) 仍未成功"
            self.notification_manager.notify_task_result(
                {
                    "account_name": self.account_name,
                    "description": f"秒杀任务 - {self.account_name}",
                    "start_time": self.start_time.strftime("%H:%M:%S.%f")[:-3],
                },
                {
                    "success": False,
                    "message": "秒杀失败",
                    "details": f"尝试了 {self.max_attempts} 次",
                    "failure_reason": failure_reason,
                },
            )

        logger.info(f"[{self.account_name}] 秒杀完成")


class RequestError(Exception):
    """请求错误"""

    pass


class ResponseError(Exception):
    """响应处理错误"""

    pass
