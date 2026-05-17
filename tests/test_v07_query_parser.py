from __future__ import annotations

import dataclasses
import unittest


class V07QueryModelTests(unittest.TestCase):
    def test_parsed_query_preserves_raw_and_normalized_query(self) -> None:
        from src.query import ParsedQuery

        parsed = ParsedQuery(
            raw_query="  GNB 7.x 변경 이력  ",
            normalized_query="gnb 7.x 변경 이력",
            intent=None,
            job=None,
            patch_range=None,
            topic=None,
            terms=("gnb", "7.x", "변경", "이력"),
        )

        self.assertTrue(dataclasses.is_dataclass(parsed))
        self.assertEqual(parsed.raw_query, "  GNB 7.x 변경 이력  ")
        self.assertEqual(parsed.normalized_query, "gnb 7.x 변경 이력")
        self.assertEqual(parsed.terms, ("gnb", "7.x", "변경", "이력"))

        with self.assertRaises(dataclasses.FrozenInstanceError):
            parsed.job = "gunbreaker"

    def test_normalize_query_casefolds_english_but_preserves_korean(self) -> None:
        from src.query import normalize_query

        normalized = normalize_query("  GNB   7.X   건브레이커 변경 이력  ")

        self.assertEqual(normalized, "gnb 7.x 건브레이커 변경 이력")
        self.assertEqual(normalize_query("   "), "")

    def test_tokenize_query_extracts_terms(self) -> None:
        from src.query import extract_terms

        terms = extract_terms("  GNB 7.x: 건브레이커 변경 이력 알려줘!  ")

        self.assertEqual(terms, ("gnb", "7.x", "건브레이커", "변경", "이력", "알려줘"))
        self.assertEqual(extract_terms("   "), ())


class V07JobDetectorTests(unittest.TestCase):
    def test_detect_job_korean_full_alias(self) -> None:
        from src.query import detect_job

        self.assertEqual(detect_job("건브레이커 변경 이력"), "gunbreaker")

    def test_detect_job_korean_short_alias(self) -> None:
        from src.query import detect_job

        self.assertEqual(detect_job("건브 뭐 바뀜?"), "gunbreaker")

    def test_detect_job_abbreviation_alias(self) -> None:
        from src.query import detect_job

        self.assertEqual(detect_job("GNB patch history"), "gunbreaker")

    def test_detect_job_english_name(self) -> None:
        from src.query import detect_job

        self.assertEqual(detect_job("Black Mage changes"), "black_mage")

    def test_detect_no_job_returns_none(self) -> None:
        from src.query import detect_job

        self.assertIsNone(detect_job("패치노트 요약"))


class V07PatchRangeParserTests(unittest.TestCase):
    def test_parse_single_patch(self) -> None:
        from src.query import parse_patch_range

        self.assertEqual(parse_patch_range("7.2 패치"), "7.2..7.2")

    def test_parse_x_patch_range(self) -> None:
        from src.query import parse_patch_range

        self.assertEqual(parse_patch_range("7.x 변경점"), "7.0..7.99")

    def test_parse_tilde_patch_range(self) -> None:
        from src.query import parse_patch_range

        self.assertEqual(parse_patch_range("7.0~7.5 변경 이력"), "7.0..7.5")

    def test_parse_dash_patch_range(self) -> None:
        from src.query import parse_patch_range

        self.assertEqual(parse_patch_range("7.0-7.5 변경 이력"), "7.0..7.5")

    def test_parse_korean_range(self) -> None:
        from src.query import parse_patch_range

        self.assertEqual(parse_patch_range("7.0부터 7.5까지"), "7.0..7.5")

    def test_parse_no_patch_returns_none(self) -> None:
        from src.query import parse_patch_range

        self.assertIsNone(parse_patch_range("건브레이커 변경 이력"))


class V07IntentDetectorTests(unittest.TestCase):
    def test_detect_job_change_history_intent_with_change_history(self) -> None:
        from src.query import detect_intent

        self.assertEqual(
            detect_intent("건브레이커 변경 이력", job="gunbreaker"),
            "job_change_history",
        )

    def test_detect_job_change_history_intent_with_what_changed(self) -> None:
        from src.query import detect_intent

        self.assertEqual(
            detect_intent("흑마 뭐 바뀜?", job="black_mage"),
            "job_change_history",
        )

    def test_detect_generic_search_without_job(self) -> None:
        from src.query import detect_intent

        self.assertEqual(detect_intent("M4S 공략 찾아줘", job=None), "generic_search")


class V07QueryParserIntegrationTests(unittest.TestCase):
    def test_parse_query_job_change_history(self) -> None:
        from src.query import parse_query

        parsed = parse_query("7.x 건브레이커 변경 이력 알려줘")

        self.assertEqual(parsed.raw_query, "7.x 건브레이커 변경 이력 알려줘")
        self.assertEqual(parsed.normalized_query, "7.x 건브레이커 변경 이력 알려줘")
        self.assertEqual(parsed.intent, "job_change_history")
        self.assertEqual(parsed.job, "gunbreaker")
        self.assertEqual(parsed.patch_range, "7.0..7.99")
        self.assertEqual(parsed.topic, "job")
        self.assertEqual(
            parsed.terms,
            ("7.x", "건브레이커", "변경", "이력", "알려줘"),
        )

    def test_parse_query_generic_search(self) -> None:
        from src.query import parse_query

        parsed = parse_query("M4S 공략 찾아줘")

        self.assertEqual(parsed.intent, "generic_search")
        self.assertIsNone(parsed.job)
        self.assertIsNone(parsed.patch_range)
        self.assertIsNone(parsed.topic)


if __name__ == "__main__":
    unittest.main()
