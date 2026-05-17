"""第2阶段：多工具 Agent（计算器 + 天气 + 时间）。"""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from langchain_community.chat_models import ChatZhipuAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_classic.agents import AgentExecutor, create_tool_calling_agent

from tools.calculator_tool import calculator
from tools.datetime_tool import get_datetime_info
from tools.weather_tool import get_weather


load_dotenv()


def build_executor() -> AgentExecutor:
    """构建多工具 AgentExecutor。"""
    api_key = os.getenv("ZHIPUAI_API_KEY")
    model_name = os.getenv("MODEL_NAME", "glm-4-flash")
    if not api_key:
        raise RuntimeError("未检测到 ZHIPUAI_API_KEY，请先配置 .env。")

    model = ChatZhipuAI(model=model_name, api_key=api_key, temperature=0)
    tools = [calculator, get_weather, get_datetime_info]
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "你是智能助理。需要查询天气时调用 get_weather；"
                "需要时间日期时调用 get_datetime_info；"
                "需要数值计算时调用 calculator。"
                "同一个问题中同一工具最多调用一次，拿到工具结果后直接回答。",
            ),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}"),
        ]
    )
    agent = create_tool_calling_agent(model, tools, prompt)
    return AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        return_intermediate_steps=True,
        max_iterations=4,
        early_stopping_method="generate",
    )


def save_trace(user_input: str, result: dict[str, Any]) -> Path:
    """保存调用链日志。"""
    log_dir = Path("logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "phase2_tool_calls.log"

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
        "input": user_input,
        "output": result.get("output"),
        "intermediate_steps": concise_steps,
    }
    with log_path.open("a", encoding="utf-8") as fp:
        fp.write(json.dumps(payload, ensure_ascii=False) + "\n")
    return log_path


def run_once(executor: AgentExecutor, user_input: str) -> dict[str, Any]:
    """执行一次多工具调用。"""
    result = executor.invoke({"input": user_input})
    log_path = save_trace(user_input, result)
    print(f"\n最终输出: {result.get('output')}")
    print(f"日志已写入: {log_path}")
    return result


def run_loop(executor: AgentExecutor) -> None:
    """交互循环。"""
    print("进入多工具交互模式，输入 exit 退出。")
    while True:
        query = input("\n你: ").strip()
        if query.lower() in {"exit", "quit"}:
            print("已退出交互模式。")
            break
        if not query:
            continue
        run_once(executor, query)


def parse_args() -> argparse.Namespace:
    """解析命令行参数。"""
    parser = argparse.ArgumentParser(description="第2阶段：多工具 Agent 运行脚本")
    parser.add_argument(
        "--query",
        default="北京今天天气如何，湿度乘以2是多少",
        help="单轮模式输入问题。",
    )
    parser.add_argument("--interactive", action="store_true", help="开启交互模式。")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    agent_executor = build_executor()
    if args.interactive:
        run_loop(agent_executor)
    else:
        run_once(agent_executor, args.query)
