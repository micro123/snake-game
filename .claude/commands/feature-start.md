---
description: 新功能启动：聊需求→提取名称与描述→自动跑文档审查优化循环
---

# feature-start 命令

本命令不接受任何参数。用户输入（如有）为自然语言描述，不是 key:value 格式。

## 主 Agent 工作流程

### 1. 主动提问
主 Agent 直接用 AskUserQuestion 开始对话式澄清。先问一个开放式问题让用户描述想做的功能（"想做什么？解决什么问题？目标用户是谁？"）。根据描述提出 1-2 个追问帮助收敛范围，循环至需求清晰。

### 2. 提取名称与描述
从对话中提取：
- `featureName`：英文 kebab-case（如 `user-login`、`todo-list`、`pygame-starter`），简短精确
- `featureDescription`：中文 1-2 句话，描述功能是什么、给谁用、核心价值

将提取结果展示给用户确认。若用户不同意，回到步骤 1 继续调整。

### 3. 调用 doc-review-loop
用户确认后，主 Agent 直接调用：
```
/doc-review-loop featureName:{确认后的值} featureDescription:"{确认后的值}"
```
进入 P1 生成 → 审查 → 自动优化循环，直至收敛或 3 轮上限。
