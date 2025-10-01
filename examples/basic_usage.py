"""
基础使用示例

展示如何使用重构后的秒杀系统
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.seckill import SeckillManager
from core.scheduler import SeckillScheduler
from config import ConfigManager


def basic_seckill_example():
    """基础秒杀示例"""
    print("=== 基础秒杀示例 ===")

    # 使用配置文件
    config_file = "./kudicookie.json"
    manager = SeckillManager(config_file=config_file)
    manager.run()


def scheduler_example():
    """调度器示例"""
    print("=== 调度器示例 ===")

    scheduler = SeckillScheduler()

    # 运行当前小时的任务
    scheduler.run_current_tasks()

    # 或者运行指定小时的任务
    # scheduler.run_hour_tasks("10")

    # 或者启动监视模式
    # scheduler.watch_mode()


def config_management_example():
    """配置管理示例"""
    print("=== 配置管理示例 ===")

    config_manager = ConfigManager()

    # 加载配置
    config = config_manager.load_seckill_config("./kudicookie.json")
    print(f"配置加载成功，用户数量: {len(config.users)}")

    # 验证配置
    is_valid = config_manager.validate_config(config.__dict__)
    print(f"配置验证结果: {is_valid}")

    # 创建默认配置
    config_manager.create_default_config("./examples/default_config.json")


def notification_example():
    """通知示例"""
    print("=== 通知示例 ===")

    from core.notification import NotificationManager, LarkNotificationService

    # 创建通知管理器
    notification_manager = NotificationManager()

    # 注册飞书通知服务
    lark_service = LarkNotificationService(
        webhook_url="your_webhook_url", secret="your_secret"
    )
    notification_manager.register_service("lark", lark_service, is_default=True)

    # 发送通知
    notification_manager.send_message("测试消息")


if __name__ == "__main__":
    print("秒杀系统使用示例")
    print("=" * 50)

    # 运行示例
    try:
        # basic_seckill_example()
        # scheduler_example()
        config_management_example()
        # notification_example()

    except Exception as e:
        print(f"示例运行失败: {e}")
        import traceback

        traceback.print_exc()
