"""
配置管理器

提供配置的加载、验证和保存功能
"""

import json
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List
from loguru import logger

from .base import IConfigManager, SeckillConfig, TaskSchedule
from .validators import ConfigValidator


class ConfigManager(IConfigManager):
    """配置管理器实现"""

    def __init__(self):
        self.validator = ConfigValidator()

    def load_config(self, config_path: str) -> Dict[str, Any]:
        """
        加载配置文件

        Args:
            config_path: 配置文件路径

        Returns:
            配置字典
        """
        try:
            config_file = Path(config_path)
            if not config_file.exists():
                raise FileNotFoundError(f"配置文件不存在: {config_path}")

            with open(config_file, "r", encoding="utf-8") as f:
                if (
                    config_file.suffix.lower() == ".yaml"
                    or config_file.suffix.lower() == ".yml"
                ):
                    return yaml.safe_load(f)
                else:
                    return json.load(f)

        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            raise

    def validate_config(self, config: Dict[str, Any]) -> bool:
        """
        验证配置有效性

        Args:
            config: 配置字典

        Returns:
            是否有效
        """
        try:
            return self.validator.validate_seckill_config(config)
        except Exception as e:
            logger.error(f"配置验证失败: {e}")
            return False

    def save_config(self, config: Dict[str, Any], config_path: str) -> bool:
        """
        保存配置文件

        Args:
            config: 配置字典
            config_path: 配置文件路径

        Returns:
            是否保存成功
        """
        try:
            config_file = Path(config_path)
            config_file.parent.mkdir(parents=True, exist_ok=True)

            with open(config_file, "w", encoding="utf-8") as f:
                if (
                    config_file.suffix.lower() == ".yaml"
                    or config_file.suffix.lower() == ".yml"
                ):
                    yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
                else:
                    json.dump(config, f, indent=4, ensure_ascii=False)

            logger.info(f"配置已保存到: {config_path}")
            return True

        except Exception as e:
            logger.error(f"保存配置文件失败: {e}")
            return False

    def load_seckill_config(self, config_path: str) -> SeckillConfig:
        """
        加载秒杀配置

        Args:
            config_path: 配置文件路径

        Returns:
            秒杀配置对象
        """
        config_dict = self.load_config(config_path)
        if not self.validate_config(config_dict):
            raise ValueError("配置验证失败")

        return SeckillConfig.from_dict(config_dict)

    def load_schedule_config(self, schedule_path: str) -> Dict[str, List[TaskSchedule]]:
        """
        加载调度配置

        Args:
            schedule_path: 调度配置文件路径

        Returns:
            调度配置字典
        """
        from datetime import datetime

        config_dict = self.load_config(schedule_path)
        schedules = {}

        for hour_str, tasks in config_dict.items():
            schedules[hour_str] = [
                TaskSchedule(
                    start_time=datetime.strptime(
                        task["start_time"], "%H:%M:%S.%f"
                    ).time(),
                    config_file=task["config_file"],
                    enabled=task.get("enabled", True),
                    description=task.get("description", ""),
                )
                for task in tasks
            ]

        return schedules

    def create_default_config(self, config_path: str) -> bool:
        """
        创建默认配置文件

        Args:
            config_path: 配置文件路径

        Returns:
            是否创建成功
        """
        default_config = {
            "start_time": "00:00:00.000",
            "proxies": "",
            "users": [],
            "mixues": [],
            "bw_keywords": "",
        }

        return self.save_config(default_config, config_path)
