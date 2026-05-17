"""第0阶段：基础模型调用验证脚本。"""

from __future__ import annotations

import os

from dotenv import load_dotenv
from langchain_community.chat_models import ChatZhipuAI
from langchain_core.messages import HumanMessage


# 加载 .env 配置，便于本地开发时读取 API Key。
load_dotenv()


def build_model() -> ChatZhipuAI:
    """构建并返回 ChatZhipuAI 实例。"""
    # 环境变量名使用官方 SDK 默认字段，避免硬编码密钥。
    api_key = os.getenv("ZHIPUAI_API_KEY")
    model_name = os.getenv("MODEL_NAME", "glm-4-flash")
    # 提前做参数校验，避免请求阶段才报错。
    if not api_key:
        raise RuntimeError("未检测到 ZHIPUAI_API_KEY，请先配置 .env。")
    return ChatZhipuAI(model=model_name, api_key=api_key, temperature=0)


def run_basic_qa(question: str) -> str:
    """执行一次基础问答并返回文本结果。"""
    # 该函数用于任务 0.3：验证 LangChain + GLM 的最小链路。
    model = build_model()
    response = model.invoke([HumanMessage(content=question)])
    return response.content if isinstance(response.content, str) else str(response.content)


if __name__ == "__main__":
    # 通过固定问题快速确认 API 是否可用。
    answer = run_basic_qa("请用一句话介绍你自己。")
    print("模型回复：")
    print(answer)
