"""
配置验证器

提供配置数据的验证功能
"""

from typing import Dict, Any, List
from loguru import logger


class ConfigValidator:
    """配置验证器"""

    def validate_seckill_config(self, config: Dict[str, Any]) -> bool:
        """
        验证秒杀配置

        Args:
            config: 配置字典

        Returns:
            是否有效
        """
        try:
            # 验证必需字段
            required_fields = ["start_time", "users"]
            for field in required_fields:
                if field not in config:
                    logger.error(f"缺少必需字段: {field}")
                    return False

            # 验证时间格式
            if not self._validate_time_format(config["start_time"]):
                logger.error("时间格式无效")
                return False

            # 验证用户配置
            if not isinstance(config["users"], list):
                logger.error("users 必须是列表")
                return False

            for i, user in enumerate(config["users"]):
                if not self._validate_user_config(user, i):
                    return False

            # 验证代理配置
            if "proxies" in config and not isinstance(config["proxies"], str):
                logger.error("proxies 必须是字符串")
                return False

            return True

        except Exception as e:
            logger.error(f"配置验证异常: {e}")
            return False

    def _validate_time_format(self, time_str: str) -> bool:
        """验证时间格式"""
        try:
            from datetime import datetime

            datetime.strptime(time_str, "%H:%M:%S.%f")
            return True
        except ValueError:
            return False

    def _validate_user_config(self, user: Dict[str, Any], index: int) -> bool:
        """验证用户配置"""
        required_user_fields = [
            "account_name",
            "cookie_id",
            "cookie_name",
            "basurl",
            "headers",
            "data",
        ]

        for field in required_user_fields:
            if field not in user:
                logger.error(f"用户 {index} 缺少必需字段: {field}")
                return False

        # 验证数据类型
        if not isinstance(user["headers"], dict):
            logger.error(f"用户 {index} headers 必须是字典")
            return False

        if not isinstance(user["data"], dict):
            logger.error(f"用户 {index} data 必须是字典")
            return False

        if "max_attempts" in user and not isinstance(user["max_attempts"], int):
            logger.error(f"用户 {index} max_attempts 必须是整数")
            return False

        if "thread_count" in user and not isinstance(user["thread_count"], int):
            logger.error(f"用户 {index} thread_count 必须是整数")
            return False

        if "request_interval" in user and not isinstance(user["request_interval"], (int, float)):
            logger.error(f"用户 {index} request_interval 必须是数字")
            return False

        if "request_interval" in user and user["request_interval"] <= 0:
            logger.error(f"用户 {index} request_interval 必须大于0")
            return False

        return True

    def validate_schedule_config(self, config: Dict[str, Any]) -> bool:
        """
        验证调度配置

        Args:
            config: 配置字典

        Returns:
            是否有效
        """
        try:
            for hour_str, tasks in config.items():
                # 验证小时格式
                if not hour_str.isdigit() or not (0 <= int(hour_str) <= 23):
                    logger.error(f"无效的小时格式: {hour_str}")
                    return False

                if not isinstance(tasks, list):
                    logger.error(f"小时 {hour_str} 的任务必须是列表")
                    return False

                for i, task in enumerate(tasks):
                    if not self._validate_task_config(task, hour_str, i):
                        return False

            return True

        except Exception as e:
            logger.error(f"调度配置验证异常: {e}")
            return False

    def _validate_task_config(
        self, task: Dict[str, Any], hour: str, index: int
    ) -> bool:
        """验证任务配置"""
        required_fields = ["start_time", "config_file"]

        for field in required_fields:
            if field not in task:
                logger.error(f"任务 {hour}:{index} 缺少必需字段: {field}")
                return False

        # 验证时间格式
        if not self._validate_time_format(task["start_time"]):
            logger.error(f"任务 {hour}:{index} 时间格式无效")
            return False

        # 验证配置文件路径
        if not isinstance(task["config_file"], str):
            logger.error(f"任务 {hour}:{index} config_file 必须是字符串")
            return False

        return True
