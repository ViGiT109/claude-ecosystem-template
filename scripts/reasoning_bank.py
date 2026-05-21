#!/usr/bin/env python3
"""
ReasoningBank Semantic Memory — Phase 2.

ChromaDB-backed semantic retrieval for project agent memory.
Uses all-mpnet-base-v2 for embeddings (768-dim, best quality).
Custom fine-tuned model is used if it exists at .memory/models/project-mpnet/.

Usage:
    python scripts/reasoning_bank.py ingest_lessons
    python scripts/reasoning_bank.py ingest_trajectories
    python scripts/reasoning_bank.py ingest_all
    python scripts/reasoning_bank.py retrieve "query" [--top-k 5] [--mode hybrid|dense|sparse] [--rrf-k 60]
    python scripts/reasoning_bank.py stats

Retrieve modes (default: hybrid):
    dense   — ChromaDB embedding search.
    sparse  — BM25 only; works without ChromaDB installed.
    hybrid  — Reciprocal Rank Fusion of dense + sparse. Degrades to sparse if ChromaDB absent.
"""

from __future__ import annotations

import json
import re
import sys
from functools import lru_cache
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
DB_PATH = Path(".memory/chroma_db")
LESSONS_FILE = Path(".memory/lessons.md")
TRAJECTORIES_FILE = Path(".memory/session_trajectories.jsonl")
RETRIEVAL_LOGS_FILE = Path(".memory/retrieval_logs.jsonl")
CUSTOM_MODEL_PATH = Path(".memory/models/project-mpnet")
MODEL_NAME = "all-mpnet-base-v2"

COLLECTION_LESSONS = "lessons"
COLLECTION_TRAJECTORIES = "trajectories"

DEFAULT_MODE = "hybrid"
DEFAULT_RRF_K = 60
VALID_MODES = ("dense", "sparse", "hybrid")


# ---------------------------------------------------------------------------
# Lazy imports (heavy deps, only when needed)
# ---------------------------------------------------------------------------
def _chromadb_available() -> bool:
    """Probe-only check; never imports the package transitively."""
    try:
        import chromadb  # noqa: F401
        return True
    except ModuleNotFoundError:
        return False


def _bm25_available() -> bool:
    try:
        from rank_bm25 import BM25Okapi  # noqa: F401
        return True
    except ModuleNotFoundError:
        return False


def _get_client():  # noqa: ANN201
    """Initialize ChromaDB persistent client. Hard-fails if chromadb missing."""
    try:
        import chromadb
    except ModuleNotFoundError:
        print(
            "❌ Error: 'chromadb' not installed. "
            "Install ReasoningBank extras: pip install '.[reasoning]'",
            file=sys.stderr,
        )
        sys.exit(1)

    DB_PATH.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=str(DB_PATH))


def _get_embedding_fn():  # noqa: ANN201
    """Initialize sentence-transformers embedding function."""
    from chromadb.utils import embedding_functions

    model_name_or_path = str(CUSTOM_MODEL_PATH) if CUSTOM_MODEL_PATH.exists() else MODEL_NAME
    return embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=model_name_or_path,
    )


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------
def parse_lessons(filepath: Path = LESSONS_FILE) -> list[dict[str, str]]:
    """Parse lessons.md into structured Memory Items.

    Expected format per lesson:
        ### Memory Item: {display_title}
        **Title:** {title}
        **Description:** {description}
        **Content:** {content}
        **Source:** {source}

    Returns list of dicts with keys: id, title, description, content, source, document.
    """
    text = filepath.read_text(encoding="utf-8")
    pattern = re.compile(
        r"### Memory Item:\s*(.+?)\n"
        r"\*\*Title:\*\*\s*(.+?)\n"
        r"\*\*Description:\*\*\s*(.+?)\n"
        r"\*\*Content:\*\*\s*(.+?)\n"
        r"\*\*Source:\*\*\s*(.+?)(?:\n|$)",
        re.DOTALL,
    )

    lessons = []
    for i, match in enumerate(pattern.finditer(text), start=1):
        display_title, title, description, content, source = (
            m.strip() for m in match.groups()
        )
        lessons.append({
            "id": f"lesson-{i:03d}",
            "title": title,
            "description": description,
            "content": content,
            "source": source,
            "document": f"{title}\n{description}\n{content}",
        })

    return lessons


