"""Checks on the TypeSafe client and its response cache. No test here touches the network.

    python framework/tests/test_typesafe_client.py
"""

from __future__ import annotations

import io
import json
import sys
import tempfile
import urllib.error
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "framework"))

import data_loader
import typesafe_client

CONFIG = data_loader.load_config()
QUESTIONS = {"forecast": {"type": "choice", "instructions": "Pick one", "criteria": {"a": None, "b": None}}}
ANSWER = {"forecast": {"type": "choice", "choice": "a", "confidence": 0.9, "probabilities": {"a": 0.9, "b": 0.1}}}


class _Response:
    def __init__(self, payload: dict) -> None:
        self._body = json.dumps(payload).encode("utf-8")

    def read(self) -> bytes:
        return self._body

    def __enter__(self) -> "_Response":
        return self

    def __exit__(self, *exc: object) -> None:
        return None


def _http_error(code: int, body: str = "{}") -> urllib.error.HTTPError:
    return urllib.error.HTTPError(
        "https://api.typesafe.ai/v1/systemone", code, "error", {}, io.BytesIO(body.encode())
    )


class _Server:
    """Stands in for `urllib.request.urlopen`: plays back a script, records every request."""

    def __init__(self, script: list) -> None:
        self.script = list(script)
        self.requests: list = []

    def __call__(self, request, timeout=None):
        self.requests.append(request)
        step = self.script.pop(0) if len(self.script) > 1 else self.script[0]
        if isinstance(step, Exception):
            raise step
        return _Response(step)


def _ok(state: object = None) -> dict:
    return {"model": "jev-1.13.0", "answers": ANSWER, "usage": {"input_tokens": 120, "output_tokens": 0}}


def _client(server: _Server, sleeps: list | None = None, retries: int = 5):
    return typesafe_client.HttpClient(
        endpoint="https://api.typesafe.ai/v1/systemone",
        model="jev-1.13.0",
        api_key="test-key",
        max_retries=retries,
        urlopen=server,
        sleep=(sleeps.append if sleeps is not None else (lambda seconds: None)),
    )


# --- the cache key ----------------------------------------------------------------------


def test_the_cache_key_changes_with_the_model_the_state_or_the_question() -> None:
    base = typesafe_client.request_key("jev-1.13.0", {"x": 1}, QUESTIONS)
    assert base != typesafe_client.request_key("jev-1.14.0", {"x": 1}, QUESTIONS)
    assert base != typesafe_client.request_key("jev-1.13.0", {"x": 2}, QUESTIONS)
    other = {"forecast": {**QUESTIONS["forecast"], "instructions": "Pick another"}}
    assert base != typesafe_client.request_key("jev-1.13.0", {"x": 1}, other)


def test_the_cache_key_ignores_key_order() -> None:
    first = typesafe_client.request_key("m", {"a": 1, "b": 2}, QUESTIONS)
    second = typesafe_client.request_key("m", {"b": 2, "a": 1}, QUESTIONS)
    assert first == second


# --- the cache --------------------------------------------------------------------------


def test_a_miss_asks_once_and_a_repeat_is_served_from_disk() -> None:
    server = _Server([_ok()])
    with tempfile.TemporaryDirectory() as tmp:
        answerer = typesafe_client.CachedAnswerer(Path(tmp), "jev-1.13.0", client=_client(server))
        request = {"state": {"x": 1}, "questions": QUESTIONS}
        first = answerer([request])[0]
        second = answerer([request])[0]
        assert len(server.requests) == 1
        assert first["answers"] == second["answers"] == ANSWER
        assert first["from_cache"] is False and second["from_cache"] is True
        assert len(list(Path(tmp).glob("*.json"))) == 1


def test_offline_refuses_to_call_on_a_miss() -> None:
    server = _Server([_ok()])
    with tempfile.TemporaryDirectory() as tmp:
        answerer = typesafe_client.CachedAnswerer(
            Path(tmp), "jev-1.13.0", client=_client(server), offline=True
        )
        try:
            answerer([{"state": {"x": 1}, "questions": QUESTIONS}])
        except typesafe_client.CacheMiss:
            assert not server.requests
            return
    raise AssertionError("an offline run called the API")


