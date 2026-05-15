from __future__ import annotations

from http.client import HTTPResponse
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from tools.html_utils import extract_text_from_html, extract_title_from_html

try:
    import requests as _requests
except ModuleNotFoundError:
    _requests = None  # type: ignore[assignment]


DEFAULT_TIMEOUT_SECONDS = 20
SUPPORTED_CONTENT_TYPES = ("text/html", "text/plain", "application/json")


class UrlFetchError(RuntimeError):
    """Raised when a user-provided URL cannot be fetched as text content."""


def fetch_single_url(url: str) -> dict[str, str]:
    headers = {"User-Agent": "ffxiv-claw-bot/0.5"}
    try:
        response = _http_get(url, headers=headers, timeout=DEFAULT_TIMEOUT_SECONDS)
        response.raise_for_status()
    except Exception as exc:  # requests exposes several exception classes.
        raise UrlFetchError(str(exc)) from exc

    content_type = response.headers.get("content-type", "")
    normalized_type = content_type.split(";", 1)[0].strip().lower()
    if not _is_supported_content_type(normalized_type):
        raise UrlFetchError(f"unsupported content-type: {content_type or 'unknown'}")

    raw_body = response.text
    if not raw_body.strip():
        raise UrlFetchError("empty response body")

    if normalized_type == "text/html":
        title = extract_title_from_html(raw_body, url)
        body = extract_text_from_html(raw_body)
    else:
        title = _fallback_title_from_url(url)
        body = raw_body

    if not body.strip():
        raise UrlFetchError("empty extracted body")

    return {
        "url": url,
        "content_type": content_type,
        "title": title,
        "body": body,
    }


def _is_supported_content_type(content_type: str) -> bool:
    return content_type in SUPPORTED_CONTENT_TYPES or content_type.endswith("+json")


def _http_get(url: str, *, headers: dict[str, str], timeout: int) -> object:
    return requests.get(url, headers=headers, timeout=timeout)


class _UrllibResponse:
    def __init__(self, response: HTTPResponse, body: bytes) -> None:
        self._response = response
        self.text = body.decode(response.headers.get_content_charset() or "utf-8")
        self.headers = {"content-type": response.headers.get("content-type", "")}

    def raise_for_status(self) -> None:
        if self._response.status >= 400:
            raise UrlFetchError(f"HTTP {self._response.status}: {self._response.reason}")


def _urllib_get(url: str, *, headers: dict[str, str], timeout: int) -> _UrllibResponse:
    request = Request(url, headers=headers)
    with urlopen(request, timeout=timeout) as response:
        return _UrllibResponse(response, response.read())


class _RequestsCompat:
    def get(self, url: str, *, headers: dict[str, str], timeout: int) -> _UrllibResponse:
        return _urllib_get(url, headers=headers, timeout=timeout)


requests = _requests if _requests is not None else _RequestsCompat()


def _fallback_title_from_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.netloc and parsed.path:
        return f"{parsed.netloc}{parsed.path}"
    if parsed.netloc:
        return parsed.netloc
    return url
