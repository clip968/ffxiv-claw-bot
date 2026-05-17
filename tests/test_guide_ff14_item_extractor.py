from __future__ import annotations

import unittest
from pathlib import Path


FIXTURE = Path(__file__).parent / "fixtures" / "guide_ff14" / "item_detail_gunblade.html"
ITEM_URL = "https://guide.ff14.co.kr/lodestone/db/item/5398978e726"
RAW_PATH = "data/raw/guide_ff14/items/5398978e726.html"


class GuideFF14ItemExtractorTests(unittest.TestCase):
    def test_extracts_official_detail_id_from_url(self) -> None:
        from src.guide_ff14.item_extractor import extract_item_detail

        result = extract_item_detail(FIXTURE.read_text(encoding="utf-8"), url=ITEM_URL, raw_path=RAW_PATH)

        self.assertEqual(result.item.id, "5398978e726")
        self.assertEqual(result.item.url, ITEM_URL)

    def test_extracts_item_name_and_preserves_korean_text(self) -> None:
        from src.guide_ff14.item_extractor import extract_item_detail

        result = extract_item_detail(FIXTURE.read_text(encoding="utf-8"), url=ITEM_URL, raw_path=RAW_PATH)

        self.assertEqual(result.item.name, "영웅의 건블레이드")
        self.assertEqual(result.item.name_ko, "영웅의 건블레이드")
        self.assertIn("한국어 설명", result.item.description)

    def test_extracts_item_and_equip_levels(self) -> None:
        from src.guide_ff14.item_extractor import extract_item_detail

        result = extract_item_detail(FIXTURE.read_text(encoding="utf-8"), url=ITEM_URL, raw_path=RAW_PATH)

        self.assertEqual(result.item.item_level, 700)
        self.assertEqual(result.item.equip_level, 100)

    def test_extracts_job_restrictions_list(self) -> None:
        from src.guide_ff14.item_extractor import extract_item_detail

        result = extract_item_detail(FIXTURE.read_text(encoding="utf-8"), url=ITEM_URL, raw_path=RAW_PATH)

        self.assertEqual(result.item.jobs, ["건브레이커", "Gunbreaker", "GNB"])

    def test_extracts_stats_dict(self) -> None:
        from src.guide_ff14.item_extractor import extract_item_detail

        result = extract_item_detail(FIXTURE.read_text(encoding="utf-8"), url=ITEM_URL, raw_path=RAW_PATH)

        self.assertEqual(result.item.stats, {"힘": 123, "활력": 456})

    def test_missing_optional_fields_do_not_fail_extraction(self) -> None:
        from src.guide_ff14.item_extractor import extract_item_detail

        html = "<main><h1>간단한 아이템</h1></main>"

        result = extract_item_detail(html, url=ITEM_URL, raw_path=RAW_PATH)

        self.assertEqual(result.item.name, "간단한 아이템")
        self.assertIsNone(result.item.item_level)
        self.assertEqual(result.item.jobs, [])
        self.assertIn("item_level", result.missing_optional_fields)

    def test_nav_footer_search_and_script_noise_are_not_in_description_or_source(self) -> None:
        from src.guide_ff14.item_extractor import extract_item_detail

        result = extract_item_detail(FIXTURE.read_text(encoding="utf-8"), url=ITEM_URL, raw_path=RAW_PATH)
        combined = f"{result.item.description}\n{result.item.source}"

        self.assertNotIn("Black Mage", combined)
        self.assertNotIn("검색", combined)
        self.assertNotIn("Footer noise", combined)
        self.assertNotIn("window.evil", combined)

    def test_output_includes_content_hash_and_raw_path(self) -> None:
        from src.guide_ff14.item_extractor import extract_item_detail

        result = extract_item_detail(FIXTURE.read_text(encoding="utf-8"), url=ITEM_URL, raw_path=RAW_PATH)

        self.assertEqual(len(result.item.content_hash), 64)
        self.assertEqual(result.item.raw_path, RAW_PATH)


if __name__ == "__main__":
    unittest.main()
