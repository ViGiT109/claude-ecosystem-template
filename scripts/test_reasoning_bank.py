#!/usr/bin/env python3
"""Regression harness for `scripts/reasoning_bank.py` retrieval.

Runs a fixed query set across modes and asserts:
- sparse mode runs without ChromaDB installed,
- exact-token query surfaces the lesson named in the corpus,
- paraphrase query still surfaces the same lesson (Top-K),
- multilingual query does not crash the tokenizer.

Designed to be cheap (no embeddings) and CI-friendly. Exits non-zero on failure.
Run from repo root: `python scripts/test_reasoning_bank.py`.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import reasoning_bank as rb  # noqa: E402


EXACT_TOKEN_QUERY = "audit_history"
PARAPHRASE_QUERY = "when did we last audit the ecosystem"
MULTILINGUAL_QUERY = "аудит экосистемы"
EXPECTED_TOP_HIT_TITLE_SUBSTR = "freshness"   # lesson-003 title contains "freshness"


def _assert(cond: bool, msg: str) -> None:
    if not cond:
        print(f"❌ FAIL: {msg}", file=sys.stderr)
        sys.exit(1)
    print(f"✅ PASS: {msg}")


def main() -> None:
    print("=" * 60)
    print("ReasoningBank retrieval harness")
    print("=" * 60)

    # 1. Sparse: exact-token query must surface the expected lesson at rank 1.
    sparse_exact = rb.retrieve(
        EXACT_TOKEN_QUERY,
        top_k=5,
        mode="sparse",
        collection_name=rb.COLLECTION_LESSONS,
    )
    _assert(len(sparse_exact) >= 1, "sparse exact-token: returned >=1 result")
    top_title = sparse_exact[0]["metadata"].get("title", "")
    _assert(
        EXPECTED_TOP_HIT_TITLE_SUBSTR.lower() in top_title.lower(),
        f"sparse exact-token: rank-1 title contains {EXPECTED_TOP_HIT_TITLE_SUBSTR!r} (got {top_title!r})",
    )

    # 2. Sparse: paraphrase must still surface the same lesson in top-K.
    sparse_para = rb.retrieve(
        PARAPHRASE_QUERY,
        top_k=5,
        mode="sparse",
        collection_name=rb.COLLECTION_LESSONS,
    )
    titles = [item["metadata"].get("title", "") for item in sparse_para]
    _assert(
        any(EXPECTED_TOP_HIT_TITLE_SUBSTR.lower() in t.lower() for t in titles),
        f"sparse paraphrase: expected lesson in top-{len(titles)} (titles={titles})",
    )

    # 3. Sparse: multilingual query must not crash; zero hits is acceptable.
    sparse_multi = rb.retrieve(
        MULTILINGUAL_QUERY,
        top_k=5,
        mode="sparse",
        collection_name=rb.COLLECTION_LESSONS,
    )
    _assert(
        isinstance(sparse_multi, list),
        f"sparse multilingual: tokenizer survives Cyrillic query (hits={len(sparse_multi)})",
    )

    # 4. Hybrid without chromadb must degrade to sparse rather than crash.
    if not rb._chromadb_available():
        hybrid_exact = rb.retrieve(
            EXACT_TOKEN_QUERY,
            top_k=5,
            mode="hybrid",
            collection_name=rb.COLLECTION_LESSONS,
        )
        _assert(
            len(hybrid_exact) >= 1,
            "hybrid without chromadb: gracefully degrades to sparse",
        )
    else:
        print("ℹ️  chromadb is available — hybrid full-path tested implicitly elsewhere")

    print("\n✅ All retrieval-harness checks passed.")


if __name__ == "__main__":
    main()
