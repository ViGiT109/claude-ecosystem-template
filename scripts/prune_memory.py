#!/usr/bin/env python3
"""
ReasoningBank Pruning Module — Phase 3.

Finds semantic duplicates in ChromaDB memory to keep context size manageable.
Generates a markdown report for manual merging by the agent.

Usage:
    python scripts/prune_memory.py [--threshold 0.90]
"""

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.reasoning_bank import COLLECTION_LESSONS, _get_client

REPORT_FILE = Path("docs/duplicates_to_merge.md")


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    dot = np.dot(a, b)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(dot / (norm_a * norm_b))


def find_duplicates(threshold: float = 0.90) -> None:
    client = _get_client()
    try:
        collection = client.get_collection(name=COLLECTION_LESSONS)
    except Exception:
        print(f"⚠️  Collection '{COLLECTION_LESSONS}' not found. Cannot prune.")
        return

    data = collection.get(include=["embeddings", "metadatas"])
    ids = data.get("ids", [])
    embeddings = data.get("embeddings", [])
    metadatas = data.get("metadatas", [])

    if len(ids) == 0 or len(embeddings) == 0:
        print("No embeddings found. Run ingest_lessons first.")
        return

    print(f"🔍 Analyzing {len(ids)} lessons for duplicates (threshold: {threshold})...")

    duplicates = []
    n = len(ids)
    for i in range(n):
        for j in range(i + 1, n):
            sim = cosine_similarity(embeddings[i], embeddings[j])
            if sim >= threshold:
                duplicates.append({
                    "sim": sim,
                    "id1": ids[i],
                    "title1": metadatas[i].get("title", ""),
                    "id2": ids[j],
                    "title2": metadatas[j].get("title", ""),
                })

    if not duplicates:
        print("✅ No duplicates found.")
        REPORT_FILE.parent.mkdir(exist_ok=True)
        if REPORT_FILE.exists():
            REPORT_FILE.unlink()
        return

    duplicates.sort(key=lambda x: x["sim"], reverse=True)

    report_lines = [
        "# Memory Pruning Report",
        "",
        f"Found {len(duplicates)} pairs of semantic duplicates (similarity >= {threshold}).",
        "Review and merge them in `.memory/lessons.md` if appropriate, "
        "then run `python scripts/reasoning_bank.py ingest_lessons`.",
        "",
    ]
    for d in duplicates:
        report_lines.append(f"## Similarity: {d['sim']:.4f}")
        report_lines.append(f"- **{d['id1']}**: {d['title1']}")
        report_lines.append(f"- **{d['id2']}**: {d['title2']}")
        report_lines.append("")

    REPORT_FILE.write_text("\n".join(report_lines), encoding="utf-8")
    print(f"⚠️  Found {len(duplicates)} potential duplicates.")
    print(f"📝 Report saved to {REPORT_FILE}")


def main() -> None:
    threshold = 0.90
    if "--threshold" in sys.argv:
        idx = sys.argv.index("--threshold")
        if idx + 1 < len(sys.argv):
            threshold = float(sys.argv[idx + 1])
    find_duplicates(threshold)


if __name__ == "__main__":
    main()
