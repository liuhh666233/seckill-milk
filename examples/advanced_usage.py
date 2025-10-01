"""
高级使用示例

展示重构后系统的高级功能
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.seckill import SeckillManager
from strategies import RequestStrategyManager, EncryptionStrategyManager
from config import ConfigManager, UserConfig, SeckillConfig
from core.notification import NotificationManager, LarkNotificationService
from datetime import time


def custom_strategy_example():
    """自定义策略示例"""
    print("=== 自定义策略示例 ===")

    # 创建策略管理器
    request_manager = RequestStrategyManager()
    encryption_manager = EncryptionStrategyManager()

    # 查看可用策略
    print("可用请求策略:", request_manager.list_strategies())
    print("可用加密策略:", encryption_manager.list_strategies())

    # 更新策略参数
    mixue_params = {
        "marketingId": "test_id",
        "round": "test_round",
        "secretword": "test_word",
    }
    request_manager.update_strategy_params("mixue", mixue_params)
    print("蜜雪冰城策略参数已更新")


def multi_user_example():
    """多用户配置示例"""
    print("=== 多用户配置示例 ===")

    # 创建用户配置
    user1 = UserConfig(
        account_name="用户1",
        cookie_id="cookie_id_1",
        cookie_name="cookie",
        basurl="https://example.com/api",
        headers={"User-Agent": "Mozilla/5.0"},
        data={"param1": "value1"},
        max_attempts=5,
        thread_count=2,
        strategy_flag="default",
    )

    user2 = UserConfig(
        account_name="用户2",
        cookie_id="cookie_id_2",
        cookie_name="cookie",
        basurl="https://example.com/api",
        headers={"User-Agent": "Mozilla/5.0"},
        data={"param2": "value2"},
        max_attempts=3,
        thread_count=1,
        strategy_flag="mixue",
        strategy_params={"marketingId": "test"},
    )

    # 创建秒杀配置
    config = SeckillConfig(
        start_time=time(12, 0, 0, 0),
        proxies="http://proxy.example.com",
        users=[user1, user2],
    )

    # 运行秒杀
    manager = SeckillManager(config=config)
    print(f"配置了 {len(config.users)} 个用户")


def notification_management_example():
    """通知管理示例"""
    print("=== 通知管理示例 ===")

    # 创建通知管理器
    notification_manager = NotificationManager()

    # 注册多个通知服务
    lark_service = LarkNotificationService(
        webhook_url="https://open.larksuite.com/open-apis/bot/v2/hook/xxx",
        secret="your_secret",
    )
    notification_manager.register_service("lark", lark_service)

    # 检查可用服务
    available_services = notification_manager.get_available_services()
    print(f"可用通知服务: {available_services}")

    # 发送不同类型的通知
    notification_manager.send_message("普通消息")
    notification_manager.notify_task_result(
        {"task": "测试任务", "status": "完成"},
        {"success": True, "message": "任务执行成功"},
    )


def config_validation_example():
    """配置验证示例"""
    print("=== 配置验证示例 ===")

    config_manager = ConfigManager()

    # 创建测试配置
    test_config = {
        "start_time": "12:00:00.000",
        "proxies": "http://proxy.example.com",
        "users": [
            {
                "account_name": "测试用户",
                "cookie_id": "test_cookie",
                "cookie_name": "cookie",
                "basurl": "https://example.com",
                "headers": {"User-Agent": "Mozilla/5.0"},
                "data": {"param": "value"},
                "max_attempts": 5,
                "thread_count": 1,
            }
        ],
    }

    # 验证配置
    is_valid = config_manager.validate_config(test_config)
    print(f"配置验证结果: {is_valid}")

    # 保存配置
    config_manager.save_config(test_config, "./examples/test_config.json")
    print("测试配置已保存")


def error_handling_example():
    """错误处理示例"""
    print("=== 错误处理示例 ===")

    try:
        # 尝试加载不存在的配置文件
        config_manager = ConfigManager()
        config = config_manager.load_seckill_config("./nonexistent.json")
    except FileNotFoundError as e:
        print(f"文件未找到: {e}")
    except Exception as e:
        print(f"其他错误: {e}")

    try:
        # 尝试使用无效配置
        invalid_config = {"invalid": "config"}
        config_manager = ConfigManager()
        is_valid = config_manager.validate_config(invalid_config)
        print(f"无效配置验证结果: {is_valid}")
    except Exception as e:
        print(f"配置验证错误: {e}")


if __name__ == "__main__":
    print("秒杀系统高级使用示例")
    print("=" * 50)

    try:
        custom_strategy_example()
        print()

        multi_user_example()
        print()

        notification_management_example()
        print()

        config_validation_example()
        print()

        error_handling_example()

    except Exception as e:
        print(f"示例运行失败: {e}")
        import traceback

        traceback.print_exc()
