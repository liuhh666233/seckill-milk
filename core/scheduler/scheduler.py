"""
秒杀调度器

从原有的scheduler.py重构而来
"""

import argparse
import time
import sys
from datetime import datetime
from loguru import logger

from .task_manager import TaskManager
from core.seckill import SeckillManager
from core.notification import NotificationConfigManager


class SeckillScheduler:
    """秒杀调度器"""

    def __init__(self):
        self.setup_logging()
        self.task_manager = TaskManager()
        self.notification_manager = NotificationConfigManager().initialize_services()

    def setup_logging(self):
        """配置日志"""
        logger.remove()  # 移除默认处理器

        # 添加控制台输出
        logger.add(
            sys.stdout,
            format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            level="INFO",
        )

    def run_task(self, task):
        """运行单个任务"""
        try:
            if not task.enabled:
                logger.info(f"任务已禁用: {task.description}")
                return

            logger.info(f"开始执行任务: {task.description}")
            logger.info(f"配置文件: {task.config_file}")

            manager = SeckillManager(config_file=task.config_file)
            result = manager.run()

            # 发送任务结果通知
            task_info = {
                "description": task.description,
                "start_time": task.start_time.strftime("%H:%M:%S.%f")[:-3],
            }
            # 确保result包含必要信息
            if not isinstance(result, dict):
                result = {"success": True, "message": "任务执行完成"}
            self.notification_manager.notify_task_result(task_info, result)

        except Exception as e:
            logger.error(f"任务执行失败: {str(e)}")
            # 发送错误通知
            task_info = {
                "description": task.description,
                "start_time": task.start_time.strftime("%H:%M:%S.%f")[:-3],
            }
            error_result = {
                "success": False,
                "message": "任务执行失败",
                "details": "任务执行过程中发生错误",
                "failure_reason": str(e),
            }
            self.notification_manager.notify_task_result(task_info, error_result)

    def run_hour_tasks(self, hour: str):
        """运行指定小时的任务"""
        tasks = self.task_manager.get_tasks_by_hour(hour)
        if not tasks:
            logger.warning(f"没有找到 {hour} 点的任务")
            return

        logger.info(f"发现 {len(tasks)} 个任务")
        for task in tasks:
            self.run_task(task)

    def run_current_tasks(self):
        """运行当前小时的任务"""
        current_hour = datetime.now().strftime("%H")
        self.run_hour_tasks(current_hour)

    def watch_mode(self):
        """监视模式：持续运行并在每小时开始时检查任务"""
        logger.info("启动监视模式")

        while True:
            now = datetime.now()

            # 如果是整点运行任务,避免重复运行
            if now.minute == 0 and now.second == 0:
                self.run_current_tasks()
                # 等待1分钟，避免重复运行
                time.sleep(60)
            else:
                # 计算到下一个整点的等待时间
                next_hour = now.replace(
                    hour=now.hour + 1, minute=0, second=0, microsecond=0
                )
                wait_seconds = (next_hour - now).total_seconds()

                logger.info(f"等待下一个整点，剩余 {wait_seconds:.0f} 秒")
                time.sleep(min(wait_seconds, 60))  # 最多等待60秒，保持响应性

    def add_task_interactive(self):
        """交互式添加任务"""
        try:
            hour = input("请输入任务小时(00-23): ").zfill(2)
            start_time = input("请输入开始时间(HH:MM:SS.fff): ")
            config_file = input("请输入配置文件路径: ")
            description = input("请输入任务描述: ")

            from config import TaskSchedule

            task = TaskSchedule(
                start_time=datetime.strptime(start_time, "%H:%M:%S.%f").time(),
                config_file=config_file,
                description=description,
            )
            self.task_manager.add_task(hour, task)
            logger.info("任务添加成功")

        except Exception as e:
            logger.error(f"添加任务失败: {e}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="秒杀任务调度器")
    parser.add_argument(
        "--mode",
        choices=["watch", "now", "hour"],
        default="watch",
        help="运行模式: watch(持续监视) / now(运行当前小时任务) / hour(运行指定小时任务)",
    )
    parser.add_argument("--hour", help="指定运行小时(格式: HH)")
    parser.add_argument("--add", action="store_true", help="添加新任务")

    args = parser.parse_args()
    scheduler = SeckillScheduler()

    try:
        if args.add:
            # 交互式添加任务
            scheduler.add_task_interactive()
            return

        if args.mode == "watch":
            scheduler.watch_mode()
        elif args.mode == "hour" and args.hour:
            scheduler.run_hour_tasks(args.hour.zfill(2))
        else:
            scheduler.run_current_tasks()

    except KeyboardInterrupt:
        logger.info("程序已停止")
    except Exception as e:
        logger.error(f"程序运行出错: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
