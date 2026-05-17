from __future__ import annotations

import unittest


class FakeResponse:
    def __init__(
        self,
        *,
        status_code: int = 200,
        text: str = "",
        url: str = "https://guide.ff14.co.kr/lodestone/db/item",
        encoding: str | None = "utf-8",
        headers: dict[str, str] | None = None,
    ) -> None:
        self.status_code = status_code
        self.text = text
        self.url = url
        self.encoding = encoding
        self.headers = headers or {"content-type": "text/html; charset=utf-8"}


class FakeSession:
    def __init__(self) -> None:
        self.get_calls: list[tuple[str, dict[str, object]]] = []
        self.head_calls: list[str] = []
        self.responses: list[object] = []

    def get(self, url: str, **kwargs: object) -> object:
        self.get_calls.append((url, kwargs))
        response = self.responses.pop(0)
        if isinstance(response, BaseException):
            raise response
        return response

    def head(self, url: str, **kwargs: object) -> object:
        self.head_calls.append(url)
        raise AssertionError("fetcher must not use HEAD")


class GuideFF14FetcherTests(unittest.TestCase):
    def test_disallowed_host_is_rejected_before_http(self) -> None:
        from src.guide_ff14.fetcher import GuideFetcher

        session = FakeSession()
        fetcher = GuideFetcher(session=session, delay_seconds=0)

        result = fetcher.fetch("https://example.com/lodestone/db/item")

        self.assertEqual(result.status, "error")
        self.assertIn("disallowed host", result.error)
        self.assertEqual(session.get_calls, [])

    def test_fetch_uses_get_not_head_and_passes_timeout(self) -> None:
        from src.guide_ff14.fetcher import GuideFetcher

        session = FakeSession()
        session.responses.append(FakeResponse(text="<html>ok</html>"))
        fetcher = GuideFetcher(session=session, delay_seconds=0, timeout_seconds=7)

        result = fetcher.fetch("https://guide.ff14.co.kr/lodestone/db/item")

        self.assertEqual(result.status, "ok")
        self.assertEqual(len(session.get_calls), 1)
        self.assertEqual(session.get_calls[0][1]["timeout"], 7)
        self.assertEqual(session.head_calls, [])

    def test_successful_html_response_returns_body_hash_and_encoding(self) -> None:
        from src.guide_ff14.fetcher import GuideFetcher

        session = FakeSession()
        session.responses.append(FakeResponse(text="<html>가이드</html>", encoding="utf-8"))
        fetcher = GuideFetcher(session=session, delay_seconds=0)

        result = fetcher.fetch("https://guide.ff14.co.kr/lodestone/db/item")

        self.assertEqual(result.http_status, 200)
        self.assertEqual(result.body, "<html>가이드</html>")
        self.assertEqual(result.encoding, "utf-8")
        self.assertEqual(len(result.content_hash), 64)

    def test_get_exception_returns_structured_error(self) -> None:
        from src.guide_ff14.fetcher import GuideFetcher

        session = FakeSession()
        session.responses.append(ConnectionResetError("connection reset"))
        fetcher = GuideFetcher(session=session, delay_seconds=0)

        result = fetcher.fetch("https://guide.ff14.co.kr/lodestone/db/item")

        self.assertEqual(result.status, "error")
        self.assertIn("connection reset", result.error)

    def test_robots_snapshot_uses_get_and_returns_text_status_metadata(self) -> None:
        from src.guide_ff14.fetcher import GuideFetcher

        session = FakeSession()
        session.responses.append(
            FakeResponse(
                status_code=200,
                text="User-agent: Bingbot\nDisallow: /lodestone/search",
                url="https://guide.ff14.co.kr/robots.txt",
                headers={"content-type": "text/plain"},
            )
        )
        fetcher = GuideFetcher(session=session, delay_seconds=0)

        result = fetcher.fetch_robots()

        self.assertEqual(result.url, "https://guide.ff14.co.kr/robots.txt")
        self.assertEqual(result.http_status, 200)
        self.assertIn("Bingbot", result.body)
        self.assertEqual(len(session.get_calls), 1)
        self.assertEqual(session.head_calls, [])

    def test_delay_is_injectable_and_can_be_disabled_in_tests(self) -> None:
        from src.guide_ff14.fetcher import GuideFetcher

        sleep_calls: list[float] = []
        session = FakeSession()
        session.responses.append(FakeResponse(text="one"))
        session.responses.append(FakeResponse(text="two"))
        fetcher = GuideFetcher(
            session=session,
            delay_seconds=0.25,
            sleep=sleep_calls.append,
        )

        fetcher.fetch("https://guide.ff14.co.kr/lodestone/db/item")
        fetcher.fetch("https://guide.ff14.co.kr/lodestone/db/item?category2=1")

        self.assertEqual(sleep_calls, [0.25])


if __name__ == "__main__":
    unittest.main()
