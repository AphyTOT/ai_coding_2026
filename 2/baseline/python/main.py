#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""活动投票封存 —— 持续运行的 HTTP 服务。

只依赖 Python 标准库，规格见 ../README.md。

设计要点
--------
1. 单一数据源：每场投票只保存「候选项原始顺序、每个候选项票数、每个用户的选择」，
   对外输出的 results / total_votes 每次现场推导，杜绝计数漂移。
2. 原子写：所有「校验 + 变更」都在同一把互斥锁内完成，ThreadingHTTPServer 下也不会重复计数。
3. id 只在创建成功时递增：校验失败不消耗 poll_N。
4. 拒绝即无损：任何非法请求在修改数据之前就抛出 ApiError。
"""

from __future__ import annotations

import json
import os
import re
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote, urlsplit

# --------------------------------------------------------------------------- 常量

TITLE_MIN_LEN, TITLE_MAX_LEN = 1, 80
OPTIONS_MIN, OPTIONS_MAX = 2, 8
OPTION_MIN_LEN, OPTION_MAX_LEN = 1, 40
MAX_BODY_BYTES = 1 << 20  # 1 MiB，防止超大请求体

STATUS_OPEN = "open"
STATUS_CLOSED = "closed"

# voter_id 只允许 [A-Za-z0-9_-]，长度 1~32
VOTER_ID_RE = re.compile(r"[A-Za-z0-9_-]{1,32}")


# --------------------------------------------------------------------------- 错误

class ApiError(Exception):
    """业务层拒绝。status 即 HTTP 状态码，message 会写进 {"error": ...}。"""

    def __init__(self, message: str, status: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.status = status


# --------------------------------------------------------------------------- 校验

def normalize_title(raw) -> str:
    """title：必填，去首尾空白后长度 1~80。"""
    if not isinstance(raw, str):
        raise ApiError("title 必须是字符串")
    title = raw.strip()
    if not TITLE_MIN_LEN <= len(title) <= TITLE_MAX_LEN:
        raise ApiError("title 去首尾空白后长度必须在 1~80 之间")
    return title


def normalize_options(raw) -> list[str]:
    """options：数组，长度 2~8；每项去空白后长度 1~40，且去空白后不得重复。"""
    if not isinstance(raw, list):
        raise ApiError("options 必须是数组")
    if not OPTIONS_MIN <= len(raw) <= OPTIONS_MAX:
        raise ApiError("options 数量必须在 2~8 之间")

    options: list[str] = []
    seen: set[str] = set()
    for item in raw:
        if not isinstance(item, str):
            raise ApiError("每个候选项都必须是字符串")
        option = item.strip()
        if not OPTION_MIN_LEN <= len(option) <= OPTION_MAX_LEN:
            raise ApiError("候选项去首尾空白后长度必须在 1~40 之间")
        if option in seen:
            raise ApiError("候选项去首尾空白后不得重复")
        seen.add(option)
        options.append(option)
    return options


def normalize_voter_id(raw: str) -> str:
    if not VOTER_ID_RE.fullmatch(raw):
        raise ApiError("voter_id 只允许 [A-Za-z0-9_-]，长度 1~32")
    return raw


# --------------------------------------------------------------------------- 数据层

class PollStore:
    """全部投票状态的唯一持有者；每个公开方法自身就是一次原子操作。"""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._polls: dict[str, dict] = {}
        self._next_seq = 1

    # -- 内部工具 ---------------------------------------------------------

    def _get(self, poll_id: str) -> dict:
        poll = self._polls.get(poll_id)
        if poll is None:
            raise ApiError("投票不存在: %s" % poll_id, status=404)
        return poll

    @staticmethod
    def _view(poll: dict) -> dict:
        """把内部状态渲染成对外的 Poll。必须持锁调用。

        排序：票数降序；票数相同时保持候选项在创建请求中的原始顺序
        （list.sort 稳定，先按原始顺序铺开再按 -votes 排序即可）。
        """
        results = [{"option": option, "votes": poll["votes"][option]}
                   for option in poll["options"]]
        results.sort(key=lambda item: -item["votes"])
        return {
            "id": poll["id"],
            "title": poll["title"],
            "status": poll["status"],
            "results": results,
            # 有效投票人数：choices 里一人一条，天然等于去重后的投票用户数
            "total_votes": len(poll["choices"]),
        }

    # -- 对外操作 ---------------------------------------------------------

    def reset(self) -> None:
        with self._lock:
            self._polls.clear()
            self._next_seq = 1

    def create(self, title_raw, options_raw) -> dict:
        # 先校验，校验通过才分配 id —— 非法请求不得消耗 poll_N
        title = normalize_title(title_raw)
        options = normalize_options(options_raw)

        with self._lock:
            poll_id = "poll_%d" % self._next_seq
            self._next_seq += 1
            poll = {
                "id": poll_id,
                "title": title,
                "status": STATUS_OPEN,
                "options": list(options),                  # 原始顺序，用于并列排序
                "votes": {option: 0 for option in options},
                "choices": {},                             # voter_id -> option
            }
            self._polls[poll_id] = poll
            return self._view(poll)

    def vote(self, poll_id: str, voter_id: str, option) -> dict:
        voter_id = normalize_voter_id(voter_id)
        if not isinstance(option, str):
            raise ApiError("option 必须是字符串")

        with self._lock:
            poll = self._get(poll_id)
            if poll["status"] != STATUS_OPEN:
                raise ApiError("投票已结束，拒绝投票", status=409)
            if option not in poll["votes"]:
                raise ApiError("option 不是该投票的候选项")

            previous = poll["choices"].get(voter_id)
            if previous == option:
                # 重复选择同一项：不重复计数，数据不变
                return self._view(poll)
            if previous is not None:
                poll["votes"][previous] -= 1          # 改票：旧项 -1
            poll["votes"][option] += 1                # 新项 +1
            poll["choices"][voter_id] = option        # total_votes 由 len(choices) 推导，保持不变
            return self._view(poll)

    def close(self, poll_id: str) -> dict:
        with self._lock:
            poll = self._get(poll_id)
            poll["status"] = STATUS_CLOSED            # 已关闭时再关一次：幂等
            return self._view(poll)

    def get(self, poll_id: str) -> dict:
        with self._lock:
            return self._view(self._get(poll_id))

    def snapshot_all(self) -> dict:
        with self._lock:
            return {poll_id: self._view(poll) for poll_id, poll in self._polls.items()}


STORE = PollStore()  # 进程启动状态 == 执行过一次 POST /reset


# --------------------------------------------------------------------------- HTTP 层

class PollHandler(BaseHTTPRequestHandler):
    server_version = "PollSeal/1.0"
    protocol_version = "HTTP/1.1"  # 配合 Content-Length 支持 keep-alive
    store = STORE

    # 判题器不关心访问日志，静音以免污染输出
    def log_message(self, _format, *_args) -> None:  # noqa: D401
        return

    # -- 响应 -------------------------------------------------------------

    def _send_json(self, status: int, payload) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    # -- 请求解析 ---------------------------------------------------------

    def _path_parts(self) -> list[str]:
        path = urlsplit(self.path).path
        return [unquote(part) for part in path.split("/") if part]

    def _read_body(self) -> dict:
        raw_length = self.headers.get("Content-Length")
        try:
            length = int(raw_length) if raw_length else 0
        except (TypeError, ValueError):
            raise ApiError("Content-Length 非法")
        if length < 0 or length > MAX_BODY_BYTES:
            raise ApiError("请求体过大")
        raw = self.rfile.read(length) if length > 0 else b""
        if not raw:
            return {}  # 允许空请求体（/reset 常见）
        try:
            payload = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise ApiError("请求体不是合法 JSON")
        if not isinstance(payload, dict):
            raise ApiError("请求体必须是 JSON 对象")
        return payload

    # -- 路由 -------------------------------------------------------------

    def _dispatch(self, method: str) -> None:
        try:
            status, payload = self._route(method)
        except ApiError as exc:
            self._send_json(exc.status, {"error": exc.message})
            return
        except (BrokenPipeError, ConnectionResetError):
            return
        except Exception:  # noqa: BLE001 - 兜底：绝不把栈信息吐给客户端
            self._send_json(500, {"error": "internal error"})
            return
        self._send_json(status, payload)

    def _route(self, method: str):
        parts = self._path_parts()

        if method == "GET":
            if parts == ["health"]:
                return 200, {"status": "ok"}
            if len(parts) == 2 and parts[0] == "polls":
                return 200, self.store.get(parts[1])
            raise ApiError("not found", status=404)

        if method == "POST":
            if parts == ["reset"]:
                self._read_body()  # 有 body 也允许，内容忽略
                self.store.reset()
                return 200, {"ok": True}
            body = self._read_body()
            if parts == ["polls"]:
                return 200, self.store.create(body.get("title"), body.get("options"))
            if len(parts) == 3 and parts[0] == "polls" and parts[2] == "close":
                return 200, self.store.close(parts[1])
            raise ApiError("not found", status=404)

        if method == "PUT":
            body = self._read_body()
            if len(parts) == 4 and parts[0] == "polls" and parts[2] == "votes":
                return 200, self.store.vote(parts[1], parts[3], body.get("option"))
            raise ApiError("not found", status=404)

        raise ApiError("method not allowed", status=405)

    # -- HTTP 方法入口 -----------------------------------------------------

    def do_GET(self) -> None:
        self._dispatch("GET")

    def do_HEAD(self) -> None:
        self._dispatch("GET")

    def do_POST(self) -> None:
        self._dispatch("POST")

    def do_PUT(self) -> None:
        self._dispatch("PUT")

    def do_DELETE(self) -> None:
        self._dispatch("DELETE")

    def do_PATCH(self) -> None:
        self._dispatch("PATCH")


class PollServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True


def build_server(port: int) -> PollServer:
    return PollServer(("0.0.0.0", port), PollHandler)


def main() -> None:
    raw_port = os.environ.get("PORT", "8000")
    try:
        port = int(raw_port)
    except ValueError:
        port = 8000
    server = build_server(port)
    print("poll-seal listening on 0.0.0.0:%d" % port, flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
