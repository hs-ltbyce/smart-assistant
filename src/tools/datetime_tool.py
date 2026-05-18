"""第2阶段：时间日期工具。"""

from __future__ import annotations

from datetime import datetime, timedelta

from langchain.tools import tool


_WEEKDAY_MAP = {
    "周一": 0,
    "周二": 1,
    "周三": 2,
    "周四": 3,
    "周五": 4,
    "周六": 5,
    "周日": 6,
    "周天": 6,
}


def _next_week_date(target_weekday: int) -> datetime:
    """计算“下周X”对应日期（下周一到下周日）。"""
    now = datetime.now()
    # weekday: 周一=0, 周日=6；先定位到下周一，再偏移到目标日。
    days_until_next_monday = 7 - now.weekday()
    next_monday = now + timedelta(days=days_until_next_monday)
    return next_monday + timedelta(days=target_weekday)


@tool
def get_datetime_info(query: str) -> str:
    """回答当前时间、今天日期、下周几日期等；不涉及天气、气温、湿度、风、降雨。"""
    text = (query or "").strip()
    if any(k in text for k in ("天气", "气温", "下雨", "下雪", "刮风", "湿度", "冷不冷", "热不热")):
        return (
            "本工具不处理气象问题；若用户问及天气实况，必须由 get_weather 处理，"
            "且用户未指定地点时请将 get_weather 的 city 置空。"
        )
    now = datetime.now()

    if "现在" in text and ("几点" in text or "时间" in text):
        return f"现在时间：{now.strftime('%Y-%m-%d %H:%M:%S')}。"

    if "今天" in text and "日期" in text:
        return f"今天日期：{now.strftime('%Y-%m-%d')}。"

    if "下周" in text:
        for label, weekday in _WEEKDAY_MAP.items():
            if label in text:
                target_date = _next_week_date(weekday)
                return f"下周{label[-1]}是：{target_date.strftime('%Y-%m-%d')}。"
        return "时间工具暂不支持该下周日期表达，请使用如“下周五日期”。"

    return (
        "未识别为时间类问题。本工具仅支持：现在几点、今天日期、下周几是几号。"
        "若用户在问天气，请改调 get_weather（未说城市则 city 置空）。"
    )