def test_offline_serves_what_the_cache_holds() -> None:
    server = _Server([_ok()])
    request = {"state": {"x": 1}, "questions": QUESTIONS}
    with tempfile.TemporaryDirectory() as tmp:
        typesafe_client.CachedAnswerer(Path(tmp), "jev-1.13.0", client=_client(server))([request])
        offline = typesafe_client.CachedAnswerer(Path(tmp), "jev-1.13.0", offline=True)
        assert offline([request])[0]["answers"] == ANSWER


def test_a_request_repeated_in_one_batch_is_asked_once() -> None:
    """The model does not answer the same request identically twice; asking twice and caching
    one answer would make the live run and its rebuild from the cache disagree."""
    server = _Server([_ok()])
    with tempfile.TemporaryDirectory() as tmp:
        answerer = typesafe_client.CachedAnswerer(Path(tmp), "jev-1.13.0", client=_client(server))
        request = {"state": {"x": 1}, "questions": QUESTIONS}
        answers = answerer([request, dict(request), {"state": {"x": 2}, "questions": QUESTIONS}])
        assert len(server.requests) == 2
        assert answers[0]["answers"] == answers[1]["answers"]
        assert answerer.calls == 2


def test_answers_come_back_in_request_order() -> None:
    class _Echo(_Server):
        def __call__(self, request, timeout=None):
            self.requests.append(request)
            state = json.loads(request.data.decode("utf-8"))["state"]
            return _Response({"model": "jev-1.13.0", "answers": {"echo": state}, "usage": {}})

    with tempfile.TemporaryDirectory() as tmp:
        answerer = typesafe_client.CachedAnswerer(
            Path(tmp), "jev-1.13.0", client=_client(_Echo([])), concurrency=4
        )
        requests = [{"state": {"i": index}, "questions": QUESTIONS} for index in range(12)]
        answers = answerer(requests)
        assert [answer["answers"]["echo"]["i"] for answer in answers] == list(range(12))


# --- the HTTP client --------------------------------------------------------------------


def test_the_request_carries_the_pinned_model_and_the_bearer_key() -> None:
    server = _Server([_ok()])
    _client(server).ask({"x": 1}, QUESTIONS)
    request = server.requests[0]
    body = json.loads(request.data.decode("utf-8"))
    assert body["model"] == "jev-1.13.0"
    assert body["state"] == {"x": 1} and body["questions"] == QUESTIONS
    assert request.get_header("Authorization") == "Bearer test-key"
    assert request.get_method() == "POST"


def test_rate_limits_and_overload_are_retried_with_backoff() -> None:
    sleeps: list = []
    server = _Server([_http_error(429), _http_error(529), _ok()])
    response = _client(server, sleeps).ask({"x": 1}, QUESTIONS)
    assert response["answers"] == ANSWER
    assert len(server.requests) == 3
    assert sleeps == [1, 2]


def test_retries_are_bounded() -> None:
    server = _Server([_http_error(429)])
    try:
        _client(server, retries=2).ask({"x": 1}, QUESTIONS)
    except typesafe_client.TypeSafeError:
        assert len(server.requests) == 3
        return
    raise AssertionError("an endless rate limit never gave up")


def test_a_bad_request_fails_at_once_with_the_server_message() -> None:
    server = _Server([_http_error(422, '{"detail": "state too long"}')])
    try:
        _client(server).ask({"x": 1}, QUESTIONS)
    except typesafe_client.TypeSafeError as error:
        assert "422" in str(error) and "state too long" in str(error)
        assert len(server.requests) == 1
        return
    raise AssertionError("a validation failure was not raised")


def test_a_missing_api_key_is_named() -> None:
    try:
        typesafe_client.client_from_config(CONFIG, environ={})
    except typesafe_client.MissingApiKey as error:
        assert CONFIG["forecast"]["api_key_env"] in str(error)
        return
    raise AssertionError("a client was built without an API key")


def test_the_client_uses_the_config_model_and_endpoint() -> None:
    client = typesafe_client.client_from_config(CONFIG, environ={"TYPESAFE_API_KEY": "k"})
    assert client.model == CONFIG["forecast"]["model"]
    assert client.endpoint == CONFIG["forecast"]["endpoint"]


def main() -> int:
    tests = [value for name, value in sorted(globals().items()) if name.startswith("test_")]
    failures = 0
    for test in tests:
        try:
            test()
        except Exception as error:
            failures += 1
            print(f"FAIL {test.__name__}: {type(error).__name__}: {error}")
        else:
            print(f"ok   {test.__name__}")
    print(f"\n{len(tests) - failures}/{len(tests)} passed")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
