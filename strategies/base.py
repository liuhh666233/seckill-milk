"""
策略基类定义

定义所有策略的抽象接口
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple, Optional
from datetime import datetime
import requests


class ISeckillStrategy(ABC):
    """秒杀策略接口"""

    @abstractmethod
    def prepare_request(
        self,
        current_time: datetime,
        data: Dict[str, Any],
        headers: Dict[str, str],
        base_url: str,
    ) -> Tuple[str, Dict[str, Any], Dict[str, str]]:
        """
        准备请求参数

        Args:
            current_time: 当前时间
            data: 请求数据
            headers: 请求头
            base_url: 基础URL

        Returns:
            (url, data, headers) 元组
        """
        pass

    @abstractmethod
    def process_response(self, response: requests.Response) -> Dict[str, Any]:
        """
        处理响应数据

        Args:
            response: HTTP响应对象

        Returns:
            处理后的响应数据
        """
        pass


class IEncryptionStrategy(ABC):
    """加密策略接口"""

    @abstractmethod
    def encrypt(
        self, data: Dict[str, Any], current_time: datetime
    ) -> Tuple[str, Dict[str, Any]]:
        """
        加密数据

        Args:
            data: 待加密数据
            current_time: 当前时间

        Returns:
            (encrypted_string, encrypted_data) 元组
        """
        pass


class IRequestStrategy(ABC):
    """请求策略接口"""

    @abstractmethod
    def make_request(
        self,
        url: str,
        data: Dict[str, Any],
        headers: Dict[str, str],
        proxies: Optional[Dict[str, str]] = None,
    ) -> requests.Response:
        """
        发送请求

        Args:
            url: 请求URL
            data: 请求数据
            headers: 请求头
            proxies: 代理配置

        Returns:
            HTTP响应对象
        """
        pass
