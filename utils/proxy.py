"""
代理管理工具

提供代理IP的获取和管理功能
"""

import random
from typing import List, Dict, Optional
from loguru import logger
import requests


class ProxyManager:
    """代理管理器"""

    def __init__(self, proxy_url: str = ""):
        self.proxy_url = proxy_url
        self.proxy_list: List[Dict[str, str]] = []

    def get_proxy_ips(self) -> List[Dict[str, str]]:
        """
        获取代理IP列表

        Returns:
            代理IP列表
        """
        if not self.proxy_url:
            logger.info("未配置代理URL，使用本地IP")
            return []

        try:
            response = requests.get(self.proxy_url, timeout=10)
            data = response.json()

            if data.get("success") and data.get("code") == 0:
                return self._extract_ip_port(data)
            else:
                logger.error(f"获取代理IP失败: {data.get('msg', '未知错误')}")
                return []

        except requests.exceptions.RequestException as e:
            logger.error(f"获取代理IP失败: {e}")
            return []

    def _extract_ip_port(self, json_data: Dict) -> List[Dict[str, str]]:
        """
        从JSON数据中解析出代理IP和端口

        Args:
            json_data: 包含代理信息的JSON数据

        Returns:
            代理列表
        """
        proxies = []
        if not isinstance(json_data, dict):
            return proxies

        for item in json_data.get("data", []):
            ip = item.get("ip")
            port = item.get("port")
            if ip and port:
                proxies.append({"http": f"http://{ip}:{port}"})

        return proxies

    def get_random_proxy(self) -> Optional[Dict[str, str]]:
        """
        随机选择一个代理

        Returns:
            随机代理配置
        """
        if not self.proxy_list:
            return None

        return random.choice(self.proxy_list)

    def refresh_proxies(self) -> bool:
        """
        刷新代理列表

        Returns:
            是否刷新成功
        """
        new_proxies = self.get_proxy_ips()
        if new_proxies:
            self.proxy_list = new_proxies
            logger.info(f"成功获取 {len(self.proxy_list)} 个代理IP")
            return True
        else:
            logger.warning("未获取到代理IP")
            return False

    def is_proxy_available(self) -> bool:
        """
        检查是否有可用代理

        Returns:
            是否有可用代理
        """
        return len(self.proxy_list) > 0
