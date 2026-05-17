"""第3阶段：基于 RunnableWithMessageHistory 的多轮记忆会话。"""

from __future__ import annotations

import argparse
import os

from dotenv import load_dotenv
from langchain_community.chat_models import ChatZhipuAI
from langchain_core.chat_history import BaseChatMessageHistory, InMemoryChatMessageHistory
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory


load_dotenv()

# 内存会话仓库：每个 session_id 对应一份独立历史。
_SESSION_STORE: dict[str, InMemoryChatMessageHistory] = {}


def get_session_history(session_id: str) -> BaseChatMessageHistory:
    """按 session_id 获取或创建会话历史。"""
    if session_id not in _SESSION_STORE:
        _SESSION_STORE[session_id] = InMemoryChatMessageHistory()
    return _SESSION_STORE[session_id]


def build_memory_chain() -> RunnableWithMessageHistory:
    """构建带会话记忆的可运行链。"""
    api_key = os.getenv("ZHIPUAI_API_KEY")
    model_name = os.getenv("MODEL_NAME", "glm-4-flash")
    if not api_key:
        raise RuntimeError("未检测到 ZHIPUAI_API_KEY，请先配置 .env。")

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "你是中文助手，会基于历史对话连续回答。"),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{input}"),
        ]
    )
    model = ChatZhipuAI(model=model_name, api_key=api_key, temperature=0)
    chain = prompt | model | StrOutputParser()
    return RunnableWithMessageHistory(
        chain,
        get_session_history,
        input_messages_key="input",
        history_messages_key="history",
    )


def chat_once(memory_chain: RunnableWithMessageHistory, session_id: str, query: str) -> str:
    """执行单轮对话。"""
    return memory_chain.invoke(
        {"input": query},
        config={"configurable": {"session_id": session_id}},
    )


def run_interactive(memory_chain: RunnableWithMessageHistory, session_id: str) -> None:
    """交互模式：同一 session 连续记忆。"""
    print(f"进入记忆对话模式，session={session_id}，输入 exit 退出。")
    while True:
        query = input("\n你: ").strip()
        if query.lower() in {"exit", "quit"}:
            print("已退出记忆对话模式。")
            break
        if not query:
            continue
        answer = chat_once(memory_chain, session_id, query)
        print(f"助手: {answer}")


def parse_args() -> argparse.Namespace:
    """解析命令行参数。"""
    parser = argparse.ArgumentParser(description="第3阶段：多轮记忆对话脚本")
    parser.add_argument("--session", default="default", help="会话ID，不同ID记忆隔离。")
    parser.add_argument("--query", default="我叫小明", help="单轮模式输入。")
    parser.add_argument("--interactive", action="store_true", help="开启交互模式。")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    chain = build_memory_chain()
    if args.interactive:
        run_interactive(chain, args.session)
    else:
        result = chat_once(chain, args.session, args.query)
        print(result)
