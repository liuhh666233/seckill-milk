"""
蜜雪冰城加密策略

实现蜜雪冰城的加密算法
"""

import hashlib
from typing import Dict, Any, Tuple
from datetime import datetime
from loguru import logger

from strategies.base import IEncryptionStrategy
from utils.js_executor import JavaScriptExecutor


class MixueEncryptionStrategy(IEncryptionStrategy):
    """蜜雪冰城加密策略"""

    def __init__(self, params: Dict[str, Any] = None):
        self.params = params or {}
        self.encryption_js = None
        self._init_js_executor()

    def _init_js_executor(self):
        """初始化JavaScript执行器"""
        try:
            self.encryption_js = JavaScriptExecutor("./js/mixue.js")
        except Exception as e:
            logger.warning(f"初始化JavaScript执行器失败: {e}")
            self.encryption_js = None

    def encrypt(
        self, data: Dict[str, Any], current_time: datetime
    ) -> Tuple[str, Dict[str, Any]]:
        """
        蜜雪冰城加密方法

        Args:
            data: 待加密数据
            current_time: 当前时间

        Returns:
            (encrypted_string, encrypted_data) 元组
        """
        try:
            marketing_id = self.params.get("marketingId", "")
            round_num = self.params.get("round", "")
            secret_word = self.params.get("secretword", "")
            timestamp = int(current_time.timestamp() * 1000)

            # 构建签名参数
            param = f"marketingId={marketing_id}&round={round_num}&s=2&secretword={secret_word}&stamp={timestamp}c274bac6493544b89d9c4f9d8d542b84"
            sign = hashlib.md5(param.encode("utf-8")).hexdigest()

            # 构建加密数据
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
                logger.warning("JavaScript执行器不可用，使用基础加密")
                encrypted_str = f"mixue_encrypted_{timestamp}"

            return encrypted_str, mixue_data

        except Exception as e:
            logger.error(f"蜜雪冰城加密失败: {e}")
            return "", data

    def is_available(self) -> bool:
        """
        检查策略是否可用

        Returns:
            是否可用
        """
        return self.encryption_js is not None and self.encryption_js.is_available()
