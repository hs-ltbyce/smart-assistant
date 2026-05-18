"""第2阶段：天气查询工具（wttr.in）；第4阶段起支持按 user_id 回退默认城市。"""

from __future__ import annotations

from typing import Any

import requests
from langchain.tools import tool

from storage.user_prefs import default_prefs_file, get_pref


WEATHER_TOOL_DESCRIPTION = (
    "查询城市当前天气（温度、湿度、描述）。"
    "用户在问题里已指明城市名时将该城市传入 city。"
    "若用户未指定地点，请传空字符串，将按该用户的 default_city 长期偏好解析目标城市。"
)


def fetch_weather(city: str = "", user_id: str = "") -> str:
    """供 Agent 与各阶段脚本复用的天气查询入口。"""
    c = city.strip() if city else ""
    uid = user_id.strip() if user_id else ""
    if c:
        target = c
    elif uid:
        pref = get_pref(uid, "default_city", default_prefs_file())
        if isinstance(pref, str) and pref.strip():
            target = pref.strip()
        else:
            return (
                "未设置默认城市偏好，请让用户说明城市，或使用 save_user_pref 保存 default_city。"
            )
    else:
        target = "北京"

    url = f"https://wttr.in/{target}"
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
            f"{target}当前天气：{weather_desc}，温度{temp_c}°C，"
            f"湿度{humidity}%。若需要计算可直接使用湿度数值 {humidity}。"
        )
    except requests.RequestException as exc:
        return f"天气查询失败：网络异常（{exc}）。"
    except Exception as exc:  # noqa: BLE001
        return f"天气查询失败：数据解析异常（{exc}）。"


@tool
def get_weather(city: str = "", user_id: str = "") -> str:
    """查询城市当前天气；未指定城市且传入 user_id 时使用 default_city 偏好。"""
    return fetch_weather(city, user_id)