def parse_trajectories(filepath: Path = TRAJECTORIES_FILE) -> list[dict[str, str]]:
    """Parse session_trajectories.jsonl into embeddable records."""
    if not filepath.exists():
        return []

    trajectories = []
    for i, line in enumerate(filepath.read_text(encoding="utf-8").splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue

        commit_msg = record.get("commit_msg", "")
        outcome = record.get("outcome", "unknown")
        task_completion = record.get("task_completion", "N/A")
        document = f"{commit_msg} | outcome: {outcome} | tasks: {task_completion}"

        trajectories.append({
            "id": f"trajectory-{i:03d}",
            "document": document,
            "date": record.get("date", ""),
            "outcome": outcome,
            "commit_msg": commit_msg,
        })

    return trajectories


# ---------------------------------------------------------------------------
# Core Operations
# ---------------------------------------------------------------------------
def ingest_lessons() -> int:
    """Parse lessons.md and upsert into ChromaDB. Returns number of lessons ingested."""
    client = _get_client()
    embedding_fn = _get_embedding_fn()
    collection = client.get_or_create_collection(
        name=COLLECTION_LESSONS,
        embedding_function=embedding_fn,
    )

    lessons = parse_lessons()
    if not lessons:
        print("⚠️  No lessons found in", LESSONS_FILE)
        return 0

    collection.upsert(
        ids=[lesson["id"] for lesson in lessons],
        documents=[lesson["document"] for lesson in lessons],
        metadatas=[
            {"title": lesson["title"], "source": lesson["source"], "description": lesson["description"]}
            for lesson in lessons
        ],
    )

    count = collection.count()
    print(f"✅ Ingested {len(lessons)} lessons → collection '{COLLECTION_LESSONS}' (total: {count})")
    return count


def ingest_trajectories() -> int:
    """Parse session_trajectories.jsonl and upsert into ChromaDB."""
    client = _get_client()
    embedding_fn = _get_embedding_fn()
    collection = client.get_or_create_collection(
        name=COLLECTION_TRAJECTORIES,
        embedding_function=embedding_fn,
    )

    trajectories = parse_trajectories()
    if not trajectories:
        print("⚠️  No trajectories found in", TRAJECTORIES_FILE)
        return 0

    collection.upsert(
        ids=[t["id"] for t in trajectories],
        documents=[t["document"] for t in trajectories],
        metadatas=[
            {"date": t["date"], "outcome": t["outcome"], "commit_msg": t["commit_msg"]}
            for t in trajectories
        ],
    )

    count = collection.count()
    print(f"✅ Ingested {len(trajectories)} trajectories → collection '{COLLECTION_TRAJECTORIES}' (total: {count})")
    return count


def _tokenize(text: str) -> list[str]:
    """Cheap, Unicode-aware tokenization for BM25 (lowercased word characters)."""
    return re.findall(r"\w+", text.lower(), flags=re.UNICODE)


def _item_metadata(item: dict) -> dict:
    """Project a parsed lessons/trajectory item to chromadb-style metadata."""
    keys = ("title", "description", "source", "date", "outcome", "commit_msg")
    return {k: item[k] for k in keys if k in item}


@lru_cache(maxsize=4)
def _build_bm25_index(corpus_path: str, _mtime_ns: int, kind: str):  # noqa: ANN202
    """Build a BM25Okapi index over the parsed corpus.

    Cache is keyed on (path, mtime_ns) so edits invalidate it transparently.
    `_mtime_ns` is part of the cache key only; the function re-reads from `corpus_path`.
    """
    from rank_bm25 import BM25Okapi

    path = Path(corpus_path)
    if kind == "lessons":
        items = parse_lessons(path)
    elif kind == "trajectories":
        items = parse_trajectories(path)
    else:
        items = []

    if not items:
        return None, []

    tokenized = [_tokenize(item["document"]) for item in items]
    return BM25Okapi(tokenized), items


def _bm25_retrieve(
    query: str,
    *,
    top_k: int,
    collection_name: str,
) -> list[dict]:
    """Sparse BM25 retrieval. Does NOT import chromadb."""
    if not _bm25_available():
        print(
            "❌ Error: 'rank-bm25' not installed. "
            "Install ReasoningBank extras: pip install '.[reasoning]'",
            file=sys.stderr,
        )
        sys.exit(1)

    if collection_name == COLLECTION_LESSONS:
        path, kind = LESSONS_FILE, "lessons"
    elif collection_name == COLLECTION_TRAJECTORIES:
        path, kind = TRAJECTORIES_FILE, "trajectories"
    else:
        return []

    if not path.exists():
        return []

    bm25, items = _build_bm25_index(str(path), path.stat().st_mtime_ns, kind)
    if bm25 is None or not items:
        return []

    tokens = _tokenize(query)
    if not tokens:
        return []

    scores = bm25.get_scores(tokens)
    ranked = sorted(zip(items, scores), key=lambda pair: pair[1], reverse=True)

    results = []
    for item, score in ranked[:top_k]:
        if score <= 0:
            continue
        results.append({
            "id": item["id"],
            "document": item["document"],
            "metadata": _item_metadata(item),
            # BM25 higher = better; mirror into negative distance for parity with dense.
            "distance": -float(score),
            "score": float(score),
        })
    return results


def _dense_retrieve(
    query: str,
    *,
    top_k: int,
    collection_name: str,
    silent_missing_deps: bool = False,
) -> list[dict]:
    """Dense ChromaDB retrieval (legacy v2.0 path)."""
    if not _chromadb_available():
        if silent_missing_deps:
            return []
        # Surface a friendly error consistent with _get_client().
        _get_client()  # exits with the standard message
        return []

    client = _get_client()
    embedding_fn = _get_embedding_fn()

    try:
        collection = client.get_collection(
            name=collection_name,
            embedding_function=embedding_fn,
        )
    except Exception:
        if not silent_missing_deps:
            print(f"⚠️  Collection '{collection_name}' not found. Run ingest first.")
        return []

    actual_count = collection.count()
    if actual_count == 0:
        if not silent_missing_deps:
            print(f"⚠️  Collection '{collection_name}' is empty.")
        return []

    n = min(top_k, actual_count)
    results = collection.query(query_texts=[query], n_results=n)

    items = []
    if results and results["ids"] and results["ids"][0]:
        for i, doc_id in enumerate(results["ids"][0]):
            items.append({
                "id": doc_id,
                "document": results["documents"][0][i] if results["documents"] else "",
                "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                "distance": results["distances"][0][i] if results["distances"] else None,
            })
    return items


def _rrf_fuse(
    dense_results: list[dict],
    sparse_results: list[dict],
    *,
    k: int = DEFAULT_RRF_K,
) -> list[dict]:
    """Reciprocal Rank Fusion: score(d) = Σ 1 / (k + rank_i(d)).

    Higher fused score wins. Items present in only one ranker are still fused
    (with a single contribution). Output mirrors `_rrf` into `distance` (negated)
    so downstream consumers can rank by ascending distance like with dense.
    """
    by_id: dict[str, dict] = {}

    for rank, item in enumerate(dense_results, start=1):
        slot = by_id.setdefault(item["id"], {**item, "_sources": []})
        slot["_rrf"] = slot.get("_rrf", 0.0) + 1.0 / (k + rank)
        slot["_sources"].append("dense")

    for rank, item in enumerate(sparse_results, start=1):
        slot = by_id.setdefault(item["id"], {**item, "_sources": []})
        slot["_rrf"] = slot.get("_rrf", 0.0) + 1.0 / (k + rank)
        slot["_sources"].append("sparse")

    merged = sorted(by_id.values(), key=lambda d: d["_rrf"], reverse=True)
    for item in merged:
        item["distance"] = -item["_rrf"]
    return merged


def _log_retrieval(
    *,
    query: str,
    collection: str,
    mode: str,
    items: list[dict],
) -> None:
    import datetime
    log_entry = {
        "timestamp": datetime.datetime.now(datetime.UTC).isoformat(),
        "query": query,
        "collection": collection,
        "mode": mode,
        "retrieved_ids": [item["id"] for item in items],
    }
    RETRIEVAL_LOGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with RETRIEVAL_LOGS_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry) + "\n")


