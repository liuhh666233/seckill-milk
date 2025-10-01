"""
BW请求策略

实现BW的请求处理逻辑
"""

import json
import hashlib
import base64
from typing import Dict, Any, Tuple
from datetime import datetime
import requests
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

from strategies.base import ISeckillStrategy


class BWRequestStrategy(ISeckillStrategy):
    """BW请求策略"""

    def __init__(self, params: Dict[str, Any] = None):
        self.params = params or {}
        self._current_kw_index = 0
        self._key_words = self.params.get("bw_keywords", "")

    def _get_current_keyword(self, keywords_str: str) -> str:
        """获取当前关键词"""
        keywords_list = [kw.strip() for kw in keywords_str.split(",")]
        if self._current_kw_index >= len(keywords_list):
            self._current_kw_index = 0
        kw = keywords_list[self._current_kw_index]
        self._current_kw_index += 1
        return kw

    def _build_signature(self, activity_id: str, user_id: str, timestamp: str) -> str:
        """构建签名"""
        key = activity_id[::-1]
        signature_str = f"activityId={activity_id}&sellerId=49006&timestamp={timestamp}&userId={user_id}&key={key}"
        return hashlib.md5(signature_str.encode("utf-8")).hexdigest().upper()

    def _encrypt_request_data(self, request_data: Dict, key: str, iv: str) -> str:
        """加密请求数据"""
        json_data = json.dumps(request_data, ensure_ascii=False, separators=(",", ":"))
        cipher = AES.new(key.encode(), AES.MODE_CBC, iv.encode())
        padded_data = pad(json_data.encode("utf-8"), AES.block_size)
        encrypted_data = cipher.encrypt(padded_data)
        return base64.b64encode(encrypted_data).decode("utf-8")

    def _get_encryption_params(self, process_data: Dict) -> str:
        """获取加密参数"""
        url = "http://192.168.31.186:3001/api/encrypt"
        payload = json.dumps(process_data)
        headers = {"Content-Type": "application/json"}
        response = requests.post(url, headers=headers, data=payload)
        params = response.json().get("data", {}).get("encrypted")
        if not params:
            raise ValueError("Encryption failed - no result returned")
        return params

    def prepare_request(
        self,
        current_time: datetime,
        data: Dict[str, Any],
        headers: Dict[str, str],
        base_url: str,
    ) -> Tuple[str, Dict[str, Any], Dict[str, str]]:
        """
        准备BW请求参数

        Args:
            current_time: 当前时间
            data: 请求数据
            headers: 请求头
            base_url: 基础URL

        Returns:
            (url, data, headers) 元组
        """
        kw = self._get_current_keyword(self._key_words)
        activity_id = data.get("activityId")
        signature = self._build_signature(
            activity_id, data.get("userId"), str(current_time)
        )

        request_data = {
            "activityId": activity_id,
            "keyWords": kw,
            "qzGtd": "",
            "gdtVid": "",
            "appid": "wxafec6f8422cb357b",
            "timestamp": current_time,
            "signature": signature,
        }

        encrypted_data = self._encrypt_request_data(
            request_data, data.get("key"), data.get("iv")
        )

        process_data = {
            **request_data,
            "data": encrypted_data,
            "version": data.get("version"),
        }

        params = self._get_encryption_params(process_data)
        process_url = f"{base_url}?type__1475={params}"
        process_data = json.dumps(
            process_data, separators=(",", ":"), ensure_ascii=False
        ).encode("utf-8")

        return process_url, process_data, headers

    def process_response(self, response: requests.Response) -> Dict[str, Any]:
        """
        处理BW响应数据

        Args:
            response: HTTP响应对象

        Returns:
            处理后的响应数据
        """
        try:
            return response.json()
        except Exception:
            return {"error": "响应解析失败", "text": response.text}
