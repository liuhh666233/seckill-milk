"""
蜜雪冰城请求策略

实现蜜雪冰城的请求处理逻辑
"""

import hashlib
import json
from typing import Dict, Any, Tuple
from datetime import datetime
import requests

from strategies.base import ISeckillStrategy
from utils.js_executor import JavaScriptExecutor


class MixueRequestStrategy(ISeckillStrategy):
    """蜜雪冰城请求策略"""

    def __init__(self, params: Dict[str, Any] = None):
        self.params = params or {}
        self.encryption_js = None
        self._init_js_executor()

    def _init_js_executor(self):
        """初始化JavaScript执行器"""
        try:
            self.encryption_js = JavaScriptExecutor("./js/mixue.js")
        except Exception as e:
            from loguru import logger

            logger.warning(f"初始化JavaScript执行器失败: {e}")
            self.encryption_js = None

    def prepare_request(
        self,
        current_time: datetime,
        data: Dict[str, Any],
        headers: Dict[str, str],
        base_url: str,
    ) -> Tuple[str, Dict[str, Any], Dict[str, str]]:
        """
        准备蜜雪冰城请求参数

        Args:
            current_time: 当前时间
            data: 请求数据
            headers: 请求头
            base_url: 基础URL

        Returns:
            (url, data, headers) 元组
        """
        marketing_id = self.params.get("marketingId", "")
        round_num = self.params.get("round", "")
        secret_word = self.params.get("secretword", "")
        timestamp = int(current_time.timestamp() * 1000)

        # 构建签名参数
        param = f"marketingId={marketing_id}&round={round_num}&s=2&secretword={secret_word}&stamp={timestamp}c274bac6493544b89d9c4f9d8d542b84"
        sign = hashlib.md5(param.encode("utf-8")).hexdigest()

        # 构建请求数据
        mixue_data = {
            "marketingId": marketing_id,
            "round": round_num,
            "secretword": secret_word,
            "sign": sign,
            "s": 2,
            "stamp": timestamp,
        }

        # 使用JavaScript执行器进行加密
        if self.encryption_js and self.encryption_js.is_available():
            encrypted_str = f'https://mxsa.mxbc.net/api/v1/h5/marketing/secretword/confirm{{"marketingId":"{marketing_id}","round":"{round_num}","secretword":"{secret_word}","sign":"{sign}","s":2,"stamp":{timestamp}}}'
            encrypted_str = self.encryption_js.call("get_sig", encrypted_str)
        else:
            from loguru import logger

            logger.warning("JavaScript执行器不可用，使用基础加密")
            encrypted_str = f"mixue_encrypted_{timestamp}"

        new_url = f"{base_url}?type__1286={encrypted_str}"
        return new_url, mixue_data, headers

    def process_response(self, response: requests.Response) -> Dict[str, Any]:
        """
        处理蜜雪冰城响应数据

        Args:
            response: HTTP响应对象

        Returns:
            处理后的响应数据
        """
        try:
            return response.json()
        except Exception:
            return {"error": "响应解析失败", "text": response.text}
