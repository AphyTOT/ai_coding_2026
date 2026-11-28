# 运行说明

> 对应题目：`2/README.md` 活动投票封存（多场投票 HTTP 服务）
> 实现文件：`baseline/cpp/main.cpp`（单文件，无第三方依赖）

---

## 1. 启动命令

### 判题环境（Linux）

```bash
# 编译（与 README 给出的命令一致）
g++ -O2 -std=c++17 -pthread main.cpp -o main

# 启动：默认监听 0.0.0.0:8000
./main

# 如需指定端口
PORT=8000 ./main
```

> 端口默认值就是 `8000`，不设 `PORT` 也能正常判题；启动后即等价于已执行过一次 `POST /reset`（空数据、id 从 `poll_1` 开始）。

### 本地自测（起服务后另开一个终端）

```bash
python3 sample_testcases/run_sample_testcases.py
```

### 本机（Windows）编译

```powershell
# 仅本机自测需要额外链接 winsock；判题环境不需要
g++ -O2 -std=c++17 -pthread main.cpp -o main.exe -lws2_32
$env:PORT = "8000"
.\main.exe
```

---

## 2. 环境依赖

| 项 | 说明 |
| --- | --- |
| 编译器 | g++ 11+，`-std=c++17` |
| 依赖库 | 仅 C++ 标准库 + 系统 socket（POSIX），**无任何第三方库** |
| 平台 | Linux（判题）；Windows 可编译，仅用于本机自测（多链 `-lws2_32`） |
| 网络/外网 | 不需要 |
| 运行时资源 | 单进程、单线程、常驻前台，无临时文件、无数据库 |

---

## 3. 实现与接口一览（便于验收对照）

| 方法 | 路径 | 成功响应 |
| --- | --- | --- |
| `GET` | `/health` | `{"status":"ok"}`（README 接口表未列，但样例脚本会调用） |
| `POST` | `/polls` | 完整 Poll 对象 |
| `PUT` | `/polls/{poll_id}/votes/{voter_id}` | 完整 Poll 对象 |
| `POST` | `/polls/{poll_id}/close` | 完整 Poll 对象（重复结票返回相同快照） |
| `POST` | `/reset` | `{"ok":true}` |

错误响应约定：参数非法 `400`、poll 不存在 `404`、结票后投票 `409`，响应体统一为 `{"error":"..."}`，且**拒绝时不改动任何数据、不消耗 id**。

核心数据只存 `poll_id -> {title, status, options(创建顺序), voter_choice(voter_id -> 候选项)}`；
票数、`total_votes`、排序全部在输出时从 `voter_choice` 现算，因此「票数 / 有效投票人数 / 最终排名」三者不会漂移。

---

## 4. 本地自测结果

| 测试 | 结果 |
| --- | --- |
| 官方样例 `run_sample_testcases.py` | **3 passed, 0 failed**（退出码 0） |
| 自写边界用例（`urllib` + `json`，23 组） | **23 passed, 0 failed** |
| 编译 `-Wall -Wextra` | 0 warning |

边界用例覆盖：title 长度 1/80/81、options 数量 2/8/9、候选项长度 1/40/41 与去空白后重复、
voter_id 长度 1/32/33 与非法字符、非法请求不消耗 id、首次/改票/重复投票、多场投票隔离、
同票按创建顺序排序、结票幂等、结票后 409 且数据不变、reset 后 id 归位、Unicode 空白 trim、
JSON 转义往返、`\uXXXX` 解码、坏 JSON 不崩、百分号编码路径。

> 测试脚本按约定放在系统临时目录，未放入本仓库。

---

## 5. 还没做完 / 有 Bug 的地方（如实记录）

1. **Linux 分支尚未在本机编译验证**（本机只有 MinGW，走的是 `#ifdef _WIN32` 的另一支）。
   POSIX 分支按标准接口编写、编译期未参与，是本次唯一没有被真实运行覆盖到的代码路径。
   **风险等级：中** —— 放到判题环境后第一件事就应该是编译验证；若报错，大概率是头文件或
   `ssize_t` / `socklen_t` 之类的类型细节，修复面很小。

2. **只监听 IPv4（`0.0.0.0`），没有监听 IPv6**。
   样例脚本默认连 `http://localhost:8000`，若运行环境的 `localhost` 优先解析到 `::1`，
   依赖客户端自动回退到 IPv4 才能连通（Python `urllib` 会按地址顺序重试，通常没问题，但不是零风险）。

3. **单线程串行处理**：一个慢连接会推迟后续请求。已给每个连接设 10s 读超时兜底，
   但**超时后是直接关闭连接，不返回任何响应**（客户端会看到连接被重置，而不是 408/400）。
   若判题器有并发压力，需要改成线程池 + 互斥锁。

4. **不支持 keep-alive 复用、`Transfer-Encoding: chunked`、`Expect: 100-continue`**。
   响应固定 `Connection: close`，每连接处理一个请求；`curl` 发大 body 时会因缺少 `100 Continue`
   多等约 1 秒。判题器若用 `urllib`/`requests` 默认行为不受影响。

5. **错误码 400/404/409 分散在三个 handler 中**（`handleCreate` / `handleVote` / `handleClose`）。
   README 声明「错误码不做强制要求」，这是按讨论约定实现的；但如果隐藏用例期望「一律 200 + 当前快照」，
   需要改 5 处以上，容易漏改——这是当前最值得重构的一点（应收敛为一个常量或统一的 `reject()`）。

6. **投票时的候选项匹配放宽了**：先精确匹配，匹配不到再按 trim 后匹配。
   这是为了兼容「客户端回传带首尾空白的候选项名」；代价是如果判题器期望
   「带空白的 option 必须被拒绝」，我们会错误地接受（返回 200）。正常用例里候选词在创建时已 trim，
   这层回退几乎不会被触发，属于收益/风险不完全对称的取舍。

7. **启动失败时没有任何日志**：`bind`/`listen` 失败直接 `return 1`。
   若判题环境的 8000 端口被占用或权限不足，只能看到进程退出、看不到原因，排查成本高。

8. **内存无上限**：`polls` 与 `voter_choice` 只增不减（只有 `/reset` 会清空）。
   判题规模下无影响，但不适合长期运行。

9. **请求体上限 1 MiB**，超过直接返回 400；判题正常用不到，属于防御性限制。
