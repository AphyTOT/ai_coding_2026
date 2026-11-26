import json
import os
import re
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote, urlsplit

VOTER_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,32}$")

_lock = threading.Lock()
_polls: dict[str, dict] = {}
_next_poll_index = 1


def reset_state() -> None:
    global _polls, _next_poll_index
    _polls = {}
    _next_poll_index = 1


def error_payload(message: str) -> dict:
    return {"error": message}


def build_results(poll: dict) -> list[dict]:
    indexed = list(enumerate(poll["options"]))
    indexed.sort(key=lambda item: (-poll["votes"][item[1]], item[0]))
    return [
        {"option": option, "votes": poll["votes"][option]}
        for _index, option in indexed
    ]


def poll_to_response(poll: dict) -> dict:
    return {
        "id": poll["id"],
        "title": poll["title"],
        "status": poll["status"],
        "results": build_results(poll),
        "total_votes": len(poll["voter_choice"]),
    }


def validate_create(body: dict) -> tuple[str, list[str]]:
    title_raw = body.get("title")
    options_raw = body.get("options")
    if not isinstance(title_raw, str):
        raise ValueError("title must be a string")
    title = title_raw.strip()
    if not 1 <= len(title) <= 80:
        raise ValueError("title length must be 1..80 after strip")

    if not isinstance(options_raw, list) or not 2 <= len(options_raw) <= 8:
        raise ValueError("options length must be 2..8")

    options: list[str] = []
    seen: set[str] = set()
    for item in options_raw:
        if not isinstance(item, str):
            raise ValueError("option must be a string")
        option = item.strip()
        if not 1 <= len(option) <= 40:
            raise ValueError("option length must be 1..40 after strip")
        if option in seen:
            raise ValueError("duplicate option")
        seen.add(option)
        options.append(option)
    return title, options


def create_poll(title: str, options: list[str]) -> dict:
    global _next_poll_index
    poll_id = f"poll_{_next_poll_index}"
    _next_poll_index += 1
    poll = {
        "id": poll_id,
        "title": title,
        "status": "open",
        "options": options,
        "votes": {option: 0 for option in options},
        "voter_choice": {},
    }
    _polls[poll_id] = poll
    return poll


def cast_vote(poll: dict, voter_id: str, option: str) -> dict:
    if poll["status"] != "open":
        raise PermissionError("poll is closed")
    if option not in poll["votes"]:
        raise ValueError("option not found")

    previous = poll["voter_choice"].get(voter_id)
    if previous == option:
        return poll
    if previous is not None:
        poll["votes"][previous] -= 1
    else:
        # first vote for this voter
        pass
    poll["votes"][option] += 1
    poll["voter_choice"][voter_id] = option
    return poll


class Handler(BaseHTTPRequestHandler):
    def log_message(self, _format, *_args):
        return

    def send_json(self, status: int, value: dict) -> None:
        data = json.dumps(value, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length) if length > 0 else b"{}"
        if not raw:
            raw = b"{}"
        value = json.loads(raw)
        if not isinstance(value, dict):
            raise ValueError("body must be object")
        return value

    def parts(self) -> list[str]:
        return [unquote(item) for item in urlsplit(self.path).path.split("/") if item]

    def do_GET(self) -> None:
        if urlsplit(self.path).path == "/health":
            self.send_json(200, {"status": "ok"})
            return
        self.send_json(404, error_payload("not found"))

    def do_POST(self) -> None:
        try:
            body = self.read_json()
        except Exception:
            self.send_json(400, error_payload("invalid json"))
            return

        parts = self.parts()
        with _lock:
            try:
                if parts == ["reset"]:
                    reset_state()
                    self.send_json(200, {"ok": True})
                    return

                if parts == ["polls"]:
                    title, options = validate_create(body)
                    poll = create_poll(title, options)
                    self.send_json(200, poll_to_response(poll))
                    return

                if len(parts) == 3 and parts[0] == "polls" and parts[2] == "close":
                    poll_id = parts[1]
                    poll = _polls.get(poll_id)
                    if poll is None:
                        self.send_json(404, error_payload("poll not found"))
                        return
                    poll["status"] = "closed"
                    self.send_json(200, poll_to_response(poll))
                    return

                self.send_json(404, error_payload("not found"))
            except ValueError as exc:
                self.send_json(400, error_payload(str(exc)))
            except Exception:
                self.send_json(400, error_payload("invalid request"))

    def do_PUT(self) -> None:
        try:
            body = self.read_json()
        except Exception:
            self.send_json(400, error_payload("invalid json"))
            return

        parts = self.parts()
        if len(parts) != 4 or parts[0] != "polls" or parts[2] != "votes":
            self.send_json(404, error_payload("not found"))
            return

        poll_id = parts[1]
        voter_id = parts[3]
        option = body.get("option")

        with _lock:
            try:
                if not VOTER_ID_RE.fullmatch(voter_id):
                    raise ValueError("invalid voter_id")
                if not isinstance(option, str):
                    raise ValueError("option must be a string")

                poll = _polls.get(poll_id)
                if poll is None:
                    self.send_json(404, error_payload("poll not found"))
                    return

                cast_vote(poll, voter_id, option)
                self.send_json(200, poll_to_response(poll))
            except PermissionError as exc:
                self.send_json(409, error_payload(str(exc)))
            except ValueError as exc:
                self.send_json(400, error_payload(str(exc)))
            except Exception:
                self.send_json(400, error_payload("invalid request"))


if __name__ == "__main__":
    reset_state()
    port = int(os.environ.get("PORT", "8000"))
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()
