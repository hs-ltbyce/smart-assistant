"""第4阶段：短期会话记忆 + 多工具 + 长期偏好（JSON 持久化）。"""

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
from langchain_core.tools import tool

from tools.calculator_tool import calculator
from tools.datetime_tool import get_datetime_info
from tools.user_pref_tool import get_user_pref, save_user_pref
from tools.weather_tool import WEATHER_TOOL_DESCRIPTION, fetch_weather


load_dotenv()

# (session_id, user_id) -> 带独立短期记忆的执行器
_EXECUTOR_CACHE: dict[tuple[str, str], AgentExecutor] = {}

_WEATHER_TRIGGERS = ("天气", "下雨", "下雪", "气温", "刮风", "湿度")


def prepend_weather_routing_instruction(user_message: str) -> str:
    """缓解工具选择不稳：在涉气象语句前附加硬路由提醒（写入短期记忆的是带前缀文本）。"""
    t = user_message.strip()
    if not any(k in t for k in _WEATHER_TRIGGERS):
        return user_message
    return (
        "[工具路由]此句涉气象实况：第一步必须调用 get_weather；"
        "若句中未出现具体城市名，则将 get_weather 的 city 置为空字符串。\n"
        f"用户原话：{user_message}"
    )


def weather_tool_bound(user_id: str):
    """绑定 user_id，`get_weather` 在用户未指定地点时读取 default_city。"""
    uid = user_id

    def get_weather(city: str = "") -> str:
        """查询当前天气实况。"""
        return fetch_weather(city, uid)

    return tool(get_weather, description=WEATHER_TOOL_DESCRIPTION)


def build_executor(user_id: str, memory: ConversationBufferMemory) -> AgentExecutor:
    """构建绑定指定用户与记忆对象的 AgentExecutor。"""
    api_key = os.getenv("ZHIPUAI_API_KEY")
    model_name = os.getenv("MODEL_NAME", "glm-4-flash")
    if not api_key:
        raise RuntimeError("未检测到 ZHIPUAI_API_KEY，请先配置 .env。")

    model = ChatZhipuAI(model=model_name, api_key=api_key, temperature=0)
    tools = [weather_tool_bound(user_id), calculator, get_datetime_info, get_user_pref, save_user_pref]
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "必须用 get_weather 回答天气问题（含「今天/明天/后天」等）：用户没说城市时令 city 为空字符串即可（会使用已保存 default_city）；"
                "不要为天气先去 get_user_pref；禁止用 get_datetime_info 回答天气。\n"
                f"user_id=\"{user_id}\"；仅在用户明确要存/读长期偏好时对 save_user_pref / get_user_pref 传入该 id。\n"
                "写入偏好 save_user_pref；读取偏好键 get_user_pref。时间日期 get_datetime_info；计算 calculator。\n",
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
        max_iterations=10,
        early_stopping_method="generate",
    )


def get_executor(session_id: str, user_id: str) -> AgentExecutor:
    """按会话与用户隔离短期记忆（ConversationBufferMemory）。"""
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
    """追加写入第4阶段工具调用日志。"""
    log_dir = Path("logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "phase4_tool_calls.log"

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
    """单轮 invoke 并写日志。"""
    effective = prepend_weather_routing_instruction(user_input)
    result = executor.invoke({"input": effective})
    log_path = save_trace(user_input, session_id, user_id, result)
    print(f"\n最终输出: {result.get('output')}")
    print(f"日志已写入: {log_path}")
    return result


def run_interactive(session_id: str, user_id: str) -> None:
    """交互循环。"""
    executor = get_executor(session_id, user_id)
    print(f"第4阶段交互模式 session={session_id} user={user_id}，输入 exit 退出。")
    while True:
        query = input("\n你: ").strip()
        if query.lower() in {"exit", "quit"}:
            print("已退出交互模式。")
            break
        if not query:
            continue
        run_once(executor, query, session_id, user_id)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="第4阶段：记忆 + 工具 + 用户偏好持久化")
    parser.add_argument("--session", default="default", help="会话ID，隔离短期对话记忆")
    parser.add_argument("--user", default="default_user", help="用户ID，读写偏好时使用")
    parser.add_argument("--query", default="", help="非交互单轮提问；留空且无 --interactive 时打印提示退出")
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
        print("请使用 --query 指定问题或添加 --interactive 进入对话。")
