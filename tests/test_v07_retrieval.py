from __future__ import annotations

import dataclasses
import unittest


class V07RetrievalPlannerTests(unittest.TestCase):
    def test_job_change_history_plan_prefers_job_wiki(self) -> None:
        from src.query import parse_query
        from src.retrieval import build_retrieval_plan

        parsed = parse_query("7.x 건브레이커 변경 이력 알려줘")
        plan = build_retrieval_plan(parsed)

        self.assertTrue(dataclasses.is_dataclass(plan))
        self.assertEqual(plan.primary[0].wiki_type, "job")
        self.assertEqual(plan.primary[0].topic, "gunbreaker")
        self.assertIn("gunbreaker", plan.primary[0].query)
        self.assertEqual(plan.limit, 5)

        with self.assertRaises(dataclasses.FrozenInstanceError):
            plan.limit = 10

    def test_generic_search_plan_has_no_topic_filter(self) -> None:
        from src.query import parse_query
        from src.retrieval import build_retrieval_plan

        parsed = parse_query("M4S 공략 찾아줘")
        plan = build_retrieval_plan(parsed, limit=3)

        self.assertEqual(plan.primary[0].wiki_type, None)
        self.assertEqual(plan.primary[0].topic, None)
        self.assertEqual(plan.primary[0].query, parsed.normalized_query)
        self.assertEqual(plan.limit, 3)

    def test_job_change_history_plan_has_source_summary_fallback(self) -> None:
        from src.query import parse_query
        from src.retrieval import build_retrieval_plan

        parsed = parse_query("GNB change history")
        plan = build_retrieval_plan(parsed)

        self.assertEqual(plan.fallback[0].wiki_type, "source_summary")
        self.assertEqual(plan.fallback[0].topic, None)
        self.assertTrue(any(target.wiki_type is None for target in plan.fallback))


if __name__ == "__main__":
    unittest.main()
