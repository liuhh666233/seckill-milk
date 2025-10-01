"""
秒杀管理器

从原有的managerun.py重构而来
"""

import time
import multiprocessing
from datetime import datetime, date, timedelta
from typing import Dict, Optional
from loguru import logger

from config import ConfigManager, SeckillConfig, UserConfig
from utils import TimeSynchronizer
from .executor import SeckillExecutor
from core.notification import NotificationConfigManager


class SeckillManager:
    """秒杀管理器"""

    def __init__(
        self, config: Optional[Dict] = None, config_file: Optional[str] = None
    ):
        self.config_manager = ConfigManager()
        self.notification_manager = NotificationConfigManager().initialize_services()

        if config:
            self.config = SeckillConfig.from_dict(config)
        elif config_file:
            self.config = self.config_manager.load_seckill_config(config_file)
        else:
            raise ValueError("必须提供 config 或 config_file 参数")

    def sync_time(self) -> float:
        """同步时间，返回时间差"""
        time_synchronizer = TimeSynchronizer()
        return time_synchronizer.sync_time()

    def worker(self, user: UserConfig, time_diff: float) -> None:
        """工作进程"""
        logger.info(f"开始秒杀: {user.account_name}")

        # 设置策略参数
        strategy_params = None
        if user.strategy_flag == "mixue" and self.config.mixues:
            strategy_params = self.config.mixues[0]
        elif user.strategy_flag == "BW" and self.config.bw_keywords:
            strategy_params = {"bw_keywords": self.config.bw_keywords}
        elif user.strategy_flag and user.strategy_params:
            strategy_params = user.strategy_params

        user.strategy_params = strategy_params

        # 创建秒杀执行器
        executor = SeckillExecutor(
            user_config=user,
            global_config=self.config,
            time_diff=time_diff,
            notification_manager=self.notification_manager,
        )

        executor.run()

    def print_remaining_time(self, time_diff: float) -> None:
        """打印剩余时间"""
        logger.info(f"开始倒计时，目标时间: {self.config.start_time}")

        time_synchronizer = TimeSynchronizer()

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
                logger.info("时间到！所有进程应该开始秒杀...")
                break

            # 显示更精确的剩余时间
            if remaining_seconds < 10:
                logger.info(f"剩余时间: {remaining_seconds:.3f} 秒")
                # 最后10秒更频繁更新
                time.sleep(0.01)
            elif remaining_seconds < 60:
                logger.info(f"剩余时间: {remaining_seconds:.2f} 秒")
                time.sleep(0.2)
            else:
                time.sleep(1)

    def run(self) -> None:
        """运行秒杀管理器"""
        # 在主进程中同步时间
        time_diff = self.sync_time()

        # 启动倒计时进程
        timer_process = multiprocessing.Process(
            target=self.print_remaining_time, args=(time_diff,)
        )
        timer_process.start()

        # 启动用户工作进程
        processes = []
        for user in self.config.users:
            p = multiprocessing.Process(target=self.worker, args=(user, time_diff))
            p.start()
            processes.append(p)

        # 等待所有进程完成
        for p in processes:
            p.join()

        # 终止倒计时进程
        timer_process.terminate()
        timer_process.join()

    def stop_all(self):
        """停止所有进程"""
        # TODO: 实现停止逻辑
        pass

    async def run_async(self):
        """异步运行方法"""
        self.run()
