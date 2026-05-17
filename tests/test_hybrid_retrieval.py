from __future__ import annotations

import sqlite3
import unittest

from src.retrieval.models import SearchResult


class HybridRetrievalTests(unittest.TestCase):
    def setUp(self) -> None:
        self.entity_index = {
            "건브": "job:gunbreaker",
            "gunbreaker": "job:gunbreaker",
            "7.5": "patch:7_5",
            "patch 7.5": "patch:7_5",
        }
        self.conn = sqlite3.connect(":memory:")
        self._seed_graph()

    def tearDown(self) -> None:
        self.conn.close()

    def _seed_graph(self) -> None:
        from src.domain_graph.storage import ensure_graph_schema, upsert_edge, upsert_node

        ensure_graph_schema(self.conn)
        upsert_node(
            self.conn,
            {
                "id": "src:local_v08",
                "type": "SourceDocument",
                "name": "local_v08",
                "properties": {"title": "Patch 7.5 Fixture", "path": "wiki/source_summaries/local_v08.md"},
            },
        )
        upsert_node(self.conn, {"id": "job:gunbreaker", "type": "Job", "name": "Gunbreaker"})
        upsert_node(self.conn, {"id": "patch:7_5", "type": "Patch", "name": "Patch 7.5"})
        upsert_node(
            self.conn,
            {
                "id": "fact:no_mercy_7_5",
                "type": "Fact",
                "name": "No Mercy duration was changed.",
                "properties": {"text": "No Mercy duration was changed."},
            },
        )
        for source, relation, target in (
            ("src:local_v08", "MENTIONS", "job:gunbreaker"),
            ("src:local_v08", "MENTIONS", "patch:7_5"),
            ("src:local_v08", "SUPPORTS", "fact:no_mercy_7_5"),
            ("fact:no_mercy_7_5", "AFFECTS_JOB", "job:gunbreaker"),
            ("fact:no_mercy_7_5", "VALID_IN_PATCH", "patch:7_5"),
        ):
            upsert_edge(
                self.conn,
                {
                    "source_node_id": source,
                    "relation_type": relation,
                    "target_node_id": target,
                    "source_id": "local_v08",
                    "confidence": 0.9,
                },
            )

    def test_entity_match_korean_query(self) -> None:
        from src.retrieval.hybrid import match_query_entities

        matches = match_query_entities("건브 7.5 변경점 알려줘", self.entity_index)

        self.assertEqual(matches, ("job:gunbreaker", "patch:7_5"))

    def test_graph_neighborhood_returns_facts(self) -> None:
        from src.retrieval.hybrid import retrieve_graph_neighborhood

        results = retrieve_graph_neighborhood(self.conn, ("job:gunbreaker", "patch:7_5"))

        self.assertTrue(any(result.node_id == "fact:no_mercy_7_5" for result in results))
        self.assertTrue(any(result.source_id == "local_v08" for result in results))

    def test_merge_fts_and_graph(self) -> None:
        from src.retrieval.hybrid import GraphRetrievalResult, merge_retrieval_results

        merged = merge_retrieval_results(
            [_fts("wiki_fts", source_id="fts_source")],
            [
                GraphRetrievalResult(
                    page_id="wiki_local_v08",
                    title="Patch 7.5 Fixture",
                    wiki_type="source_summary",
                    path="wiki/source_summaries/local_v08.md",
                    snippet="No Mercy duration was changed.",
                    source_id="local_v08",
                    node_id="fact:no_mercy_7_5",
                    score=1.4,
                )
            ],
        )

        self.assertEqual({result.page_id for result in merged}, {"wiki_fts", "wiki_local_v08"})

    def test_dedup_sources(self) -> None:
        from src.retrieval.hybrid import GraphRetrievalResult, merge_retrieval_results

        merged = merge_retrieval_results(
            [_fts("wiki_local_v08", source_id="local_v08")],
            [
                GraphRetrievalResult(
                    page_id="wiki_local_v08",
                    title="Patch 7.5 Fixture",
                    wiki_type="source_summary",
                    path="wiki/source_summaries/local_v08.md",
                    snippet="No Mercy duration was changed.",
                    source_id="local_v08",
                    node_id="fact:no_mercy_7_5",
                    score=1.4,
                )
            ],
        )

        self.assertEqual([result.page_id for result in merged], ["wiki_local_v08"])

    def test_fts_only_fallback(self) -> None:
        from src.retrieval.hybrid import merge_retrieval_results

        merged = merge_retrieval_results([_fts("wiki_fts")], [])

        self.assertEqual([result.page_id for result in merged], ["wiki_fts"])

    def test_graph_only_context(self) -> None:
        from src.retrieval.hybrid import build_answer_context, retrieve_graph_neighborhood

        graph_results = retrieve_graph_neighborhood(self.conn, ("job:gunbreaker",))
        contexts = build_answer_context(graph_results)

        self.assertTrue(contexts)
        self.assertEqual(contexts[0]["source_id"], "local_v08")


def _fts(page_id: str, *, source_id: str = "source") -> SearchResult:
    return SearchResult(
        page_id=page_id,
        title=page_id,
        wiki_type="source_summary",
        path=f"wiki/source_summaries/{source_id}.md",
        score=0.2,
        snippet=f"source_id: {source_id}\nGunbreaker changed.",
        topic=None,
    )


if __name__ == "__main__":
    unittest.main()
