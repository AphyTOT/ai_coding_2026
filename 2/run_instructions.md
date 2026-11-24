# 运行说明

## 1. 环境依赖

| 项 | 说明 |
| --- | --- |
| 语言 | Python **3.10+**（判题机为 Python 3.11，本地在 3.12 上验证过） |
| 第三方库 | **无**。只用标准库：`json` / `os` / `re` / `threading` / `http.server` / `urllib.parse` |
| 安装步骤 | 无。不需要 `pip install`，不需要外网 |
| 端口 | 监听 `0.0.0.0:8000`；读取环境变量 `PORT`，未设置时默认 `8000` |

## 2. 代码位置

| 文件 | 说明 |
| --- | --- |
| `baseline/python/main.py` | **唯一实现文件**，单文件，无包依赖、无相对导入 |
| `selftest/run_edge_cases.py` | 我自己补的边界 / 并发测试（不是判题必需，仅用于自测） |

> 题面里的 `work/` 是**判题器**的目录：它把 `baseline/python/` 整个拷进 `work/` 再运行，
> 所以 `main.py` 最终落在 `work/` 根目录。**我没有手动创建 `work/` 目录**，也不需要。

## 3. 启动命令

```bash
# Linux / macOS
cd baseline/python
PORT=8000 python3 main.py
```

```powershell
# Windows PowerShell
cd baseline\python
$env:PORT='8000'; python main.py
```

前台持续运行，看到 `poll-seal listening on 0.0.0.0:8000` 即启动成功。

## 4. 本地自测命令

```bash
# ① 官方公开样例（从 2/ 目录执行，服务需已在 8000 端口运行）
python3 sample_testcases/run_sample_testcases.py

# ② 我自己补的边界用例（14 项，含并发与随机模糊测试）
python3 selftest/run_edge_cases.py
```

实测结果：

```
# sample_testcases
3 passed, 0 failed

# selftest
14 passed, 0 failed
```

## 5. 接口与错误码约定

| 方法 | 路径 | 成功 | 说明 |
| --- | --- | --- | --- |
| `POST` | `/polls` | 200 + 完整 Poll | 创建投票 |
| `PUT` | `/polls/{poll_id}/votes/{voter_id}` | 200 + 完整 Poll | 投票 / 改票 |
| `POST` | `/polls/{poll_id}/close` | 200 + 完整 Poll | 结票，**幂等** |
| `POST` | `/reset` | 200 `{"ok": true}` | 全量清空，id 归零 |
| `GET` | `/health` | 200 `{"status": "ok"}` | 样例测试需要，题面接口表未列 |
| `GET` | `/polls/{poll_id}` | 200 + 完整 Poll | 我额外加的只读接口，方便调试 |

拒绝时的约定（题面未强制状态码，重点是**不改数据、不消耗 id**）：

| 情况 | 状态码 | 响应体 |
| --- | --- | --- |
| 参数非法（长度 / 数量 / 重复 / 类型 / JSON 格式） | `400` | `{"error": "..."}` |
| `poll_id` 不存在 | `404` | `{"error": "..."}` |
| 投票已结票仍投票 / 改票 | `409` | `{"error": "..."}` |
| 未知路径 / 不支持的方法 | `404` / `405` | `{"error": "..."}` |

## 6. 实现要点

1. **单一数据源**：每场投票只存 `options`（原始顺序）、`votes`（各选项票数）、`choices`（`voter_id -> option`）、`status`。
   `results` 与 `total_votes` 每次从同一份数据现场推导，`total_votes` 就是 `len(choices)`，结构上不可能与票数之和漂移。
2. **原子写**：每个操作的「校验 + 变更」整体在一把 `threading.Lock` 内完成，`ThreadingHTTPServer` 并发下不会重复计数。
3. **id 不浪费**：`create` 先做完全部校验，再拿锁分配 `poll_N`；非法请求不消耗 id。
4. **稳定的并列排序**：先按创建原始顺序铺开 `results`，再按 `-votes` 排序（Python sort 稳定），并列时自然保持创建顺序，不依赖 dict 遍历顺序。
5. **拒绝即无损**：所有校验在修改数据之前抛 `ApiError`，被拒绝的请求对状态零影响。

## 7. 已知取舍 / 未完成的地方（如实说明）

1. **没有做持久化**：数据只在内存，进程重启即清空。
   这是**有意为之**——题面要求「启动状态等同于已执行一次 `POST /reset`」，落盘反而会违反这条。
2. **投票时 `option` 按精确字符串匹配，不做 strip**：创建时选项已去首尾空白存储，
   若客户端投票时仍带首尾空格，会被判为「不是该投票的候选项」而拒绝。
   题面只写「必须是该投票已创建的候选项之一」，我按字面取精确匹配。**这是全文唯一有歧义的点**，如果隐藏用例期望宽松匹配，需要改成 `option.strip()` 再比对。
3. **未处理 `Transfer-Encoding: chunked`**：只按 `Content-Length` 读请求体。判题器发普通 JSON，够用；
   若后续要支持流式上传，需补 chunked 解析。
4. **`GET /polls/{id}` 是额外接口**：题面没要求。加它是因为调试时比反复 `curl` 全量更省事，且只读、不影响任何写入语义。
5. **没有做鉴权 / 限流**：题面未涉及，且 `voter_id` 由调用方传入、服务端不验证身份，属于题目设定而非缺陷。
