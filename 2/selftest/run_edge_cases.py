#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""活动投票封存 —— 边界/隐藏用例自测。

用法（先启动服务）：
    PORT=8000 python3 main.py &
    python3 selftest/run_edge_cases.py

对照 README「5. 边界与校验汇总」和「隐藏用例常见覆盖点」逐条验证，
并额外做并发与随机模糊测试，检查
    sum(results[].votes) == total_votes == 有效投票人数
这条核心不变量。
"""

import json
import os
import random
import sys
import threading
import urllib.error
import urllib.request
from urllib.parse import quote

BASE_URL = os.environ.get("BASE_URL", "http://127.0.0.1:" + os.environ.get("PORT", "8000")).rstrip("/")

PASSED = 0
FAILED = 0
FAILURES = []


# --------------------------------------------------------------------------- 客户端

def call(method, path, body=None):
    data = None if body is None else json.dumps(body, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        BASE_URL + path,
        data=data,
        headers={"Content-Type": "application/json"},
        method=method,
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            raw = response.read().decode("utf-8")
            return response.status, (json.loads(raw) if raw else None)
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8")
        try:
            return exc.code, (json.loads(raw) if raw else None)
        except json.JSONDecodeError:
            return exc.code, raw


def rejected(method, path, body=None):
    """断言被拒绝（非 2xx）。返回响应便于调用方再检查数据未变。"""
    status, payload = call(method, path, body)
    assert not (200 <= status < 300), "本应被拒绝，却返回 %s: %s" % (status, payload)
    return status, payload


def ok(method, path, body=None):
    status, payload = call(method, path, body)
    assert 200 <= status < 300, "本应成功，却返回 %s: %s" % (status, payload)
    return payload


def check(name, function):
    global PASSED, FAILED
    try:
        function()
        PASSED += 1
    except Exception as exc:  # noqa: BLE001
        FAILED += 1
        FAILURES.append((name, "%s: %s" % (type(exc).__name__, exc)))
        print("[FAIL] %s -> %s: %s" % (name, type(exc).__name__, exc))
        return
    print("[PASS] %s" % name)


def reset():
    ok("POST", "/reset", {})


def create(title="Lunch", options=("Rice", "Noodles")):
    return ok("POST", "/polls", {"title": title, "options": list(options)})


def votes_of(poll):
    return {item["option"]: item["votes"] for item in poll["results"]}


def invariant(poll):
    """results 票数之和 == total_votes，且排序为「票数降序」。"""
    total = sum(item["votes"] for item in poll["results"])
    assert total == poll["total_votes"], "票数之和 %d != total_votes %d" % (total, poll["total_votes"])
    counts = [item["votes"] for item in poll["results"]]
    assert counts == sorted(counts, reverse=True), "results 未按票数降序: %s" % counts


# --------------------------------------------------------------------------- 创建校验

def title_bounds():
    reset()
    rejected("POST", "/polls", {"title": "", "options": ["A", "B"]})
    rejected("POST", "/polls", {"title": "   ", "options": ["A", "B"]})
    rejected("POST", "/polls", {"options": ["A", "B"]})
    rejected("POST", "/polls", {"title": 123, "options": ["A", "B"]})

    assert create("A", ["x", "y"])["title"] == "A"                    # 1 字符可以
    assert create("B" * 80, ["x", "y"])["title"] == "B" * 80          # 80 可以
    rejected("POST", "/polls", {"title": "C" * 81, "options": ["x", "y"]})  # 81 拒绝
    # 去首尾空白后 80 字符，应通过且保存为去空白后的值
    padded = "  " + "D" * 80 + "  "
    assert create(padded, ["x", "y"])["title"] == "D" * 80


def options_bounds():
    reset()
    rejected("POST", "/polls", {"title": "t", "options": ["only"]})
    rejected("POST", "/polls", {"title": "t", "options": ["a"] * 9})
    rejected("POST", "/polls", {"title": "t", "options": "a,b"})
    rejected("POST", "/polls", {"title": "t"})
    rejected("POST", "/polls", {"title": "t", "options": [1, 2]})
    rejected("POST", "/polls", {"title": "t", "options": ["", "b"]})
    rejected("POST", "/polls", {"title": "t", "options": ["   ", "b"]})

    assert len(create("t2", ["a", "b"])["results"]) == 2              # 2 个可以
    eight = ["o%d" % i for i in range(8)]
    poll = create("t3", eight)
    assert [item["option"] for item in poll["results"]] == eight      # 8 个可以，保持原始顺序
    rejected("POST", "/polls", {"title": "t4", "options": ["o%d" % i for i in range(9)]})

    assert create("t5", ["E" * 40, "b"])["results"][0]["option"] == "E" * 40   # 40 可以
    rejected("POST", "/polls", {"title": "t6", "options": ["F" * 41, "b"]})   # 41 拒绝


def options_dedup_after_strip():
    reset()
    rejected("POST", "/polls", {"title": "t", "options": ["A", "A"]})
    rejected("POST", "/polls", {"title": "t", "options": ["A", " A "]})   # 去空白后重复
    rejected("POST", "/polls", {"title": "t", "options": ["A", "A ", "B"]})
    # 去空白后不同的应当通过，并保存去空白后的值
    poll = create("t", [" A ", "B"])
    assert [item["option"] for item in poll["results"]] == ["A", "B"]


def invalid_request_does_not_consume_id():
    reset()
    for _ in range(5):
        rejected("POST", "/polls", {"title": "x" * 81, "options": ["a", "b"]})
    assert create("ok", ["a", "b"])["id"] == "poll_1", "非法请求消耗了 id"
    assert create("ok2", ["a", "b"])["id"] == "poll_2"


def malformed_json():
    reset()
    for body in (b"{", b"[]", b"null", b'"str"'):
        request = urllib.request.Request(
            BASE_URL + "/polls", data=body,
            headers={"Content-Type": "application/json"}, method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                raise AssertionError("非法 JSON 被接受: %s" % response.status)
        except urllib.error.HTTPError as exc:
            assert not (200 <= exc.code < 300)


# --------------------------------------------------------------------------- 多场投票

def multiple_polls_are_independent():
    reset()
    first = create("One", ["a", "b"])
    second = create("Two", ["x", "y", "z"])
    assert first["id"] == "poll_1" and second["id"] == "poll_2"
    ok("PUT", "/polls/poll_1/votes/u1", {"option": "a"})
    ok("PUT", "/polls/poll_2/votes/u1", {"option": "z"})   # 同一个 voter 在不同投票里各有一票
    assert votes_of(ok("GET", "/polls/poll_1")) == {"a": 1, "b": 0}
    assert votes_of(ok("GET", "/polls/poll_2")) == {"x": 0, "y": 0, "z": 1}
    assert ok("GET", "/polls/poll_1")["total_votes"] == 1
    assert ok("GET", "/polls/poll_2")["total_votes"] == 1


# --------------------------------------------------------------------------- 投票 / 改票

def first_vote_and_change():
    reset()
    create("Color", ["Red", "Blue"])
    poll = ok("PUT", "/polls/poll_1/votes/u_1", {"option": "Blue"})
    invariant(poll)
    assert votes_of(poll) == {"Red": 0, "Blue": 1}
    assert poll["total_votes"] == 1
    assert poll["results"][0] == {"option": "Blue", "votes": 1}   # 票数降序

    poll = ok("PUT", "/polls/poll_1/votes/u_1", {"option": "Red"})   # 改票
    invariant(poll)
    assert votes_of(poll) == {"Red": 1, "Blue": 0}, "改票后旧项未清零"
    assert poll["total_votes"] == 1, "改票不应改变 total_votes"

    poll = ok("PUT", "/polls/poll_1/votes/u_1", {"option": "Red"})   # 重复选同一项
    invariant(poll)
    assert votes_of(poll) == {"Red": 1, "Blue": 0}, "重复投票被重复计数"
    assert poll["total_votes"] == 1


def many_voters_and_tie_order():
    reset()
    create("Tie", ["a", "b", "c"])
    ok("PUT", "/polls/poll_1/votes/u1", {"option": "c"})
    ok("PUT", "/polls/poll_1/votes/u2", {"option": "c"})
    poll = ok("PUT", "/polls/poll_1/votes/u3", {"option": "a"})
    invariant(poll)
    # c 有 2 票排第一；a=1、b=0，b 与 a 不同票，剩 b 排最后
    assert [item["option"] for item in poll["results"]] == ["c", "a", "b"]
    assert poll["total_votes"] == 3

    # 并列时应回到创建顺序：a、b 都 1 票，c 0 票
    reset()
    create("Tie2", ["a", "b", "c"])
    ok("PUT", "/polls/poll_1/votes/u1", {"option": "b"})
    poll = ok("PUT", "/polls/poll_1/votes/u2", {"option": "a"})
    assert [item["option"] for item in poll["results"]] == ["a", "b", "c"], "并列未按创建顺序"


def vote_validation():
    reset()
    create("V", ["a", "b"])
    before = ok("GET", "/polls/poll_1")

    rejected("PUT", "/polls/poll_1/votes/u1", {"option": "zzz"})        # 非候选项
    rejected("PUT", "/polls/poll_1/votes/u1", {})                       # 缺 option
    rejected("PUT", "/polls/poll_1/votes/u1", {"option": 1})            # 类型错
    rejected("PUT", "/polls/poll_404/votes/u1", {"option": "a"})        # 投票不存在
    rejected("PUT", "/polls/poll_1/votes/u.1", {"option": "a"})         # 非法字符
    rejected("PUT", "/polls/poll_1/votes/" + "u" * 33, {"option": "a"}) # 超长
    rejected("PUT", "/polls/poll_1/votes/" + quote("u 1"), {"option": "a"})  # 空格

    assert ok("GET", "/polls/poll_1") == before, "拒绝请求改变了数据"

    # 32 字符合法
    poll = ok("PUT", "/polls/poll_1/votes/" + "v" * 32, {"option": "a"})
    assert poll["total_votes"] == 1
    # 1 字符合法
    poll = ok("PUT", "/polls/poll_1/votes/z", {"option": "b"})
    assert poll["total_votes"] == 2


# --------------------------------------------------------------------------- 结票

def close_semantics():
    reset()
    create("C", ["a", "b"])
    ok("PUT", "/polls/poll_1/votes/u1", {"option": "a"})
    closed = ok("POST", "/polls/poll_1/close")
    assert closed["status"] == "closed"
    again = ok("POST", "/polls/poll_1/close")            # 幂等
    assert again == closed, "重复结票返回了不同结果"

    rejected("PUT", "/polls/poll_1/votes/u2", {"option": "b"})   # 结票后拒绝投票
    rejected("PUT", "/polls/poll_1/votes/u1", {"option": "b"})   # 结票后拒绝改票
    assert ok("GET", "/polls/poll_1") == closed, "结票后被拒绝的请求改动了数据"
    rejected("POST", "/polls/poll_404/close")                   # 结不存在的投票


# --------------------------------------------------------------------------- 重置

def reset_semantics():
    reset()
    create("R", ["a", "b"])
    ok("PUT", "/polls/poll_1/votes/u1", {"option": "a"})
    assert ok("POST", "/reset", {}) == {"ok": True}
    rejected("GET", "/polls/poll_1")                    # 旧数据已清空
    assert create("R2", ["a", "b"])["id"] == "poll_1", "reset 后未重新从 poll_1 开始"
    # reset 不需要请求体
    status, payload = call("POST", "/reset")
    assert 200 <= status < 300 and payload == {"ok": True}


# --------------------------------------------------------------------------- 并发

def concurrent_distinct_voters():
    reset()
    create("Race", ["a", "b"])
    voters = ["u%d" % i for i in range(40)]
    errors = []

    def worker(voter):
        try:
            ok("PUT", "/polls/poll_1/votes/" + voter, {"option": random.choice(["a", "b"])})
        except Exception as exc:  # noqa: BLE001
            errors.append(exc)

    threads = [threading.Thread(target=worker, args=(v,)) for v in voters]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert not errors, "并发投票出错: %s" % errors[:3]
    poll = ok("GET", "/polls/poll_1")
    invariant(poll)
    assert poll["total_votes"] == 40, "并发下丢票或重复计数: %s" % poll["total_votes"]


def concurrent_same_voter():
    reset()
    create("Race2", ["a", "b"])

    def worker():
        for _ in range(10):
            call("PUT", "/polls/poll_1/votes/only", {"option": "a"})

    threads = [threading.Thread(target=worker) for _ in range(8)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    poll = ok("GET", "/polls/poll_1")
    invariant(poll)
    assert poll["total_votes"] == 1, "同一用户的并发重复投票被重复计数"
    assert votes_of(poll)["a"] == 1, "同一用户的并发重复投票被重复计数"


# --------------------------------------------------------------------------- 随机模糊

def fuzz_invariants():
    reset()
    random.seed(20260101)
    created = []
    for _ in range(120):
        action = random.random()
        if action < 0.25 or not created:
            status, poll = call("POST", "/polls", {
                "title": "t%d" % random.randint(0, 10 ** 6),
                "options": ["o%d" % i for i in range(random.randint(2, 5))],
            })
            if 200 <= status < 300:
                created.append(poll["id"])
                invariant(poll)
        elif action < 0.85:
            poll_id = random.choice(created)
            voter = "u%d" % random.randint(0, 6)
            status, poll = call("PUT", "/polls/%s/votes/%s" % (poll_id, voter), {"option": "o0"})
            if 200 <= status < 300:
                invariant(poll)
        else:
            poll_id = random.choice(created)
            status, poll = call("POST", "/polls/%s/close" % poll_id)
            if 200 <= status < 300:
                invariant(poll)
        # 每一步都回读校验：total_votes 与票数之和必须一致
        for poll_id in created:
            invariant(ok("GET", "/polls/" + poll_id))


# --------------------------------------------------------------------------- 入口

def main():
    checks = [
        ("title 长度边界 1/80/81 与空白", title_bounds),
        ("options 数量 2/8/9 与单项长度 40/41", options_bounds),
        ("候选项去空白后查重", options_dedup_after_strip),
        ("非法创建不消耗 id", invalid_request_does_not_consume_id),
        ("非法 JSON 请求体", malformed_json),
        ("多场投票相互独立", multiple_polls_are_independent),
        ("首次投票 / 改票 / 重复投票", first_vote_and_change),
        ("多人投票与并列排序", many_voters_and_tie_order),
        ("投票参数校验且不改数据", vote_validation),
        ("结票幂等与结票后拒绝", close_semantics),
        ("reset 全量清空并重置 id", reset_semantics),
        ("并发 40 人各投一票", concurrent_distinct_voters),
        ("同一用户并发重复投票", concurrent_same_voter),
        ("随机操作序列不变量", fuzz_invariants),
    ]
    for name, function in checks:
        check(name, function)

    print("\n%d passed, %d failed" % (PASSED, FAILED))
    for name, reason in FAILURES:
        print("  - %s: %s" % (name, reason))
    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())
