---
name: commit
description: 分析 Git 变更并生成符合 Conventional Commits 的中文提交信息，支持主分支自动创建功能分支与分批提交。用户请求“提交代码”、输入 /commit、或表达“帮我提交”时使用。
---

# Commit 技能

自动执行提交和推送

## 提交信息规范

遵循 [Conventional Commits](https://www.conventionalcommits.org/)：

```text
<type>(<scope>): <emoji> <description> #<taskId>
```

破坏性变更：

```text
<type>(<scope>)!: <emoji> <description> #<taskId>

BREAKING CHANGE: <具体说明>
```

约束：
- `description` 使用中文，建议 50 字以内，采用“动词 + 对象 + 说明”。
- `scope` 从路径推断，如 `api`、`auth`、`components`、`pages`、`utils`。

Type 映射：
- `feat` 🎉：新增功能
- `fix` 🐛：缺陷修复
- `docs` 📚：文档变更
- `style` 💄：格式/样式
- `refactor` ♻️：重构
- `perf` ⚡️：性能优化
- `test` ✅：测试相关
- `build` 👷：构建/依赖
- `ci` 🔧：CI 配置
- `chore` 🔨：杂项维护

## 执行流程

### 1) 安全检查

- 禁止修改 git config。
- 禁止执行破坏性命令（`reset --hard`、`push --force` 等），除非用户明确要求。
- 禁止使用 `--no-verify` 等跳过 hook 参数，除非用户明确要求。
- 禁止提交敏感文件（如 `.env`、`*.pem`、`credentials.json`）；发现后提示并排除。
- 若无变更，不创建空提交。

### 2) 使用主分支main

- 所有代码都自动推送到主分支， 无需创建功能分支或者pr
- 只有明确要求创建分支或者pr时才创建

### 3) 收集状态

优先并行获取：

```bash
git status
git diff
git diff --cached
git diff --cached --stat
git log -5 --oneline
```

规则：
- 有暂存内容时，优先基于 `git diff --cached` 生成提交信息。
- 没有暂存内容时，基于 `git diff` 分析后再决定 `git add` 范围。

### 4) 判断是否分批提交

满足任一条件时，建议分批：
- 修改文件数 >= 5
- 新增+删除行数 >= 200
- 同时跨多个模块或多种变更类型

分批策略（按优先级）：
1. 按业务模块分组
2. 按依赖顺序分组（基础能力 -> 功能实现 -> 集成/测试）

分批时先展示分组与每组文件，再询问是否按分组提交。

### 5) 执行提交

每组或整批执行：
1. `git add` 目标文件
2. 生成提交信息
3. `git commit`
4. `git status` 验证结果

hook 失败时，修复问题后创建新 commit；除非用户明确要求，否则不使用 amend。

### 6) 推送策略

- 默认自动推送。
- 仅在用户明确要求（如“不要 push”）不执行push时才禁止 `git push`。

## 示例

```text
feat(dashboard): 🎉 添加智能调度看板组件 #1234
fix(auth): 🐛 修复登录令牌校验异常 #5678
refactor(api)!: ♻️ 重构用户鉴权接口 #9001

BREAKING CHANGE: 鉴权接口从 v1 升级为 v2，客户端需同步更新
```
