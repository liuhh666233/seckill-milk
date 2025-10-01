"""
时间同步工具

提供网络时间同步功能
"""

import time
from datetime import datetime, date
from typing import List
from loguru import logger
import requests


class TimeSynchronizer:
    """时间同步器"""

    def __init__(
        self,
        network_time_url: str = "https://cube.meituan.com/ipromotion/cube/toc/component/base/getServerCurrentTime",
    ):
        self.network_time_url = network_time_url

    def get_network_time(self) -> datetime.time:
        """
        获取网络时间

        Returns:
            网络时间
        """
        try:
            response = requests.get(self.network_time_url, timeout=5)
            res = response.json()
            now_time = int(res["data"]) / 1000.0
            return datetime.fromtimestamp(now_time).time()
        except requests.exceptions.RequestException as e:
            logger.error(f"获取网络时间失败: {e}")
            return datetime.now().time()

    def sync_time(self, measurements: int = 3) -> float:
        """
        同步时间，返回时间差

        Args:
            measurements: 测量次数

        Returns:
            时间差（秒）
        """
        time_diffs = []

        for i in range(measurements):
            start_local = time.time()
            network_time = self.get_network_time()
            end_local = time.time()

            # 计算网络请求的平均延迟
            request_latency = (end_local - start_local) / 2

            # 使用请求中点时间进行比较
            middle_local_time = start_local + request_latency
            middle_local_datetime = datetime.fromtimestamp(middle_local_time)

            network_datetime = datetime.combine(
                middle_local_datetime.date(), network_time
            )

            time_diff = (network_datetime - middle_local_datetime).total_seconds()
            time_diffs.append(time_diff)

            logger.debug(
                f"时间同步第{i+1}次: {time_diff:.6f} 秒 (延迟: {request_latency*1000:.1f}ms)"
            )

            if i < measurements - 1:  # 不是最后一次，等待一小段时间
                time.sleep(0.1)

        # 使用中位数作为最终时间差，减少异常值影响
        time_diffs.sort()
        final_time_diff = time_diffs[len(time_diffs) // 2]  # 中位数

        logger.info(
            f"网络时间与本地时间差: {final_time_diff:.6f} 秒 (测量次数: {len(time_diffs)})"
        )
        logger.debug(f"所有测量值: {[f'{d:.6f}' for d in time_diffs]}")

        return final_time_diff

    def wait_for_time(self, target_time: datetime.time, time_diff: float = 0.0) -> None:
        """
        等待到指定时间

        Args:
            target_time: 目标时间
            time_diff: 时间差
        """
        logger.debug(f"目标启动时间: {target_time}")
        logger.debug(f"时间差: {time_diff:.3f} 秒")

        while True:
            # 使用高精度时间计算
            current_timestamp = time.time()
            current_local = datetime.fromtimestamp(current_timestamp).time()
            adjusted_timestamp = current_timestamp + time_diff
            adjusted_time = datetime.fromtimestamp(adjusted_timestamp).time()

            # 计算到启动时间的精确秒数差
            target_datetime = datetime.combine(date.today(), target_time)
            adjusted_datetime = datetime.fromtimestamp(adjusted_timestamp)

            time_diff_seconds = (target_datetime - adjusted_datetime).total_seconds()

            # 如果时间已到或已过，立即启动
            if time_diff_seconds <= 0:
                logger.info("Starting seckill...")
                break

            # 如果剩余时间很短（小于0.001秒），使用忙等待
            if time_diff_seconds <= 0.001:
                logger.debug(f"进入精确等待模式，剩余: {time_diff_seconds:.6f} 秒")
                while True:
                    current_timestamp = time.time()
                    adjusted_timestamp = current_timestamp + time_diff
                    adjusted_datetime = datetime.fromtimestamp(adjusted_timestamp)
                    time_diff_seconds = (
                        target_datetime - adjusted_datetime
                    ).total_seconds()
                    if time_diff_seconds <= 0:
                        logger.info("Starting seckill...")
                        return
                    # 微秒级忙等待
                    time.sleep(0.0001)  # 0.1毫秒

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


def print_time_cost(func):
    """打印函数执行时间"""
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        logger.info(f"函数 {func.__name__} 执行时间: {end_time - start_time:.6f} 秒")
        return result
    return wrapper