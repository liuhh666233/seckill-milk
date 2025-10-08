import threading
import time
from datetime import datetime, date, timedelta
from typing import Dict, Optional, List

from curl_cffi import requests

# import requests
from loguru import logger
import random
from encory import RequestStrategyManager
from config import SeckkillerConfig
from send_message_to_lark import send_message


class Seckkiller:

    def __init__(self, config: SeckkillerConfig):
        self.cookie_id: str = config.cookie_id
        self.cooke_name: str = config.cookie_name
        self._headers: Dict[str, str] = {
            **config.headers,
            self.cooke_name: config.cookie_id,
        }
        self._data: Dict[str, int] = config.data
        self._base_url: str = config.base_url
        self._proxy_url: str = config.proxy_url
        self.max_attempts: int = config.max_attempts
        self.attempts: int = 0
        self.key_value: Optional[Dict[str, str]] = config.key_value
        self.key_messgae: str = config.key_message
        self.account_name: Optional[str] = config.account_name
        self.stop_flag: threading.Event = threading.Event()
        self.thread_count: int = config.thread_count
        self.start_time: datetime.time = config.start_time
        self.proxy_list: List[Dict[str, str]] = []
        self.strategy_flag: bool = config.strategy_flag
        self.strategy_manager = RequestStrategyManager()
        if config.strategy_flag and config.strategy_params:
            self.strategy_manager.update_strategy_params(
                config.strategy_flag, config.strategy_params
            )
        self.proxy_flag: bool = config.proxy_flag
        self.time_diff: float = config.time_diff

    def get_formatted_proxy(self):
        """从代理列表中随机选择一个代理并格式化"""
        if not self.proxy_list:
            return None

        proxy = random.choice(self.proxy_list)
        ip, port = proxy.split(":")
        return {"http": f"http://{ip}:{port}"}

    def post_seckill_url(self) -> None:
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
                f"[{self.account_name}] Reached maximum attempts ({self.max_attempts}). Stopping requests."
            )
            self.stop_flag.set()
            return True
        return False

    def _prepare_request(self) -> tuple[str, Dict, Dict]:
        """准备请求参数"""
        current_time = str(int(time.time() * 1000))
        strategy = self.strategy_manager.get_strategy(self.strategy_flag)
        return strategy.prepare_request(
            current_time, self._data, self._headers, self._base_url
        )

    def _make_request(self) -> requests.Response:
        """发送请求"""
        url, process_data, headers = self._prepare_request()
        proxies = random.choice(self.proxy_list) if self.proxy_list else None

        try:
            response = requests.get(
                url,
                headers=headers,
                # data=process_data,
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
            strategy = self.strategy_manager.get_strategy(self.strategy_flag)
            response_data = strategy.process_response(response)
            message = response_data.get(self.key_messgae, "")

            logger.debug(f"[{self.account_name}] Response: {message}")

            if self.key_value in message.lower():
                logger.info(
                    f"[{self.account_name}] Successfully completed the request."
                )
                self.stop_flag.set()
                send_message(
                    environ="SECKILL",
                    message=f"任务: {self.account_name}\n\n任务结果: {message}",
                )
            else:
                logger.warning(f"[{self.account_name}] Unexpected response: {message}")

        except Exception as e:
            raise ResponseError(f"处理响应失败: {str(e)}")

    def _handle_error(self, error: Exception) -> None:
        """处理错误"""
        if isinstance(error, (RequestError, ResponseError)):
            logger.error(f"[{self.account_name}] {str(error)}")
        else:
            logger.error(f"[{self.account_name}] Unexpected error: {str(error)}")

        logger.info(
            f"[{self.account_name}] Attempt {self.attempts}/{self.max_attempts} failed. Retrying..."
        )

    def start_seckill(self) -> None:
        # 等待到指定开始时间
        self.wait_for_start_time()

        # 记录实际开始时间
        actual_start_time = time.time()
        actual_start_datetime = datetime.fromtimestamp(
            actual_start_time + self.time_diff
        )
        logger.info(
            f"[{self.account_name}] 实际开始时间: {actual_start_datetime.strftime('%Y-%m-%d %H:%M:%S.%f')}"
        )
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

    @staticmethod
    def get_network_time() -> datetime.time:
        NetworkTimeUrl = "https://cube.meituan.com/ipromotion/cube/toc/component/base/getServerCurrentTime"
        # NetworkTimeUrl = (
        #     "http://api.m.taobao.com/rest/api3.do?api=mtop.common.getTimestamp"
        # )
        try:
            response = requests.get(
                NetworkTimeUrl,
                # verify=False,
                # impersonate="chrome100",
            )
            res = response.json()
            now_time = int(res["data"]) / 1000.0
            return datetime.fromtimestamp(now_time).time()
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            return datetime.now().time()

    def get_proxy_ips(self) -> List[Dict[str, str]]:
        if self.proxy_flag == False:
            logger.info(f"[{self.account_name}] Using proxy IP9s")
            return []
        else:
            try:
                response = requests.get(
                    self._proxy_url,
                    # impersonate="chrome100",
                )
                data = response.json()
                if data["success"] and data["code"] == 0:
                    return Seckkiller.extract_ip_port(data)
                else:
                    logger.error(f"Failed to get proxy IP9s: {data['msg']}")
                    return []
            except requests.exceptions.RequestException as e:
                logger.error(f"Failed to get proxy IPs: {e}")
                return []

    @staticmethod
    def extract_ip_port(json_str):
        """
        从 JSON 数据中解析出代理 IP 和端口。

        :param json_str: 包含代理信息的 JSON 数据（字典格式）
        :return: 代理列表，格式为 ["ip:port", ...]
        """
        proxies = []
        if not isinstance(json_str, dict):
            return proxies

        for item in json_str.get("data", []):
            ip = item.get("ip")
            port = item.get("port")
            if ip and port:
                proxies.append({"http": f"http://{ip}:{port}"})
        return proxies

    def wait_for_start_time(self) -> None:
        proxy_fetch_interval = 5  # 设置获取代理 IP 的间隔时间（秒）
        last_proxy_fetch_time = 0
        proxy_fetch_failed = False  # 标记代理获取是否失败

        logger.debug(f"[{self.account_name}] 目标启动时间: {self.start_time}")
        logger.debug(f"[{self.account_name}] 时间差: {self.time_diff:.3f} 秒")

        while True:
            # 使用高精度时间计算
            current_timestamp = time.time()
            adjusted_timestamp = current_timestamp + self.time_diff

            # 计算到启动时间的精确秒数差
            target_datetime = datetime.combine(date.today(), self.start_time)
            adjusted_datetime = datetime.fromtimestamp(adjusted_timestamp)

            time_diff_seconds = (target_datetime - adjusted_datetime).total_seconds()

            # 如果时间已到或已过，立即启动
            if time_diff_seconds <= 0:
                logger.info(f"[{self.account_name}] Starting seckill...")
                break

            # 如果剩余时间很短（小于0.001秒），使用忙等待
            if time_diff_seconds <= 0.001:
                logger.debug(
                    f"[{self.account_name}] 进入精确等待模式，剩余: {time_diff_seconds:.6f} 秒"
                )
                while True:
                    current_timestamp = time.time()
                    adjusted_timestamp = current_timestamp + self.time_diff
                    adjusted_datetime = datetime.fromtimestamp(adjusted_timestamp)
                    time_diff_seconds = (
                        target_datetime - adjusted_datetime
                    ).total_seconds()
                    if time_diff_seconds <= 0:
                        logger.info(f"[{self.account_name}] Starting seckill...")
                        return
                    # 微秒级忙等待
                    time.sleep(0.0001)  # 0.1毫秒

            # 检查是否需要获取代理 IP（仅在剩余时间较长时执行）
            if (
                time_diff_seconds > 1.0  # 剩余时间大于1秒时才获取代理
                and not self.proxy_list
                and not proxy_fetch_failed
                and current_timestamp - last_proxy_fetch_time > proxy_fetch_interval
            ):
                self.proxy_list = self.get_proxy_ips()
                last_proxy_fetch_time = current_timestamp
                if self.proxy_list:
                    logger.info(
                        f"[{self.account_name}] Got {len(self.proxy_list)} proxy IPs"
                    )
                else:
                    logger.info(
                        f"[{self.account_name}] No proxy IPs available, will use local IP"
                    )
                    logger.debug(f"[{self.proxy_list}] Proxy fetch failed")
                    proxy_fetch_failed = True

            # 根据剩余时间调整睡眠间隔
            if time_diff_seconds > 5:
                sleep_time = 0.1  # 剩余时间长时，每100毫秒检查一次
            elif time_diff_seconds > 1:
                sleep_time = 0.01  # 剩余时间中等时，每10毫秒检查一次
            elif time_diff_seconds > 0.1:
                sleep_time = 0.001  # 剩余时间短时，每1毫秒检查一次
            else:
                sleep_time = 0.0001  # 剩余时间很短时，每0.1毫秒检查一次

            time.sleep(sleep_time)

    def run(self) -> None:
        logger.info(f"[{self.account_name}] Waiting for start time: {self.start_time}")
        seckill_threads: List[threading.Thread] = []
        for _ in range(self.thread_count):
            t = threading.Thread(target=self.start_seckill)
            t.start()
            seckill_threads.append(t)

        for t in seckill_threads:
            t.join()

        logger.info(f"[{self.account_name}] Seckill finished")


class RequestError(Exception):
    """请求错误"""

    pass


class ResponseError(Exception):
    """响应处理错误"""

    pass
