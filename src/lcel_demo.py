"""第0阶段：LCEL（Prompt + Model + Parser）调用演示。"""

from __future__ import annotations

import os

from dotenv import load_dotenv
from langchain_community.chat_models import ChatZhipuAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate


# 启动时加载环境变量，保证脚本可直接运行。
load_dotenv()


def build_chain():
    """构建 LCEL 调用链。"""
    # 读取模型参数，默认使用免费模型。
    api_key = os.getenv("ZHIPUAI_API_KEY")
    model_name = os.getenv("MODEL_NAME", "glm-4-flash")
    if not api_key:
        raise RuntimeError("未检测到 ZHIPUAI_API_KEY，请先配置 .env。")

    # Prompt 模板：将输入包装为可复用消息结构。
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "你是一个简洁、可靠的中文助手。"),
            ("human", "请把这个主题写成一句话总结：{topic}"),
        ]
    )

    # Model：连接智谱模型。
    model = ChatZhipuAI(model=model_name, api_key=api_key, temperature=0.2)
    # Parser：把消息对象解析成纯字符串输出。
    parser = StrOutputParser()
    # LCEL 组合：prompt -> model -> parser。
    return prompt | model | parser


if __name__ == "__main__":
    chain = build_chain()
    output = chain.invoke({"topic": "LangChain 中 LCEL 的价值"})
    print("LCEL 输出：")
    print(output)
