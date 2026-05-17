"""第1阶段：单工具 Agent（计算器）最小闭环实现。"""

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


# 脚本启动时加载环境变量。
load_dotenv()


def build_executor() -> AgentExecutor:
    """构建 AgentExecutor，供单轮或循环调用。"""
    api_key = os.getenv("ZHIPUAI_API_KEY")
    model_name = os.getenv("MODEL_NAME", "glm-4-flash")
    if not api_key:
        raise RuntimeError("未检测到 ZHIPUAI_API_KEY，请先配置 .env。")

    # 这里使用 create_tool_calling_agent，满足第1阶段指定实现方式。
    model = ChatZhipuAI(model=model_name, api_key=api_key, temperature=0)
    tools = [calculator]
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "你是一个谨慎的计算助手，只在需要时调用计算器工具。"
                "同一个问题最多调用一次 calculator，拿到工具结果后直接回答。",
            ),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}"),
        ]
    )
    agent = create_tool_calling_agent(model, tools, prompt)
    # verbose=True 用于直接打印 Thought-Action-Observation 过程。
    return AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        return_intermediate_steps=True,
        max_iterations=3,
        early_stopping_method="generate",
    )


def save_trace(user_input: str, result: dict[str, Any]) -> Path:
    """将工具调用中间步骤写入日志文件。"""
    log_dir = Path("logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "phase1_tool_calls.log"
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
    """执行一次 Agent 调用。"""
    result = executor.invoke({"input": user_input})
    log_path = save_trace(user_input, result)
    print(f"\n最终输出: {result.get('output')}")
    print(f"日志已写入: {log_path}")
    return result


def run_loop(executor: AgentExecutor) -> None:
    """启动交互循环，输入 exit 退出。"""
    print("进入交互模式，输入 exit 结束。")
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
    parser = argparse.ArgumentParser(description="第1阶段：单工具 Agent 运行脚本")
    parser.add_argument(
        "--query",
        default="123 * 456 等于多少",
        help="单轮模式下的输入问题。",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="开启循环交互模式。",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    agent_executor = build_executor()
    if args.interactive:
        run_loop(agent_executor)
    else:
        run_once(agent_executor, args.query)
