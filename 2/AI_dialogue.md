# AI 协作记录

> 说明：以下是我与 AI 编程助手（DeepSeek Harness 会话）的真实对话摘录，按轮次整理。
> 只做了两件事：删掉无关寒暄、把 AI 的折行排版理顺。技术内容、报错原文、代码改动都保持原样。
> 截图见文末「附：截图清单」。

---

## 轮次 1：先让它帮我把题目读懂

**我：**
> https://github.com/uhura666/ai_coding_2026/tree/main ，这是一个考核题目发来的 GitHub 链接，要求我们完成，但是我看不太懂，请你告诉我我该怎么完成

**AI：**
先给结论：这仓库是一套**题库**，不是一道题。

| 目录 | 是什么 | 要做吗 |
| --- | --- | --- |
| `1/` | Hello World 的 C++ 题 | 热身占位，不用管 |
| `2/` | **正式题：活动投票封存** | 这才是考核题 |

第 2 题说白了：写一个**一直跑着的小型 HTTP 服务**（固定 8000 端口），管「活动投票」，只有 4 个接口：

- `POST /polls` 创建投票（标题 + 2~8 个候选项）
- `PUT /polls/{poll_id}/votes/{voter_id}` 投票 / 改票
- `POST /polls/{poll_id}/close` 结票（幂等）
- `POST /reset` 全清，id 重新从 `poll_1` 开始

核心矛盾只有一个：**`results` 里的票数、`total_votes`、排名顺序三者必须永远自洽**。u_1 先投「米饭」再改成「面条」，结果必须是米饭 0、面条 1，`total_votes` 仍然是 **1** 而不是 2。

**我的收获：** 一开始我以为要跑起来一个复杂系统，其实就是一个几百行的单文件服务，难点全在「一致性」和「边界」。

---

## 轮次 2：我让它先审查 baseline，别急着写

**我：**
> 那 baseline 里已经给了代码，我是不是改一改就行？

**AI：**
baseline 是**故意写坏的半成品**，你得先知道它坏在哪。读完 `2/baseline/python/main.py` 后，问题有 5 个：

1. 全局只有一个 `poll`，`id` 永远返回 `poll_1` —— 不支持多场投票
2. 全局只有一个 `selected`，**根本没有 voter_id** —— 两个人投票会互相覆盖
3. 改票那段 `if selected is not None and selected != option: return result()` —— 改票根本不生效，只是把旧结果原样返回
4. `title` 没查 80 字上限，`options` 没查单项 40 字上限、没查去空白后重复，`voter_id` 完全没校验
5. 给不存在的选项投票、对已结票的投票投票，都返回 200 + 原数据（规格要求「拒绝」）

所以这题不是「改一改」，是**按规格重写**。baseline 唯一有价值的是它的 HTTP 骨架（`BaseHTTPRequestHandler` + `send_json`），以及告诉你输出格式长什么样。

**我的收获：** 学会了一件事——拿到 baseline 先当 code review 做，把「已有」和「规格要求」逐条对表，缺什么一目了然。这比直接让 AI 写一整份更有底。

---

## 轮次 3：定实现方案，我要求它先讲设计再写码

**我：**
> 那你打算怎么实现？先说思路，别直接甩代码。

**AI：**
三条纪律，其余都是细节：

**① 单一数据源。** 每场投票只存四样东西：

```
options  : 候选项原始顺序（用于并列排序）
votes    : {候选项: 票数}
choices  : {voter_id: 候选项}     ← 一人一条，这就是 total_votes 的来源
status   : open / closed
```

`results` 和 `total_votes` **每次现场推导**，绝不单独存一份计数。这样「票数、人数、排名」在结构上就不可能漂移 —— 而不是靠每处加减小心维护。

**② 原子写。** `ThreadingHTTPServer` 是多线程的，判题器会连发请求。所以每个操作的「校验 + 变更」整体包在一把 `threading.Lock` 里。

**③ id 只在成功时递增。** 校验放在拿锁、分配 id **之前**。非法创建不消耗 `poll_N`。

排序用 `results.sort(key=lambda r: -r["votes"])` 就够了 —— Python 的 sort 是**稳定**的，先按原始顺序铺开，再按票数降序排，并列时自然保持创建顺序，不用手写二级比较。

