from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass
from typing import Any, Callable, Protocol
from urllib.parse import urlparse
from urllib.request import Request, urlopen


ALLOWED_HOSTS = frozenset({"guide.ff14.co.kr"})
ROBOTS_URL = "https://guide.ff14.co.kr/robots.txt"


class HttpSession(Protocol):
    def get(self, url: str, **kwargs: Any) -> Any:
        ...


@dataclass(frozen=True)
class FetchResult:
    url: str
    status: str
    http_status: int | None = None
    final_url: str | None = None
    body: str | None = None
    encoding: str | None = None
    content_hash: str | None = None
    error: str | None = None


class GuideFetcher:
    def __init__(
        self,
        *,
        session: HttpSession | None = None,
        delay_seconds: float = 1.0,
        timeout_seconds: float = 20.0,
        sleep: Callable[[float], None] = time.sleep,
        allowed_hosts: set[str] | frozenset[str] = ALLOWED_HOSTS,
    ) -> None:
        self.session = session or _UrllibSession()
        self.delay_seconds = delay_seconds
        self.timeout_seconds = timeout_seconds
        self.sleep = sleep
        self.allowed_hosts = frozenset(allowed_hosts)
        self._has_fetched = False

    def fetch(self, url: str) -> FetchResult:
        if not self._is_allowed(url):
            return FetchResult(
                url=url,
                status="error",
                error=f"disallowed host for guide.ff14.co.kr crawler: {url}",
            )

        self._delay_if_needed()
        try:
            response = self.session.get(url, timeout=self.timeout_seconds)
        except Exception as exc:  # noqa: BLE001 - fetcher must contain batch failures.
            self._has_fetched = True
            return FetchResult(url=url, status="error", error=str(exc))

        self._has_fetched = True
        body = str(getattr(response, "text", "") or "")
        http_status = int(getattr(response, "status_code", 0) or 0)
        final_url = str(getattr(response, "url", url) or url)
        encoding = getattr(response, "encoding", None)
        content_hash = _content_hash(body) if body else None
        status = "ok" if 200 <= http_status < 400 else "error"
        error = None if status == "ok" else f"http status {http_status}"
        return FetchResult(
            url=url,
            status=status,
            http_status=http_status,
            final_url=final_url,
            body=body,
            encoding=str(encoding) if encoding else None,
            content_hash=content_hash,
            error=error,
        )

    def fetch_robots(self) -> FetchResult:
        return self.fetch(ROBOTS_URL)

    def _delay_if_needed(self) -> None:
        if self._has_fetched and self.delay_seconds > 0:
            self.sleep(self.delay_seconds)

    def _is_allowed(self, url: str) -> bool:
        parsed = urlparse(url)
        return parsed.scheme == "https" and parsed.netloc in self.allowed_hosts


class _UrllibSession:
    def get(self, url: str, **kwargs: Any) -> Any:
        timeout = float(kwargs.get("timeout") or 20.0)
        request = Request(url, method="GET", headers={"User-Agent": "ffxiv-claw-bot/0.9"})
        with urlopen(request, timeout=timeout) as response:  # nosec B310 - host is guarded by GuideFetcher.
            raw = response.read()
            encoding = response.headers.get_content_charset() or "utf-8"
            return _UrllibResponse(
                status_code=response.status,
                text=raw.decode(encoding, errors="replace"),
                url=response.geturl(),
                encoding=encoding,
                headers=dict(response.headers.items()),
            )


@dataclass(frozen=True)
class _UrllibResponse:
    status_code: int
    text: str
    url: str
    encoding: str
    headers: dict[str, str]


def _content_hash(body: str) -> str:
    return hashlib.sha256(body.encode("utf-8")).hexdigest()
