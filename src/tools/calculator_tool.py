"""第1阶段：计算器工具定义。"""

from __future__ import annotations

import ast
import operator
from typing import Union

from langchain.tools import tool


# 支持的运算符白名单，避免直接 eval 带来的执行风险。
_ALLOWED_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}

Number = Union[int, float]


def _safe_eval(node: ast.AST) -> Number:
    """递归解析 AST 并计算表达式。"""
    if isinstance(node, ast.Expression):
        return _safe_eval(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp):
        left = _safe_eval(node.left)
        right = _safe_eval(node.right)
        op_type = type(node.op)
        if op_type not in _ALLOWED_OPERATORS:
            raise ValueError(f"不支持的运算符: {op_type.__name__}")
        return _ALLOWED_OPERATORS[op_type](left, right)
    if isinstance(node, ast.UnaryOp):
        operand = _safe_eval(node.operand)
        op_type = type(node.op)
        if op_type not in _ALLOWED_OPERATORS:
            raise ValueError(f"不支持的一元运算符: {op_type.__name__}")
        return _ALLOWED_OPERATORS[op_type](operand)
    raise ValueError("表达式包含不支持的语法。")


@tool
def calculator(expression: str) -> str:
    """执行数学表达式计算，支持 + - * / % ** 与括号。"""
    try:
        parsed = ast.parse(expression, mode="eval")
        result = _safe_eval(parsed)
        return str(result)
    except Exception as exc:  # noqa: BLE001
        return f"计算失败：{exc}"
