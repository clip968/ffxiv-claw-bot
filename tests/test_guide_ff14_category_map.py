from __future__ import annotations

import unittest
from pathlib import Path


FIXTURE = Path(__file__).parent / "fixtures" / "guide_ff14" / "category_map_item_nav.html"


class GuideFF14CategoryMapTests(unittest.TestCase):
    def test_fn_open_left_menu_urls_are_normalized_to_absolute_guide_urls(self) -> None:
        from src.guide_ff14.category_map import parse_category_map

        categories = parse_category_map(FIXTURE.read_text(encoding="utf-8"))

        self.assertIn(
            "https://guide.ff14.co.kr/lodestone/db/item",
            [category.url for category in categories],
        )
        self.assertTrue(all(category.url.startswith("https://guide.ff14.co.kr/") for category in categories))

    def test_top_level_db_roots_are_recognized(self) -> None:
        from src.guide_ff14.category_map import parse_category_map

        categories = parse_category_map(FIXTURE.read_text(encoding="utf-8"))

        self.assertEqual(
            [category.db_type for category in categories[:8]],
            [
                "item",
                "quest",
                "duty",
                "achievement",
                "recipe",
                "gathering",
                "shop",
                "text_command",
            ],
        )

    def test_gunbreaker_weapon_category_is_extracted_with_stable_id(self) -> None:
        from src.guide_ff14.category_map import parse_category_map

        categories = parse_category_map(FIXTURE.read_text(encoding="utf-8"))
        gunblade = next(category for category in categories if category.category3 == "110")

        self.assertEqual(gunblade.id, "guide:item:1:110")
        self.assertEqual(gunblade.db_type, "item")
        self.assertEqual(gunblade.category2, "1")
        self.assertEqual(gunblade.category3, "110")

    def test_javascript_pseudo_urls_are_excluded(self) -> None:
        from src.guide_ff14.category_map import parse_category_map

        categories = parse_category_map(FIXTURE.read_text(encoding="utf-8"))

        self.assertFalse(any("javascript:" in category.url for category in categories))
        self.assertFalse(any(category.label == "열기" for category in categories))

    def test_query_params_are_split_into_category_fields_and_filters(self) -> None:
        from src.guide_ff14.category_map import parse_category_map

        categories = parse_category_map(FIXTURE.read_text(encoding="utf-8"))
        gunblade = next(category for category in categories if category.category3 == "110")

        self.assertEqual(gunblade.category2, "1")
        self.assertEqual(gunblade.category3, "110")
        self.assertEqual(
            gunblade.filters,
            {"max_item_lv": "700", "min_item_lv": "650"},
        )

    def test_korean_labels_are_preserved(self) -> None:
        from src.guide_ff14.category_map import parse_category_map

        categories = parse_category_map(FIXTURE.read_text(encoding="utf-8"))
        labels = [category.label for category in categories]

        self.assertIn("아이템", labels)
        self.assertIn("건블레이드", labels)


if __name__ == "__main__":
    unittest.main()