def retrieve(
    query: str,
    *,
    top_k: int = 5,
    collection_name: str = COLLECTION_LESSONS,
    mode: str = DEFAULT_MODE,
    rrf_k: int = DEFAULT_RRF_K,
) -> list[dict]:
    """Hybrid / dense / sparse retrieval over a collection.

    mode:
      - 'dense'  — ChromaDB embedding search (v2.0 legacy behaviour).
      - 'sparse' — BM25 over lessons.md / trajectories.jsonl. No ChromaDB needed.
      - 'hybrid' — Reciprocal Rank Fusion of dense + sparse (default).
                   If ChromaDB is unavailable, gracefully degrades to sparse only.
    Returns list of items with keys: id, document, metadata, distance.
    """
    if mode not in VALID_MODES:
        raise ValueError(f"Unknown mode: {mode!r} (expected one of {VALID_MODES})")

    if mode == "sparse":
        items = _bm25_retrieve(query, top_k=top_k, collection_name=collection_name)
    elif mode == "dense":
        items = _dense_retrieve(query, top_k=top_k, collection_name=collection_name)
    else:  # hybrid
        # Over-fetch from each ranker so RRF has signal to fuse before truncation.
        fetch_k = max(top_k * 4, 20)
        dense = _dense_retrieve(
            query, top_k=fetch_k, collection_name=collection_name,
            silent_missing_deps=True,
        )
        sparse = _bm25_retrieve(query, top_k=fetch_k, collection_name=collection_name)
        items = _rrf_fuse(dense, sparse, k=rrf_k)[:top_k]

    if items:
        _log_retrieval(query=query, collection=collection_name, mode=mode, items=items)
    return items


