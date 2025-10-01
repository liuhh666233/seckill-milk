"""
京东请求策略

实现京东的请求处理逻辑
"""

from typing import Dict, Any, Tuple
from datetime import datetime
import requests

from strategies.base import ISeckillStrategy


class JDRequestStrategy(ISeckillStrategy):
    """京东请求策略"""

    def __init__(self, params: Dict[str, Any] = None):
        self.params = params or {}

    def prepare_request(
        self,
        current_time: datetime,
        data: Dict[str, Any],
        headers: Dict[str, str],
        base_url: str,
    ) -> Tuple[str, Dict[str, Any], Dict[str, str]]:
        """
        准备京东请求参数

        Args:
            current_time: 当前时间
            data: 请求数据
            headers: 请求头
            base_url: 基础URL

        Returns:
            (url, data, headers) 元组
        """
        # 京东策略：直接返回原参数
        return base_url, data, headers

    def process_response(self, response: requests.Response) -> Dict[str, Any]:
        """
        处理京东响应数据

        Args:
            response: HTTP响应对象

        Returns:
            处理后的响应数据
        """
        try:
            res = response.json()
            if "data" in res:
                return res["data"]
            else:
                return res
        except Exception:
            return {"error": "响应解析失败", "text": response.text}
