"""Call TypeSafe System One and keep every answer on disk.

The forecast in `DESIGN.md` section 9.3 is the one result in this project that depends on a
service outside the repository. Two things keep it reproducible anyway. The model is pinned
by its full version in `config.yaml`, never `jev-latest`. And every answer is written to
`results/forecast_cache/`, keyed by a hash of the exact model, state and question that
produced it, so `make all` rebuilds the result from the cache without calling the API, and
any single number can be traced back to the answer behind it.

Only the standard library is used: the core of the framework has no business depending on a
vendor SDK for one POST request.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

RETRYABLE = {429, 500, 502, 503, 504, 529}
MAX_BACKOFF_SECONDS = 30


class TypeSafeError(RuntimeError):
    """The API refused a request, or kept failing after every retry."""


class MissingApiKey(RuntimeError):
    """No API key in the environment variable the config names."""


class CacheMiss(RuntimeError):
    """An offline run needed an answer the cache does not hold."""


def request_key(model: str, state: Any, questions: Mapping[str, Any]) -> str:
    """A hash of everything that decides the answer. Key order does not change it."""
    canonical = json.dumps(
        {"model": model, "state": state, "questions": questions},
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class HttpClient:
    """One POST per request, retried with exponential backoff when the service is busy."""

    def __init__(
        self,
        endpoint: str,
        model: str,
        api_key: str,
        timeout: float = 120.0,
        max_retries: int = 5,
        urlopen: Callable[..., Any] = urllib.request.urlopen,
        sleep: Callable[[float], Any] = time.sleep,
    ) -> None:
        self.endpoint = endpoint
        self.model = model
        self._api_key = api_key
        self.timeout = timeout
        self.max_retries = max_retries
        self._urlopen = urlopen
        self._sleep = sleep

    def ask(self, state: Any, questions: Mapping[str, Any]) -> dict[str, Any]:
        body = json.dumps(
            {"state": state, "model": self.model, "questions": questions}, ensure_ascii=False
        ).encode("utf-8")
        failure = "no attempt was made"
        for attempt in range(self.max_retries + 1):
            request = urllib.request.Request(
                self.endpoint,
                data=body,
                method="POST",
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
            )
            try:
                with self._urlopen(request, timeout=self.timeout) as response:
                    return json.loads(response.read().decode("utf-8"))
            except urllib.error.HTTPError as error:
                detail = error.read().decode("utf-8", errors="replace")
                if error.code not in RETRYABLE:
                    raise TypeSafeError(f"TypeSafe answered {error.code}: {detail}") from error
                failure = f"{error.code}: {detail}"
            except (urllib.error.URLError, TimeoutError) as error:
                failure = str(error)
            if attempt < self.max_retries:
                self._sleep(min(2**attempt, MAX_BACKOFF_SECONDS))
        raise TypeSafeError(
            f"TypeSafe still failing after {self.max_retries + 1} attempts - last: {failure}"
        )


def client_from_config(
    config: dict[str, Any], environ: Mapping[str, str] | None = None
) -> HttpClient:
    settings = config["forecast"]
    environ = os.environ if environ is None else environ
    key = environ.get(settings["api_key_env"], "").strip()
    if not key:
        raise MissingApiKey(
            f"set {settings['api_key_env']} to call TypeSafe, or run with --offline to use "
            "only the cached answers"
        )
    return HttpClient(endpoint=settings["endpoint"], model=settings["model"], api_key=key)


class CachedAnswerer:
    """Answer a batch of requests, from disk where possible and from the API otherwise.

    Each request is `{"state": ..., "questions": ...}`. Each answer comes back in request
    order as `{"model", "answers", "usage", "from_cache"}`.
    """

    def __init__(
        self,
        cache_dir: Path,
        model: str,
        client: HttpClient | None = None,
        offline: bool = False,
        concurrency: int = 8,
    ) -> None:
        self.cache_dir = Path(cache_dir)
        self.model = model
        self.client = client
        self.offline = offline
        self.concurrency = max(1, int(concurrency))
        self.hits = 0
        self.calls = 0

    def _path(self, key: str) -> Path:
        return self.cache_dir / f"{key}.json"

    def _load(self, key: str) -> dict[str, Any] | None:
        path = self._path(key)
        if not path.exists():
            return None
        stored = json.loads(path.read_text(encoding="utf-8"))
        return {**stored, "from_cache": True}

    def _fetch(self, key: str, request: Mapping[str, Any]) -> dict[str, Any]:
        if self.client is None:
            raise TypeSafeError("no client was given, so a cache miss cannot be answered")
        response = self.client.ask(request["state"], request["questions"])
        stored = {
            "key": key,
            "model_requested": self.model,
            "model": response.get("model"),
            "answers": response["answers"],
            "usage": response.get("usage", {}),
        }
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        temporary = self._path(key).with_suffix(".tmp")
        temporary.write_text(json.dumps(stored, indent=1, sort_keys=True) + "\n", encoding="utf-8")
        temporary.replace(self._path(key))
        return {**stored, "from_cache": False}

    def __call__(self, requests: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
        keys = [request_key(self.model, r["state"], r["questions"]) for r in requests]
        results: list[dict[str, Any] | None] = [self._load(key) for key in keys]
        missing = [index for index, result in enumerate(results) if result is None]
        self.hits += len(requests) - len(missing)
        if missing and self.offline:
            raise CacheMiss(
                f"{len(missing)} of {len(requests)} answers are not in {self.cache_dir}; "
                "run once without --offline, with the API key set, to fill the cache"
            )
        if missing:
            # One call per distinct request: the model does not answer twice identically, so
            # a repeat inside the batch takes the first answer rather than a second opinion.
            first = {}
            for index in missing:
                first.setdefault(keys[index], index)
            with ThreadPoolExecutor(max_workers=self.concurrency) as pool:
                fetched = dict(
                    zip(first, pool.map(lambda key: self._fetch(key, requests[first[key]]), first))
                )
            for index in missing:
                results[index] = fetched[keys[index]]
            self.calls += len(first)
        return [result for result in results if result is not None]
