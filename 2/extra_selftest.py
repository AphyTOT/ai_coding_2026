#!/usr/bin/env python3
"""Extra edge-case checks beyond the official sample script."""

import json
import os
import sys
import urllib.error
import urllib.request

BASE_URL = os.environ.get(
    "BASE_URL", "http://localhost:" + os.environ.get("PORT", "8000")
).rstrip("/")
PASSED = 0
FAILED = 0


def request(method, path, body=None, expect_error=False):
    data = None if body is None else json.dumps(body, ensure_ascii=False).encode()
    call = urllib.request.Request(
        BASE_URL + path,
        data=data,
        headers={"Content-Type": "application/json"},
        method=method,
    )
    try:
        with urllib.request.urlopen(call, timeout=3) as response:
            status = response.status
            payload = json.loads(response.read().decode())
            if expect_error:
                raise AssertionError(f"expected error, got {status} {payload}")
            return status, payload
    except urllib.error.HTTPError as exc:
        payload = json.loads(exc.read().decode() or "{}")
        if not expect_error:
            raise AssertionError(f"unexpected HTTP {exc.code}: {payload}") from exc
        return exc.code, payload


def check(name, function):
    global PASSED, FAILED
    try:
        function()
        PASSED += 1
        print(f"[PASS] {name}")
    except Exception as exc:
        FAILED += 1
        print(f"[FAIL] {name}: {exc}")


def change_vote_and_tie_order():
    request("POST", "/reset", {})
    _, poll = request(
        "POST",
        "/polls",
        {"title": "午餐", "options": ["米饭", "面条", "饺子"]},
    )
    assert poll["id"] == "poll_1"
    request("PUT", "/polls/poll_1/votes/u1", {"option": "米饭"})
    _, poll = request("PUT", "/polls/poll_1/votes/u1", {"option": "面条"})
    assert poll["total_votes"] == 1
    assert poll["results"][0] == {"option": "面条", "votes": 1}
    assert poll["results"][1]["votes"] == 0 and poll["results"][2]["votes"] == 0
    # same option again
    _, again = request("PUT", "/polls/poll_1/votes/u1", {"option": "面条"})
    assert again == poll


def close_idempotent_and_reject():
    request("POST", "/reset", {})
    request("POST", "/polls", {"title": "Color", "options": ["Red", "Blue"]})
    _, closed = request("POST", "/polls/poll_1/close", {})
    assert closed["status"] == "closed"
    _, again = request("POST", "/polls/poll_1/close", {})
    assert again == closed
    code, _ = request(
        "PUT", "/polls/poll_1/votes/u2", {"option": "Red"}, expect_error=True
    )
    assert code >= 400


def validation_and_id_not_consumed():
    request("POST", "/reset", {})
    code, _ = request(
        "POST",
        "/polls",
        {"title": "", "options": ["A", "B"]},
        expect_error=True,
    )
    assert code >= 400
    _, poll = request("POST", "/polls", {"title": "OK", "options": ["A", "B"]})
    assert poll["id"] == "poll_1"

    code, _ = request(
        "POST",
        "/polls",
        {"title": "Dup", "options": [" A ", "A"]},
        expect_error=True,
    )
    assert code >= 400
    _, poll2 = request("POST", "/polls", {"title": "Two", "options": ["X", "Y"]})
    assert poll2["id"] == "poll_2"

    # space is illegal for voter_id; send as %20 so urllib accepts the URL
    code, _ = request(
        "PUT",
        "/polls/poll_2/votes/bad%20voter",
        {"option": "X"},
        expect_error=True,
    )
    assert code >= 400
    # too long (>32)
    long_id = "a" * 33
    code, _ = request(
        "PUT",
        f"/polls/poll_2/votes/{long_id}",
        {"option": "X"},
        expect_error=True,
    )
    assert code >= 400


def reset_restarts_ids():
    request("POST", "/reset", {})
    request("POST", "/polls", {"title": "A", "options": ["1", "2"]})
    request("POST", "/polls", {"title": "B", "options": ["1", "2"]})
    request("POST", "/reset", {})
    _, poll = request("POST", "/polls", {"title": "C", "options": ["1", "2"]})
    assert poll["id"] == "poll_1"


check("改票 / 重复投票 / 排序", change_vote_and_tie_order)
check("结票幂等与拒投", close_idempotent_and_reject)
check("校验失败不耗 id", validation_and_id_not_consumed)
check("reset 后 id 重计", reset_restarts_ids)
print(f"{PASSED} passed, {FAILED} failed")
sys.exit(1 if FAILED else 0)
