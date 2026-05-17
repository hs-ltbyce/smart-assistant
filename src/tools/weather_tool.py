"""第2阶段：天气查询工具（wttr.in）。"""

from __future__ import annotations

from typing import Any

import requests
from langchain.tools import tool


@tool
def get_weather(city: str) -> str:
    """查询城市天气，返回温度、湿度、天气描述。"""
    target_city = city.strip() if city and city.strip() else "北京"
    url = f"https://wttr.in/{target_city}"
    params = {"format": "j1"}
    try:
        response = requests.get(url, params=params, timeout=8)
        response.raise_for_status()
        data: dict[str, Any] = response.json()
        current = data.get("current_condition", [{}])[0]
        weather_desc = current.get("weatherDesc", [{}])[0].get("value", "未知")
        temp_c = current.get("temp_C", "未知")
        humidity = current.get("humidity", "未知")
        return (
            f"{target_city}当前天气：{weather_desc}，温度{temp_c}°C，"
            f"湿度{humidity}%。若需要计算可直接使用湿度数值 {humidity}。"
        )
    except requests.RequestException as exc:
        return f"天气查询失败：网络异常（{exc}）。"
    except Exception as exc:  # noqa: BLE001
        return f"天气查询失败：数据解析异常（{exc}）。"
