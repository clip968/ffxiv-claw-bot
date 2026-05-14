from __future__ import annotations

from html.parser import HTMLParser
from urllib.parse import urlparse


IGNORED_TEXT_TAGS = {"script", "style", "nav", "footer", "header", "aside"}


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._ignored_stack: list[str] = []
        self._chunks: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag_name = tag.lower()
        if self._ignored_stack or tag_name in IGNORED_TEXT_TAGS:
            self._ignored_stack.append(tag_name)

    def handle_endtag(self, tag: str) -> None:
        if self._ignored_stack:
            self._ignored_stack.pop()

    def handle_data(self, data: str) -> None:
        if not self._ignored_stack:
            text = data.strip()
            if text:
                self._chunks.append(text)

    def text(self) -> str:
        return "\n".join(self._chunks)


class _TitleExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._in_title = False
        self._chunks: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "title":
            self._in_title = True

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        if self._in_title:
            text = data.strip()
            if text:
                self._chunks.append(text)

    def title(self) -> str | None:
        title = " ".join(self._chunks).strip()
        return title or None


def _optional_beautiful_soup() -> object | None:
    try:
        from bs4 import BeautifulSoup
    except ModuleNotFoundError:
        return None
    return BeautifulSoup


def extract_text_from_html(html: str) -> str:
    beautiful_soup = _optional_beautiful_soup()
    if beautiful_soup is not None:
        soup = beautiful_soup(html, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()
        text = soup.get_text(separator="\n", strip=True)
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        return "\n".join(lines)

    parser = _TextExtractor()
    parser.feed(html)
    parser.close()
    return parser.text()


def extract_title_from_html(html: str, fallback_url: str) -> str:
    beautiful_soup = _optional_beautiful_soup()
    if beautiful_soup is not None:
        soup = beautiful_soup(html, "html.parser")
        if soup.title and soup.title.string:
            title = soup.title.string.strip()
            if title:
                return title
    else:
        parser = _TitleExtractor()
        parser.feed(html)
        parser.close()
        title = parser.title()
        if title:
            return title

    parsed = urlparse(fallback_url)
    return parsed.netloc or fallback_url