**我的追问：**
> 为什么不用 `sorted(votes.items(), key=...)`？

**AI：**
因为 dict 的插入顺序虽然靠得住，但「靠某个容器的遍历顺序」是隐式约定；显式先铺 `options` 再按 `-votes` 稳定排序，是**代码里写明了规则**，别人读的时候不用推理 dict 行为。规格第 8 节也明确写了「输出时重新排序 results，不依赖字典顺序」。

**我的收获：** 「不存冗余计数，全部推导」这一条是这题的关键。我原来会想「加一票就 total_votes += 1」，那样改票、重复投票、并发三个场景各要小心一次，很容易漏。

---

## 轮次 4：开工，卡在 git clone（报错 1）

**我：**
> 开始吧。先 clone 下来。
>
> ```
> git clone --depth 1 https://github.com/uhura666/ai_coding_2026.git exam_repo
> fatal: unable to access '...': schannel: AcquireCredentialsHandle failed:
> SEC_E_NO_CREDENTIALS (0x8009030e) - 安全程序包没有可用的凭证
> ```

**AI：**
这是 Windows 上 Git 用 schannel 做 TLS 时的凭证问题，不是网络不通。换 OpenSSL 后端再试：

```bash
# 只对这一次生效
git -c http.sslBackend=openssl clone --depth 1 https://github.com/uhura666/ai_coding_2026.git exam_repo

# 或者当前 shell 全局生效
export GIT_SSL_BACKEND=openssl
```

**结果：** 换成 openssl 后 clone 成功，17 个文件。

**我的收获：** `SEC_E_NO_CREDENTIALS` 这种看着像「没权限」的报错，其实和权限无关，是 TLS 实现相关。以后遇到 Windows 上 Git 连不上，先试换 sslBackend。

---

## 轮次 5：启动服务报错（报错 2）

**我：**
> 我在 `2/` 目录下跑 `python main.py`，报错：
>
> ```
> can't open file '...\exam_repo\2\main.py': [Errno 2] No such file or directory
> ```

**AI：**
`main.py` 在 `2/baseline/python/` 下，不在 `2/` 下。**本地开发时工作目录要在 `baseline/python`**：

```bash
cd 2/baseline/python && PORT=8000 python3 main.py
```

至于 README 里说的「入口文件位于当前 `work/` 根目录」，那是**判题器**的动作：它把你选的 `baseline/<语言>/` 整个拷进 `work/` 再跑，所以 `main.py` 最终确实落在 `work/` 根目录。**你不用自己建 `work/` 目录。**

（这一点我特意又确认了一遍，因为外层 README 说「在 baseline/ 里写」，题目说「复制到 work/ 根目录」，看着像矛盾，其实是一件事的两个视角。）

**我的收获：** 措辞要把「我写代码的目录」和「判题器运行的目录」分开，不然会自己吓自己。

---

## 轮次 6：写测试脚本时踩坑（报错 3）

**我：**
> 我自己加了边界用例，测「voter_id 含空格要被拒绝」这条时，测试脚本先崩了：
>
> ```
> InvalidURL: URL can't contain control characters.
> '/polls/poll_1/votes/u 1' (found at least ' ')
> ```

**AI：**
这是**测试客户端**的问题，不是服务端：`urllib` 不允许 URL 里有裸空格。要测这条得先百分号编码：

```python
from urllib.parse import quote
rejected("PUT", "/polls/poll_1/votes/" + quote("u 1"), {"option": "a"})
# 实际发出的是 /polls/poll_1/votes/u%201
# 服务端 unquote 后拿到 "u 1"，正则 ^[A-Za-z0-9_-]{1,32}$ 不匹配 → 400
```

**我的收获：** 测试失败先分清「被测对象错」还是「测试工具有错」。这次是后者 —— 差点去改服务端代码。

---

## 轮次 7：隐藏用例怎么自测

**我：**
> 样例只有 3 个用例，全过了也不代表能拿分。隐藏用例会打哪些点？帮我列个清单，我照着写测试。

**AI：**
README 第 7 节自己列了，我把它翻译成可执行的断言：

