import requests
import hashlib
import logging
import base64
import hmac
import time
from loguru import logger

LARK_CONFIG = {
    "SECKILL": {
        "LARK_URL": "",
        "LARK_SIGN": "",
    },
}


def _gen_sign(timestamp: int, secret: str) -> str:
    # 拼接timestamp和secret
    string_to_sign = "{}\n{}".format(timestamp, secret)
    hmac_code = hmac.new(
        string_to_sign.encode("utf-8"), digestmod=hashlib.sha256
    ).digest()
    # 对结果进行base64处理
    sign = base64.b64encode(hmac_code).decode("utf-8")
    return sign


def send_message(environ: str = "SECKILL", message: str = "") -> bool:
    """
    return: 返回消息发送结果
    environ: 指定需要发送消息的lark群组, 分别有QUANT TRADING TEST NOTICE
    message: 设置消息内容
    """
    try:
        lark_config = LARK_CONFIG.get(environ)

        if lark_config is None:
            logger.error(f"Do not exists the config of {environ}. Please check.")
            return False

        url = lark_config.get("LARK_URL")

        timestamp = int(time.time())

        sign = _gen_sign(timestamp, lark_config.get("LARK_SIGN"))

        content = {
            "timestamp": str(timestamp),
            "sign": str(sign),
            "msg_type": "text",
            "content": {"text": message},
        }

        result = requests.post(url, json=content)

        if result.status_code == 200:
            logger.info("Message had been successfully sent to lark.")
            return True
        logger.error(
            f"Message failed to be sent to lark. Exists error as follows {result}."
        )
        return False

    except Exception as e:
        logger.error(f"Message failed to be sent to lark. Exists error as follows {e}.")
        return False
