"""
库迪咖啡请求策略

实现库迪咖啡的请求处理逻辑
"""

import json
import hashlib
from typing import Dict, Any, Tuple
from datetime import datetime
import requests

from strategies.base import ISeckillStrategy


class KuDiRequestStrategy(ISeckillStrategy):
    """库迪咖啡请求策略"""

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
        准备库迪咖啡请求参数

        Args:
            current_time: 当前时间
            data: 请求数据
            headers: 请求头
            base_url: 基础URL

        Returns:
            (url, data, headers) 元组
        """
        timestamp = int(current_time.timestamp() * 1000)

        # 库迪咖啡的签名算法
        kudi_params = f"path/cotti-capi/universal/coupon/receiveLaunchRewardH5timestamp{timestamp}versionv1Bu0Zsh4B0SnKBRfds0XWCSn51WJfn5yN"
        encrypted_sign = hashlib.md5(kudi_params.encode("utf-8")).hexdigest().upper()

        # 更新请求头
        headers["sign"] = encrypted_sign
        headers["timestamp"] = str(timestamp)

        # 处理请求数据
        process_data = json.dumps(data, separators=(",", ":"), ensure_ascii=False)

        return base_url, process_data, headers

    def process_response(self, response: requests.Response) -> Dict[str, Any]:
        """
        处理库迪咖啡响应数据

        Args:
            response: HTTP响应对象

        Returns:
            处理后的响应数据
        """
        try:
            res = response.json()
            return res.get("data", res)
        except Exception:
            return {"error": "响应解析失败", "text": response.text}