| 覆盖点 | 断言 |
| --- | --- |
| `title` 长度 | 1 ✅ / 80 ✅ / 81 ❌；空串、纯空白 ❌；首尾空白要去掉后判断 |
| `options` 数量 | 2 ✅ / 8 ✅ / 9 ❌ |
| 单项长度 | 40 ✅ / 41 ❌；空串、纯空白 ❌ |
| 去重 | `["A"," A "]` ❌（去空白后重复） |
| `voter_id` | 长度 1 ✅ / 32 ✅ / 33 ❌；`.`、空格等非法字符 ❌ |
| 投票三态 | 首投 +1、改票旧项 -1 且 `total_votes` 不变、重复同项不变 |
| 结票 | 能结；**重复结票返回同一份结果**；结票后投票 ❌ 且数据不变 |
| `reset` | 清空；下一次创建仍是 `poll_1` |
| 排序 | 票数降序；**并列按创建时的原始顺序** |
| 不变式 | 任意时刻 `sum(results.votes) == total_votes` |

**我的追问：**
> 「拒绝」要返回什么状态码？

**AI：**
规格原话是「具体 HTTP 错误码不做强制要求，响应使用 JSON 即可」，重点只有一条：**拒绝时不得改变数据、不得消耗新 id**。我用的约定是 `400` 参数非法 / `404` 投票不存在 / `409` 已结票 —— 都是非 2xx，且都带 `{"error": "..."}`。

**我的收获：** 判分不看具体码，看「拒绝是否无损」。所以测试里我不写 `assert status == 400`，而是写 `assert not (200 <= status < 300)`，再去回读数据确认没变 —— 这样测试和实现都不被错误码绑架。

---

## 轮次 8：要它顺便把并发也测了

**我：**
> 判题器可能连发请求，并发你测了吗？

**AI：**
加两个用例：

1. **40 个不同用户同时投一票** → `total_votes` 必须正好 40，且 `sum(votes) == 40`（丢票或重复计数都会露馅）
2. **同一个用户并发发 80 次**（8 线程 × 10 次）→ `total_votes` 必须正好 1，该选项票数正好 1

再加一个随机模糊测试：随机 120 步「创建 / 投票 / 结票」，每一步之后把所有投票回读一遍，校验不变式 + 排序。

**结果：** 14 个用例全过（`14 passed, 0 failed`）。

**我的收获：** 并发测试不用复杂工具，`threading.Thread` 起 40 个线程就够用了，关键是把「同一用户并发」单独测 —— 这个最容易重复计数。

---

## 轮次 9：最后让它自查「有哪些做了取舍的地方」

**我：**
> 你觉得还有哪些地方没做完或者有坑？我要如实写进 run_instructions.md。

**AI：**
四个，都写进去了：

1. **无持久化** —— 进程重启即清空。规格说「启动状态等同于执行过一次 `POST /reset`」，所以这是符合规格的，不是缺陷。
2. **`option` 精确匹配，不做 strip** —— 创建时选项已去空白存储，投票时若客户端还带首尾空格，会被判为「不是候选项」而拒绝。规格只说「必须是已创建的候选项之一」，我按字面取精确匹配。这是**有歧义的点**，我在文档里标注了。
3. **未处理 `Transfer-Encoding: chunked`** —— 只按 `Content-Length` 读 body。判题器发的都是普通 JSON，够用。
4. **额外加了 `GET /polls/{id}`** —— 规格没要求，但调试时很好用，且是只读接口，不影响任何写入语义。

**我的收获：** 「如实写没做的部分」比假装完美更能拿过程分 —— 尤其是第 2 条，说明我真的读过规格的措辞。

---

## 我自己的操作（非 AI 代劳）

- Fork 仓库、clone 到本地、配 `git config user.name / user.email`
- 按轮次里的命令启动服务，本地跑通 `sample_testcases` 和 `selftest`
- 两次 commit 分开提交（先代码、后文档）
- 发 PR，标题按 `姓名_学号`

---

## 附：截图清单

> 建议补 3~5 张，比纯文字更有说服力。

1. `2/README.md` 规格 + `baseline/python/main.py` 原始代码对照（轮次 2）
2. 第一次跑 `run_sample_testcases.py` 的 PASS 输出
3. `selftest/run_edge_cases.py` 的 `14 passed, 0 failed`
4. 上面那几个报错的原始截图（git clone / main.py 找不到 / InvalidURL）
5. `git log --oneline` 显示两次提交
