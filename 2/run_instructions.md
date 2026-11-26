# 运行说明

## 环境

- 语言：Python 3.10+（本机实测可用 3.11 / 3.12）
- 依赖：仅标准库（`http.server` / `json` / `re` / `threading`），无需 `pip install`
- 入口文件：`2/main.py`
- 端口：默认 `8000`，可通过环境变量 `PORT` 覆盖；监听 `0.0.0.0`

## 启动

在仓库的 `2/` 目录下执行：

```bash
cd 2
PORT=8000 python3 main.py
```

服务前台持续运行。启动状态等价于已执行一次 `POST /reset`。

## 本地样例测试

另开终端：

```bash
cd 2
python3 sample_testcases/run_sample_testcases.py
```

可选：跑更完整的边界自测（需服务已启动）：

```bash
cd 2
python3 extra_selftest.py
```

## 已实现要点

- 多场投票，`poll_1`、`poll_2`…；非法创建不消耗 id
- 首次投票 / 改票 / 重复选同一项
- 结票幂等；结票后拒绝投票（HTTP 409）
- `title` / `options` / `voter_id` 边界校验
- `results`：票数降序，并列按创建原始顺序
- `ThreadingHTTPServer` + 锁，保证写操作原子性

## 已知限制

- 错误码未强制统一：非法参数多为 400，不存在为 404，结票后投票为 409；响应体均为 JSON
- 公开样例只覆盖连通性与部分契约，隐藏用例以 README 边界表为准

## 交卷状态

- 提交人：杜永康 / 6020262121
- PR：https://github.com/AphyTOT/ai_coding_2026/pull/3
- 完整勾选结论见：`交卷检查清单.md`（复查结论：已完成）
