"""Small HTTP helpers on top of urllib with retries and a polite delay."""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request

USER_AGENT = "Mozilla/5.0 (compatible; ktv-ranking/1.0)"
TIMEOUT = 30
RETRIES = 3
DELAY = 1.0  # seconds between requests, to stay polite

_last_request = 0.0


def _open(req: urllib.request.Request) -> bytes:
    global _last_request
    last_error: Exception | None = None
    for attempt in range(RETRIES):
        wait = _last_request + DELAY - time.monotonic()
        if wait > 0:
            time.sleep(wait)
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                body = resp.read()
            _last_request = time.monotonic()
            return body
        except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
            _last_request = time.monotonic()
            last_error = exc
            # 4xx will not get better on retry
            if isinstance(exc, urllib.error.HTTPError) and 400 <= exc.code < 500:
                break
            time.sleep(2 ** attempt)
    raise RuntimeError(f"{req.get_method()} {req.full_url} failed: {last_error}")


def get_bytes(url: str, headers: dict[str, str] | None = None) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, **(headers or {})})
    return _open(req)


def get_text(url: str, headers: dict[str, str] | None = None) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, **(headers or {})})
    return _open(req).decode("utf-8", errors="replace")


def post_json_array(url: str, payload: dict, headers: dict[str, str] | None = None):
    """POST `[payload]` the way both Taiwanese KTV sites' front-ends do, return parsed JSON."""
    req = urllib.request.Request(
        url,
        data=json.dumps([payload], ensure_ascii=False).encode("utf-8"),
        method="POST",
        headers={
            "User-Agent": USER_AGENT,
            "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
            **(headers or {}),
        },
    )
    body = _open(req).decode("utf-8", errors="replace").strip()
    if not body:
        raise RuntimeError(f"POST {url} returned an empty body")
    try:
        return json.loads(body)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"POST {url} returned non-JSON: {body[:120]!r}") from exc
