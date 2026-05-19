"""第5阶段：待办 SQLite + 与第4阶段工具集成的多工具 Agent（含短期记忆）。"""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from langchain_community.chat_models import ChatZhipuAI
from langchain_classic.agents import AgentExecutor, create_tool_calling_agent
from langchain_classic.memory import ConversationBufferMemory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from phase4_memory_prefs_agent import prepend_weather_routing_instruction, weather_tool_bound
from tools.calculator_tool import calculator
from tools.datetime_tool import get_datetime_info
from tools.todo_tool import add_todo, complete_todo, delete_todo, list_todos
from tools.user_pref_tool import get_user_pref, save_user_pref


load_dotenv()

_EXECUTOR_CACHE: dict[tuple[str, str], AgentExecutor] = {}


def build_executor(user_id: str, memory: ConversationBufferMemory) -> AgentExecutor:
    api_key = os.getenv("ZHIPUAI_API_KEY")
    model_name = os.getenv("MODEL_NAME", "glm-4-flash")
    if not api_key:
        raise RuntimeError("未检测到 ZHIPUAI_API_KEY，请先配置 .env。")

    model = ChatZhipuAI(model=model_name, api_key=api_key, temperature=0)
    tools = [
        weather_tool_bound(user_id),
        calculator,
        get_datetime_info,
        get_user_pref,
        save_user_pref,
        add_todo,
        list_todos,
        complete_todo,
        delete_todo,
    ]
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "必须用 get_weather 回答天气（含明天/后天）；用户未说城市则 city 空字符串；禁止用 get_datetime_info 冒充天气。\n"
                f"当前 user_id=\"{user_id}\"。save_user_pref/get_user_pref 与全部待办工具都须使用该 user_id。\n"
                "待办：add_todo 添加；list_todos 列出（可传 status_filter 为 pending/done）；complete_todo 完成；delete_todo 删除。\n"
                "多步示例：先 get_weather 检查天气描述，若可能下雨则 add_todo 提醒带伞或买伞，最后用 list_todos 汇总。\n"
                "时间日期用 get_datetime_info；计算用 calculator。\n",
            ),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}"),
        ]
    )
    agent = create_tool_calling_agent(model, tools, prompt)
    return AgentExecutor(
        agent=agent,
        tools=tools,
        memory=memory,
        verbose=True,
        return_intermediate_steps=True,
        max_iterations=12,
        early_stopping_method="generate",
    )


def get_executor(session_id: str, user_id: str) -> AgentExecutor:
    key = (session_id, user_id)
    if key not in _EXECUTOR_CACHE:
        memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
        _EXECUTOR_CACHE[key] = build_executor(user_id, memory)
    return _EXECUTOR_CACHE[key]


def save_trace(
    user_input: str,
    session_id: str,
    user_id: str,
    result: dict[str, Any],
) -> Path:
    log_dir = Path("logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "phase5_tool_calls.log"

    concise_steps: list[dict[str, Any]] = []
    for step in result.get("intermediate_steps", []):
        if isinstance(step, tuple) and len(step) == 2:
            action, observation = step
            concise_steps.append(
                {
                    "tool": getattr(action, "tool", "unknown"),
                    "tool_input": getattr(action, "tool_input", {}),
                    "observation": observation,
                }
            )

    payload = {
        "time": datetime.now().isoformat(timespec="seconds"),
        "session_id": session_id,
        "user_id": user_id,
        "input": user_input,
        "output": result.get("output"),
        "intermediate_steps": concise_steps,
    }
    with log_path.open("a", encoding="utf-8") as fp:
        fp.write(json.dumps(payload, ensure_ascii=False) + "\n")
    return log_path


def run_once(executor: AgentExecutor, user_input: str, session_id: str, user_id: str) -> dict[str, Any]:
    effective = prepend_weather_routing_instruction(user_input)
    result = executor.invoke({"input": effective})
    log_path = save_trace(user_input, session_id, user_id, result)
    print(f"\n最终输出: {result.get('output')}")
    print(f"日志已写入: {log_path}")
    return result


def run_interactive(session_id: str, user_id: str) -> None:
    executor = get_executor(session_id, user_id)
    print(f"第5阶段交互模式 session={session_id} user={user_id}，输入 exit 退出。")
    while True:
        query = input("\n你: ").strip()
        if query.lower() in {"exit", "quit"}:
            print("已退出交互模式。")
            break
        if not query:
            continue
        run_once(executor, query, session_id, user_id)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="第5阶段：待办 + 全工具 Agent")
    parser.add_argument("--session", default="default", help="会话ID")
    parser.add_argument("--user", default="default_user", help="用户ID")
    parser.add_argument("--query", default="", help="单轮提问")
    parser.add_argument("--interactive", action="store_true", help="交互模式")
    return parser.parse_args()


if __name__ == "__main__":
    cli = parse_args()
    if cli.interactive:
        run_interactive(cli.session, cli.user)
    elif cli.query.strip():
        ex = get_executor(cli.session, cli.user)
        run_once(ex, cli.query.strip(), cli.session, cli.user)
    else:
        print("请使用 --query 或 --interactive。")
