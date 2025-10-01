from multiuserseckill import Seckkiller
from datetime import datetime, date, timedelta
from typing import Dict
import time
import json
import multiprocessing
from loguru import logger
from config import SeckillConfig, UserConfig, SeckkillerConfig


class SeckillManager:
    def __init__(self, config: dict = None, config_file: str = None):
        if config:
            self.config = SeckillConfig.from_dict(config)
        elif config_file:
            self.config_file = config_file
            with open(self.config_file, "r", encoding="utf-8") as f:
                logger.info(f"Loading config from {self.config_file}...")
                config_dict = json.load(f)
                self.config = SeckillConfig.from_dict(config_dict)
        else:
            raise ValueError("必须提供 config 或 config_file 参数")

    def sync_time(self) -> float:
        """同步时间，返回时间差"""
        # 进行多次时间同步以提高精度
        time_diffs = []
        for i in range(3):  # 进行3次测量
            start_local = time.time()
            network_time = Seckkiller.get_network_time()
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

            if i < 2:  # 不是最后一次，等待一小段时间
                time.sleep(0.1)

        # 使用中位数作为最终时间差，减少异常值影响
        time_diffs.sort()
        final_time_diff = time_diffs[1]  # 中位数

        logger.info(
            f"网络时间与本地时间差: {final_time_diff:.6f} 秒 (测量次数: {len(time_diffs)})"
        )
        logger.debug(f"所有测量值: {[f'{d:.6f}' for d in time_diffs]}")

        return final_time_diff

    def worker(self, user: UserConfig, time_diff: float) -> None:
        logger.info(f"Starting seckill for {user.account_name}...")

        strategy_params = None
        if user.strategy_flag == "mixue" and self.config.mixues:
            strategy_params = self.config.mixues[0]
        elif user.strategy_flag == "BW" and self.config.bw_keywords:
            strategy_params = self.config.bw_keywords
        elif user.strategy_flag and user.strategy_params:
            strategy_params = user.strategy_params

        user.strategy_params = strategy_params
        seckkiller_config = SeckkillerConfig.from_user_config(user, self.config)
        seckkiller_config.time_diff = time_diff  # 添加时间差到配置中
        seckkiller = Seckkiller(config=seckkiller_config)
        seckkiller.run()

    def print_remaining_time(self, time_diff: float) -> None:
        logger.info(f"开始倒计时，目标时间: {self.config.start_time}")

        while True:
            # 使用高精度时间计算
            current_timestamp = time.time()
            adjusted_timestamp = current_timestamp + time_diff
            adjusted_datetime = datetime.fromtimestamp(adjusted_timestamp)

            target_datetime = datetime.combine(date.today(), self.config.start_time)

            # 如果跨天了，调整目标时间
            if adjusted_datetime.date() > date.today():
                target_datetime = target_datetime + timedelta(days=1)

            remaining_seconds = (target_datetime - adjusted_datetime).total_seconds()

            if remaining_seconds <= 0:
                logger.info("Time is up! All processes should start seckill...")
                break

            # 显示更精确的剩余时间
            if remaining_seconds < 10:
                logger.info(f"Remaining time: {remaining_seconds:.3f} seconds")
                # 最后10秒更频繁更新
                time.sleep(0.01)
            elif remaining_seconds < 60:
                logger.info(f"Remaining time: {remaining_seconds:.2f} seconds")
                time.sleep(0.2)
            else:
                time.sleep(1)

    def run(self) -> None:
        # 在主进程中同步时间
        time_diff = self.sync_time()

        timer_process = multiprocessing.Process(
            target=self.print_remaining_time, args=(time_diff,)
        )
        timer_process.start()

        processes = []
        for user in self.config.users:
            p = multiprocessing.Process(target=self.worker, args=(user, time_diff))
            p.start()
            processes.append(p)

        for p in processes:
            p.join()
        timer_process.terminate()
        timer_process.join()

    def stop_all(self):
        """停止所有进程"""
        # 实现停止逻辑
        pass

    async def run_async(self):
        """异步运行方法"""
        self.run()


def main(config_file: str) -> None:
    manager = SeckillManager(config_file=config_file)
    manager.run()


if __name__ == "__main__":
    # start_time = "10:59:59.950"
    config_file = "./kudicookie.json"
    main(config_file)
