"""
美团请求策略

实现美团的请求处理逻辑
"""

import json
from typing import Dict, Any, Tuple
from datetime import datetime
from urllib.parse import urlparse, parse_qs
import requests

from strategies.base import ISeckillStrategy


class MTRequestStrategy(ISeckillStrategy):
    """美团请求策略"""

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
        准备美团请求参数

        Args:
            current_time: 当前时间
            data: 请求数据
            headers: 请求头
            base_url: 基础URL

        Returns:
            (url, data, headers) 元组
        """
        # 美团策略：处理数据格式
        process_data = json.dumps(data, separators=(",", ":"), ensure_ascii=False)
        return base_url, process_data, headers

    def process_response(self, response: requests.Response) -> Dict[str, Any]:
        """
        处理美团响应数据

        Args:
            response: HTTP响应对象

        Returns:
            处理后的响应数据
        """
        try:
            res = response.json()
            return res["data"]["coupon"]
        except Exception:
            return {"error": "响应解析失败", "text": response.text}

    def get_coupon_info(self, headers: Dict[str, str], base_url: str) -> Dict[str, Any]:
        """
        获取优惠券信息

        Args:
            headers: 请求头
            base_url: 基础URL

        Returns:
            优惠券信息
        """
        try:
            parsed_url = urlparse(base_url)
            query_params = parse_qs(parsed_url.query)
            coupon_id = query_params.get("couponReferId")[0]
            cookie = headers["cookie"]

            url = f"https://promotion.waimai.meituan.com/lottery/limitcouponcomponent/info?couponReferIds={coupon_id}&actualLng=118.33515&actualLat=35.04518&geoType=2"

            headers_temp = {
                "dj-token": "",
                "User-Agent": "Mozilla/5.0 (Linux; Android 13; MI 6 Build/TQ2A.230405.003.E1; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/112.0.5615.136 Mobile Safari/537.36 TitansX/12.9.1 KNB/1.2.0 android/13 mt/com.sankuai.meituan/12.9.404 App/10120/12.9.404 MeituanGroup/12.9.404",
                "Content-Type": "application/json",
                "X-Requested-With": "com.sankuai.meituan",
                "Sec-Fetch-Site": "same-site",
                "Sec-Fetch-Mode": "cors",
                "mtgsig": "",
                "Sec-Fetch-Dest": "empty",
                "Cookie": cookie,
            }

            response = requests.get(url=url, headers=headers_temp)
            if response.status_code == 200:
                return response.json()
            else:
                return None

        except Exception as e:
            from loguru import logger

            logger.error(f"获取优惠券信息失败: {e}")
            return None