def show_stats() -> None:
    """Print collection statistics."""
    client = _get_client()
    print("📊 ReasoningBank Stats")
    print("=" * 40)
    for name in [COLLECTION_LESSONS, COLLECTION_TRAJECTORIES]:
        try:
            col = client.get_collection(name=name)
            print(f"  {name}: {col.count()} records")
        except Exception:
            print(f"  {name}: (not created)")
    print(f"  model: {MODEL_NAME}")
    print(f"  custom model: {CUSTOM_MODEL_PATH} ({'exists' if CUSTOM_MODEL_PATH.exists() else 'not found — using base'})")
    print(f"  db_path: {DB_PATH.resolve()}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main() -> None:
    """CLI entry point for reasoning_bank operations."""
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    command = sys.argv[1]

    if command == "ingest_lessons":
        ingest_lessons()

    elif command == "ingest_trajectories":
        ingest_trajectories()

    elif command == "ingest_all":
        ingest_lessons()
        ingest_trajectories()

    elif command == "retrieve":
        if len(sys.argv) < 3:
            print(
                'Usage: python scripts/reasoning_bank.py retrieve "query" '
                "[--top-k 5] [--mode hybrid|dense|sparse] [--rrf-k 60]"
            )
            sys.exit(1)

        query = sys.argv[2]
        top_k = 5
        collection = COLLECTION_LESSONS
        mode = DEFAULT_MODE
        rrf_k = DEFAULT_RRF_K

        i = 3
        while i < len(sys.argv):
            if sys.argv[i] == "--top-k" and i + 1 < len(sys.argv):
                top_k = int(sys.argv[i + 1])
                i += 2
            elif sys.argv[i] == "--collection" and i + 1 < len(sys.argv):
                collection = sys.argv[i + 1]
                i += 2
            elif sys.argv[i] == "--mode" and i + 1 < len(sys.argv):
                mode = sys.argv[i + 1]
                if mode not in VALID_MODES:
                    print(
                        f"❌ Error: invalid --mode {mode!r}. "
                        f"Expected one of {VALID_MODES}.",
                        file=sys.stderr,
                    )
                    sys.exit(2)
                i += 2
            elif sys.argv[i] == "--rrf-k" and i + 1 < len(sys.argv):
                rrf_k = int(sys.argv[i + 1])
                i += 2
            else:
                i += 1

        results = retrieve(
            query,
            top_k=top_k,
            collection_name=collection,
            mode=mode,
            rrf_k=rrf_k,
        )
        if not results:
            print("No results found.")
            return

        print(f'\n🔍 Top-{len(results)} results for: "{query}" (mode={mode})')
        print("=" * 60)
        for rank, item in enumerate(results, 1):
            meta = item["metadata"]
            title = meta.get("title", item["id"])
            distance = item.get("distance")
            dist_str = f"{distance:.4f}" if isinstance(distance, (int, float)) else "n/a"
            sources = item.get("_sources")
            tag = f" via {'+'.join(sources)}" if sources else ""
            print(f"\n#{rank} [{item['id']}] (distance: {dist_str}{tag})")
            print(f"   Title: {title}")
            if "description" in meta:
                print(f"   Description: {meta['description']}")
            if "source" in meta:
                print(f"   Source: {meta['source']}")

    elif command == "stats":
        show_stats()

    else:
        print(f"Unknown command: {command}")
        print("Available: ingest_lessons, ingest_trajectories, ingest_all, retrieve, stats")
        sys.exit(1)


if __name__ == "__main__":
    main()
