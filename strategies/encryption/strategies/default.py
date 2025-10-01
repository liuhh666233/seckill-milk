"""
默认加密策略

提供基础的加密功能
"""

import hashlib
from typing import Dict, Any, Tuple
from datetime import datetime
from loguru import logger

from strategies.base import IEncryptionStrategy


class DefaultEncryptionStrategy(IEncryptionStrategy):
    """默认加密策略"""

    def __init__(self, params: Dict[str, Any] = None):
        self.params = params or {}

    def encrypt(
        self, data: Dict[str, Any], current_time: datetime
    ) -> Tuple[str, Dict[str, Any]]:
        """
        默认加密方法（直接返回原数据）

        Args:
            data: 待加密数据
            current_time: 当前时间

        Returns:
            (encrypted_string, encrypted_data) 元组
        """
        logger.debug("使用默认加密策略")
        return "", data

    @staticmethod
    def md5_hash(text: str) -> str:
        """
        计算MD5哈希值

        Args:
            text: 待哈希的文本

        Returns:
            MD5哈希值
        """
        return hashlib.md5(text.encode("utf-8")).hexdigest()

    @staticmethod
    def sha256_hash(text: str) -> str:
        """
        计算SHA256哈希值

        Args:
            text: 待哈希的文本

        Returns:
            SHA256哈希值
        """
        return hashlib.sha256(text.encode("utf-8")).hexdigest()
