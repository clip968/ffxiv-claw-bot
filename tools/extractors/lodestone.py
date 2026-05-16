from __future__ import annotations

from html.parser import HTMLParser
from typing import Any
from urllib.parse import urlparse

from tools.html_utils import extract_title_from_html


OFFICIAL_LODESTONE_HOSTS = {
    "na.finalfantasyxiv.com",
    "eu.finalfantasyxiv.com",
    "jp.finalfantasyxiv.com",
    "de.finalfantasyxiv.com",
    "fr.finalfantasyxiv.com",
}

IGNORED_TAGS = {"script", "style", "nav", "footer", "header", "aside"}
IGNORED_CLASS_TOKENS = {
    "news__detail__share",
    "share",
    "social",
    "sns",
}


class LodestoneExtractionError(RuntimeError):
    """Raised when Lodestone article content cannot be extracted."""


def is_lodestone_url(url: str) -> bool:
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    path = parsed.path or ""
    return host in OFFICIAL_LODESTONE_HOSTS and path.startswith("/lodestone/")


def extract_lodestone_article(html: str, url: str) -> dict[str, str]:
    if not html.strip():
        raise LodestoneExtractionError("empty Lodestone HTML")

    beautiful_soup = _optional_beautiful_soup()
    if beautiful_soup is not None:
        title, body = _extract_with_beautiful_soup(html, url, beautiful_soup)
    else:
        title, body = _extract_with_html_parser(html, url)

    if not body.strip():
        raise LodestoneExtractionError("empty Lodestone article body")

    return {
        "title": title,
        "body": body,
        "extractor": "lodestone",
    }


def _optional_beautiful_soup() -> Any | None:
    try:
        from bs4 import BeautifulSoup
    except ModuleNotFoundError:
        return None
    return BeautifulSoup


def _extract_with_beautiful_soup(
    html: str,
    url: str,
    beautiful_soup: Any,
) -> tuple[str, str]:
    soup = beautiful_soup(html, "html.parser")
    wrapper = soup.select_one(".news__detail__wrapper")
    if wrapper is None:
        raise LodestoneExtractionError("missing Lodestone .news__detail__wrapper")

    for tag in wrapper(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()
    for tag in wrapper.select(".news__detail__share, .share, .social, .sns"):
        tag.decompose()

    title = _extract_title_from_wrapper(wrapper) or extract_title_from_html(html, url)
    body = _normalize_text(wrapper.get_text(separator="\n", strip=True))
    if not body:
        raise LodestoneExtractionError("empty Lodestone article body")
    return title, body


def _extract_title_from_wrapper(wrapper: Any) -> str | None:
    for selector in (".news__detail__title", "h1", "h2"):
        node = wrapper.select_one(selector)
        if node is None:
            continue
        title = _normalize_text(node.get_text(separator=" ", strip=True))
        if title:
            return title
    return None


class _LodestoneArticleParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.wrapper_seen = False
        self._wrapper_depth = 0
        self._ignored_depth = 0
        self._heading_depth = 0
        self._chunks: list[str] = []
        self._title_chunks: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag_name = tag.lower()
        classes = _class_tokens(attrs)

        if self._wrapper_depth == 0 and "news__detail__wrapper" in classes:
            self.wrapper_seen = True
            self._wrapper_depth = 1
            if tag_name in {"h1", "h2"}:
                self._heading_depth = 1
            return

        if self._wrapper_depth == 0:
            return

        self._wrapper_depth += 1
        if self._ignored_depth > 0 or tag_name in IGNORED_TAGS or _has_ignored_class(classes):
            self._ignored_depth += 1
        elif tag_name in {"h1", "h2"}:
            self._heading_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if self._wrapper_depth == 0:
            return
        if self._ignored_depth > 0:
            self._ignored_depth -= 1
        elif self._heading_depth > 0 and tag.lower() in {"h1", "h2"}:
            self._heading_depth -= 1

        self._wrapper_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._wrapper_depth == 0 or self._ignored_depth > 0:
            return
        text = data.strip()
        if not text:
            return
        self._chunks.append(text)
        if self._heading_depth > 0 and not self._title_chunks:
            self._title_chunks.append(text)

    def title(self) -> str | None:
        title = _normalize_text(" ".join(self._title_chunks))
        return title or None

    def body(self) -> str:
        return _normalize_text("\n".join(self._chunks))


def _extract_with_html_parser(html: str, url: str) -> tuple[str, str]:
    parser = _LodestoneArticleParser()
    parser.feed(html)
    parser.close()
    if not parser.wrapper_seen:
        raise LodestoneExtractionError("missing Lodestone .news__detail__wrapper")

    title = parser.title() or extract_title_from_html(html, url)
    body = parser.body()
    if not body:
        raise LodestoneExtractionError("empty Lodestone article body")
    return title, body


def _class_tokens(attrs: list[tuple[str, str | None]]) -> set[str]:
    for name, value in attrs:
        if name.lower() == "class" and value:
            return {part.strip().lower() for part in value.split() if part.strip()}
    return set()


def _has_ignored_class(classes: set[str]) -> bool:
    return any(
        token in IGNORED_CLASS_TOKENS or "share" in token
        for token in classes
    )


def _normalize_text(text: str) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return "\n".join(lines)
