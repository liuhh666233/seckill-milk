"""
配置基类定义

定义配置相关的抽象接口和基础类
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import time


class IConfigManager(ABC):
    """配置管理接口"""

    @abstractmethod
    def load_config(self, config_path: str) -> Dict[str, Any]:
        """加载配置文件"""
        pass

    @abstractmethod
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """验证配置有效性"""
        pass

    @abstractmethod
    def save_config(self, config: Dict[str, Any], config_path: str) -> bool:
        """保存配置文件"""
        pass


@dataclass
class UserConfig:
    """用户配置"""

    account_name: str
    cookie_id: str
    cookie_name: str
    basurl: str
    headers: Dict[str, str]
    data: Dict[str, Any]
    max_attempts: int = 10
    thread_count: int = 5
    key_value: str = ""
    key_message: str = ""
    proxy_flag: bool = False
    strategy_flag: Optional[str] = None
    strategy_params: Optional[Dict[str, Any]] = None


@dataclass
class SeckillConfig:
    """秒杀配置"""

    start_time: time
    proxies: str
    users: List[UserConfig]
    mixues: List[Dict[str, str]] = None
    bw_keywords: str = ""

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "SeckillConfig":
        """从字典创建配置对象"""
        from datetime import datetime

        start_time = datetime.strptime(
            config_dict.get("start_time", ""), "%H:%M:%S.%f"
        ).time()

        users = [UserConfig(**user_dict) for user_dict in config_dict.get("users", [])]

        return cls(
            start_time=start_time,
            proxies=config_dict.get("proxies", ""),
            users=users,
            mixues=config_dict.get("mixues", []),
            bw_keywords=config_dict.get("bw_keywords", ""),
        )


@dataclass
class TaskSchedule:
    """任务调度配置"""

    start_time: time
    config_file: str
    enabled: bool = True
    description: str = ""


class BaseConfig(ABC):
    """配置基类"""

    def __init__(self, config_data: Dict[str, Any]):
        self.config_data = config_data
        self._validate()

    @abstractmethod
    def _validate(self) -> None:
        """验证配置数据"""
        pass

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        return self.config_data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """设置配置值"""
        self.config_data[key] = value
