# smart-assistant

智能助手项目，包含基础调用、LCEL 示例、多工具 Agent 与记忆聊天示例代码。

## 环境要求
- Python 3.10+
- 建议使用虚拟环境（venv/conda）

## 安装依赖
```bash
pip install -r requirements.txt
```

## 运行示例
```bash
python src/basic_call.py
python src/lcel_demo.py
python src/phase1_single_tool_agent.py
python src/phase2_multi_tool_agent.py
python src/phase3_memory_chat.py
```

## 目录说明
```text
smart-assistant
├── src/                 # 源代码
├── src/tools/           # 工具实现（计算器、时间、天气）
├── test-doc/            # 测试文档（功能与测试点）
├── logs/                # 执行日志
├── pm/                  # 项目需求与排期（只读）
├── pm/develop/          # 开发留痕与阶段汇报
├── .cursor/rules/       # 开发规则
└── .cursor/skills/      # 技能定义
```

## 测试文档规范
每一个新功能以及每一个测试点都必须创建测试文档，放在 `test-doc/` 目录。

每份测试文档至少包含三部分：
1. 测试什么（目标功能、测试点）
2. 怎么测试（运行环境、执行脚本、前置条件/测试数据）
3. 期望结果（成功标准、关键输出、异常场景预期）

建议命名：
- `test-doc/YYYY-MM-DD_<feature>_test.md`

建议模板：
```text
# <功能名称> 测试文档

## 1. 测试什么
- 功能：
- 测试点：

## 2. 怎么测试
### 2.1 运行环境
- OS:
- 运行时版本:
- 依赖版本:

### 2.2 执行脚本/命令
1.
2.

### 2.3 前置条件/测试数据
- 

## 3. 期望结果
- 
```
