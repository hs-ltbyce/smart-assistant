"""本地 JSON 用户偏好存储（原子替换写入）。"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

ALLOWED_KEYS: frozenset[str] = frozenset({"default_city", "news_categories"})


def default_prefs_file() -> Path:
    """偏好文件路径，可通过环境变量 SMART_ASSISTANT_PREFS_PATH 覆盖。"""
    raw = os.getenv("SMART_ASSISTANT_PREFS_PATH", "").strip()
    return Path(raw) if raw else Path(__file__).resolve().parents[2] / "data" / "user_prefs.json"


def load_all(prefs_path: Path | None = None) -> dict[str, dict[str, Any]]:
    path = prefs_path or default_prefs_file()
    if not path.is_file():
        return {}
    try:
        with path.open(encoding="utf-8") as fp:
            data = json.load(fp)
    except (json.JSONDecodeError, OSError):
        return {}
    if not isinstance(data, dict):
        return {}
    out: dict[str, dict[str, Any]] = {}
    for uid, blob in data.items():
        if isinstance(uid, str) and isinstance(blob, dict):
            out[uid] = dict(blob)
    return out


def atomic_save(data: dict[str, dict[str, Any]], prefs_path: Path | None = None) -> None:
    path = prefs_path or default_prefs_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    payload = json.dumps(data, ensure_ascii=False, indent=2)
    tmp.write_text(payload + "\n", encoding="utf-8")
    os.replace(tmp, path)


def get_pref(user_id: str, key: str, prefs_path: Path | None = None) -> Any | None:
    if key not in ALLOWED_KEYS:
        return None
    all_data = load_all(prefs_path)
    user_blob = all_data.get(user_id) or {}
    return user_blob.get(key)


def set_pref(user_id: str, key: str, value: Any, prefs_path: Path | None = None) -> str:
    if key not in ALLOWED_KEYS:
        return f"无效的偏好键：{key}，仅允许 {sorted(ALLOWED_KEYS)}。"
    if value is None or (isinstance(value, str) and not value.strip() and key != "news_categories"):
        return "拒绝写入空偏好值（news_categories 可用空数组）。"

    all_data = load_all(prefs_path)
    blob = dict(all_data.get(user_id) or {})
    if key == "news_categories":
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
            except json.JSONDecodeError:
                return "news_categories 需为 JSON 数组字符串，例如 [\"科技\",\"体育\"]。"
            value = parsed
        if not isinstance(value, list) or not all(isinstance(x, str) for x in value):
            return "news_categories 必须是字符串列表。"
        blob[key] = value
    elif key == "default_city":
        if not isinstance(value, str):
            return "default_city 必须是字符串。"
        city = value.strip()
        if not city:
            return "default_city 不能为空字符串。"
        blob[key] = city
    else:
        blob[key] = value

    all_data[user_id] = blob
    try:
        atomic_save(all_data, prefs_path)
    except OSError as exc:
        return f"写入失败：{exc}"
    return "已保存。"
