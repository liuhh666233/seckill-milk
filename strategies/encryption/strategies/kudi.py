"""
库迪咖啡加密策略

实现库迪咖啡的加密算法
"""

import hashlib
from typing import Dict, Any, Tuple
from datetime import datetime
from loguru import logger

from strategies.base import IEncryptionStrategy


class KuDiEncryptionStrategy(IEncryptionStrategy):
    """库迪咖啡加密策略"""

    def __init__(self, params: Dict[str, Any] = None):
        self.params = params or {}

    def encrypt(
        self, data: Dict[str, Any], current_time: datetime
    ) -> Tuple[str, Dict[str, Any]]:
        """
        库迪咖啡加密方法

        Args:
            data: 待加密数据
            current_time: 当前时间

        Returns:
            (encrypted_string, encrypted_data) 元组
        """
        try:
            timestamp = int(current_time.timestamp() * 1000)

            # 库迪咖啡的签名算法
            kudi_params = f"path/cotti-capi/universal/coupon/receiveLaunchRewardH5timestamp{timestamp}versionv1Bu0Zsh4B0SnKBRfds0XWCSn51WJfn5yN"
            sign = hashlib.md5(kudi_params.encode("utf-8")).hexdigest().upper()

            # 构建加密数据
            encrypted_data = {"timestamp": timestamp, "sign": sign, "version": "v1"}

            return sign, encrypted_data

        except Exception as e:
            logger.error(f"库迪咖啡加密失败: {e}")
            return "", data

    def is_available(self) -> bool:
        """
        检查策略是否可用

        Returns:
            是否可用
        """
        return True
