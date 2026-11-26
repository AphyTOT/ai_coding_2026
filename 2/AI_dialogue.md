# AI 协作记录

工具：Cursor Agent（本对话）  
目标：完成 `2/` 活动投票封存 HTTP 服务，并按考核要求准备交卷材料。

---

## 1. 需求拆解

**我：** 先读取仓库，讲解 Fork 等概念，再给保姆级交卷教程。

**AI：**
- 说明仓库是工作室 AI Coding 考核：题 1 Hello World，题 2 投票服务
- 拆解 Git 概念：Fork / Clone / Commit / Push / PR
- 按账号 `1244765538` 写出 Fork → Clone → 开发 → 两次提交 → PR 步骤

**我：** 确认 Fork 页面配置是否正确；Fork 成功后问「然后呢」。

**AI：** 确认 Owner / 仓库名 / Copy main only 无误；随后帮助 Clone 到  
`/Users/dk/Desktop/工作室考核/ai_coding_2026`，并核对 `origin` / `upstream`。

**我：** 让 AI 罗列要完成的事情，然后说「开始」。

**AI：** 列出实现服务、边界、样例、文档、两次 commit、PR；默认用 Python 实现题 2。

---

## 2. 实现策略（向 AI 提出的约束）

基于 `2/README.md`，要求 AI：

1. 不要沿用 `baseline/python/main.py` 的「单 poll + 单用户」错误模型
2. 用单一数据源：`options` 保序 + `votes` 计票 + `voter_choice` 记每人当前选项
3. `results` / `total_votes` 每次响应时推导，避免冗余计数漂移
4. `ThreadingHTTPServer` 下对写路径加锁
5. 非法创建不得消耗 `poll_n` id；`close` 幂等；结票后拒绝投票

---

## 3. 对照 baseline 发现的问题（排查过程）

阅读官方骨架后，AI 指出 baseline 与题面不符之处：

| 问题 | 影响 |
| --- | --- |
| 全局只有一个 `poll` / `selected` | 无法多场投票、无法多用户 |
| 改票逻辑错误（已有票且不同选项直接 return） | 改票失败 |
| 结票后投票仍返回 200 且像成功 | 状态机错误 |
| 缺少 title 1~80、option 1~40、去重、voter_id 正则 | 隐藏用例会挂 |
| 创建失败也会覆盖状态 / id 行为不清晰 | 与「非法不耗 id」冲突 |

因此在 `2/main.py` **重写**实现，而不是小修 baseline。

---

## 4. 落地内容

**AI 产出：**
- `2/main.py`：完整投票服务
- `2/run_instructions.md`：启动与依赖说明
- `2/extra_selftest.py`：边界自测（改票、结票、校验、reset 后 id）
- 本文件：协作过程记录

**本地验证命令：**

```bash
cd 2
PORT=8000 python3 main.py
# 另开终端
python3 sample_testcases/run_sample_testcases.py
python3 extra_selftest.py
```

---

## 5. 本轮明确任务复述（2026-11-26）

**我：**「开始做 ai_coding_2026 题 2：按 README 实现投票服务，边做边记 AI_dialogue.md，最后补 run_instructions.md。」

**AI：** 核对仓库状态后确认：
- `2/main.py` 已按 README 重写（非小修 baseline）
- 官方样例 3/3、边界自测 4/4 再次跑通
- `run_instructions.md` 已写明环境 / 启动 / 自测 / 已知限制
- 本文件持续追加协作过程

**复测命令与结果：**

```text
python3 sample_testcases/run_sample_testcases.py  → 3 passed, 0 failed
python3 extra_selftest.py                         → 4 passed, 0 failed
python3 -m py_compile main.py                     → OK
```

实现对照 README 检查表：

| README 要求 | 落地 |
| --- | --- |
| `0.0.0.0` + `PORT` 默认 8000 | ✅ |
| `POST /polls` / `PUT .../votes/...` / `POST .../close` / `POST /reset` | ✅ |
| `GET /health`（样例需要） | ✅ |
| title 1~80、options 2~8、项 1~40 去重 | ✅ |
| voter_id `^[A-Za-z0-9_-]{1,32}$` | ✅ |
| 首次 / 改票 / 重复选；结票幂等；结票拒投 | ✅ |
| results 票数降序，并列保创建序 | ✅ |
| 非法创建不耗 id；写路径加锁 | ✅ |

---

## 6. 交卷

**我：** 提供交卷身份：`杜永康` / `6020262121`

**AI：** 按考核要求执行：
1. 第一次 commit：`feat: 完成基础业务逻辑`（`main.py` + 边界自测）
2. 第二次 commit：`docs: 补充 AI 对话记录及运行说明`
3. push 到 `1244765538/ai_coding_2026`
4. 向 `AphyTOT/ai_coding_2026` 开 PR，标题：`杜永康_6020262121`

---

## 7. 完成后复查（2026-11-26）

**我：**「检查一下看看是否完成，并写进文档。」

**AI：** 对照 README、本地测试、Git/PR 全量复查，结论：**交卷项已完成**。

复查结果摘要：

| 类别 | 结果 |
| --- | --- |
| 代码 / 文档交付物 | ✅ `main.py`、`AI_dialogue.md`、`run_instructions.md` 齐全 |
| 官方样例 | ✅ 3/3 |
| 边界自测 | ✅ 4/4 |
| README 示例流程 | ✅ PASS |
| 两次 commit + push | ✅ `9453ac9` / `f5c8d89` |
| PR | ✅ [#3](https://github.com/AphyTOT/ai_coding_2026/pull/3) 标题 `杜永康_6020262121`，OPEN / MERGEABLE |

详细勾选表见：`2/交卷检查清单.md`。
