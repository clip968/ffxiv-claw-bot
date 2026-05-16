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


if __name__ == "__main__":
    unittest.main()
