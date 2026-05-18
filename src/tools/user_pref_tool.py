"""第4阶段：用户偏好读写工具。"""

from __future__ import annotations

import json
from typing import Any

from langchain.tools import tool

from storage.user_prefs import default_prefs_file, get_pref, set_pref


@tool
def get_user_pref(user_id: str, key: str) -> str:
    """读取用户的长期偏好。key 只能是 default_city（默认查询城市）或 news_categories（新闻类别列表）。

    查询天气且用户未说明城市时，必须先调用本工具读取 default_city。"""
    user_id = (user_id or "").strip() or "default_user"
    key = (key or "").strip()
    if key not in ("default_city", "news_categories"):
        return "无效的 key，仅支持 default_city、news_categories。"
    val = get_pref(user_id, key, default_prefs_file())
    if val is None:
        return f"用户 {user_id} 未设置 {key}。"
    if key == "news_categories":
        return json.dumps(val, ensure_ascii=False)
    return str(val)


@tool
def save_user_pref(user_id: str, key: str, value: str) -> str:
    """保存用户的长期偏好。key 为 default_city 时 value 为城市名；

    key 为 news_categories 时 value 为 JSON 数组字符串，如 [\"国内\",\"科技\"]。"""
    user_id = (user_id or "").strip() or "default_user"
    key = (key or "").strip()
    parsed_value: Any = value
    if key == "news_categories" and isinstance(value, str):
        try:
            parsed_value = json.loads(value)
        except json.JSONDecodeError:
            pass
    return set_pref(user_id, key, parsed_value, default_prefs_file())
