"""第5阶段：待办 SQLite 工具。"""

from __future__ import annotations

from langchain.tools import tool

from storage.todo_store import default_db_path, add_row as db_add, complete_row as db_complete, delete_row as db_delete, list_rows as db_list


@tool
def add_todo(user_id: str, content: str) -> str:
    """添加一条待办事项。content 为待办正文。"""
    user_id = (user_id or "").strip() or "default_user"
    content = (content or "").strip()
    if not content:
        return "待办内容不能为空。"
    try:
        tid = db_add(user_id, content, default_db_path())
    except ValueError as e:
        return str(e)
    return f"已添加待办，id={tid}：{content}"


@tool
def list_todos(user_id: str, status_filter: str = "") -> str:
    """列出当前用户的待办。status_filter 为空则列出全部；可取 pending（未完成）或 done（已完成）。"""
    user_id = (user_id or "").strip() or "default_user"
    sf = (status_filter or "").strip().lower()
    if sf not in ("", "all", "pending", "done"):
        return "status_filter 只能是 pending、done 或留空表示全部。"
    eff = None if sf in ("", "all") else sf
    rows = db_list(user_id, eff, default_db_path())
    if not rows:
        return "暂无待办。"
    lines = []
    for r in rows:
        lines.append(
            f"[{r['id']}] ({r['status']}) {r['content']} @ {r['created_at']}"
        )
    return "\n".join(lines)


@tool
def complete_todo(user_id: str, todo_id: int) -> str:
    """将指定 id 的待办标记为已完成（自 pending 变为 done）。"""
    user_id = (user_id or "").strip() or "default_user"
    try:
        tid = int(todo_id)
    except (TypeError, ValueError):
        return "todo_id 必须是整数。"
    if db_complete(user_id, tid, default_db_path()):
        return f"已将待办 id={tid} 标为完成。"
    return f"未找到可完成的待办 id={todo_id}（可能已删除或已完成）。"


@tool
def delete_todo(user_id: str, todo_id: int) -> str:
    """删除指定 id 的待办。"""
    user_id = (user_id or "").strip() or "default_user"
    try:
        tid = int(todo_id)
    except (TypeError, ValueError):
        return "todo_id 必须是整数。"
    if db_delete(user_id, tid, default_db_path()):
        return f"已删除待办 id={tid}。"
    return f"未找到待办 id={todo_id}。"
