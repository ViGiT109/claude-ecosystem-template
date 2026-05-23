#!/usr/bin/env python3
"""
ReasoningBank Contrastive Learning Module — Phase 3.

Fine-tunes the 'all-mpnet-base-v2' embedding model using usage logs
(retrieval_logs.jsonl + session_trajectories.jsonl) or synthetic fallback pairs.
Uses MultipleNegativesRankingLoss for fast semantic search alignment.

Saves the fine-tuned model to .memory/models/project-mpnet/,
which reasoning_bank.py will prefer over the base model on subsequent runs.

Usage:
    python scripts/train_reasoning_bank.py [--epochs 3] [--batch-size 8]

Prerequisites:
    pip install sentence-transformers torch
    python scripts/reasoning_bank.py ingest_lessons  (populate retrieval_logs first)
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.reasoning_bank import CUSTOM_MODEL_PATH, MODEL_NAME, RETRIEVAL_LOGS_FILE, parse_lessons

try:
    import torch
    from sentence_transformers import InputExample, SentenceTransformer, losses
    from torch.utils.data import DataLoader
except ImportError:
    print("⚠️  Dependencies missing. Run: pip install sentence-transformers torch")
    sys.exit(1)


def get_training_data() -> list[InputExample]:
    """Build triplet dataset (Anchor, Positive) for contrastive learning."""
    lessons = parse_lessons()
    if not lessons:
        print("⚠️  No lessons found.")
        return []

    lesson_by_id = {lesson["id"]: lesson for lesson in lessons}
    train_examples: list[InputExample] = []

    if RETRIEVAL_LOGS_FILE.exists():
        print(f"📄 Found retrieval logs: {RETRIEVAL_LOGS_FILE}")
        for line in RETRIEVAL_LOGS_FILE.read_text("utf-8").splitlines():
            try:
                log = json.loads(line)
            except json.JSONDecodeError:
                continue
            query = log.get("query", "")
            retrieved_ids = log.get("retrieved_ids", [])
            if not query or not retrieved_ids:
                continue
            pos_id = retrieved_ids[0]
            if pos_id in lesson_by_id:
                train_examples.append(InputExample(texts=[query, lesson_by_id[pos_id]["document"]]))

    print("🧠 Generating synthetic pairs from lessons...")
    for lesson in lessons:
        anchor = f"{lesson['title']}. {lesson.get('description', '')}"
        train_examples.append(InputExample(texts=[anchor, lesson["document"]]))
        if lesson.get("description"):
            train_examples.append(InputExample(texts=[lesson["title"], lesson["description"]]))

    return train_examples


def train(epochs: int = 1, batch_size: int = 4) -> None:
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"🚀 Training on: {device.upper()}")

    model_to_load = str(CUSTOM_MODEL_PATH) if CUSTOM_MODEL_PATH.exists() else MODEL_NAME
    print(f"📦 Loading model: {model_to_load}")
    model = SentenceTransformer(model_to_load, device=device)

    train_examples = get_training_data()
    if not train_examples:
        print("❌ No training data available.")
        return

    print(f"📊 Dataset size: {len(train_examples)} pairs")
    actual_batch_size = min(batch_size, len(train_examples))
    train_dataloader = DataLoader(train_examples, shuffle=True, batch_size=actual_batch_size)
    train_loss = losses.MultipleNegativesRankingLoss(model=model)
    warmup_steps = int(len(train_dataloader) * epochs * 0.1)

    print(f"⏳ Training: {epochs} epochs, batch={actual_batch_size}, warmup={warmup_steps}...")
    model.fit(
        train_objectives=[(train_dataloader, train_loss)],
        epochs=epochs,
        warmup_steps=warmup_steps,
        show_progress_bar=True,
    )

    CUSTOM_MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    model.save(str(CUSTOM_MODEL_PATH))
    print(f"✅ Custom model saved to {CUSTOM_MODEL_PATH}")
    print("Run `python scripts/reasoning_bank.py retrieve` to test the fine-tuned model.")


def main() -> None:
    epochs = 3
    batch_size = 8
    args = sys.argv[1:]
    if "--epochs" in args:
        idx = args.index("--epochs")
        epochs = int(args[idx + 1])
    if "--batch-size" in args:
        idx = args.index("--batch-size")
        batch_size = int(args[idx + 1])
    train(epochs, batch_size)


if __name__ == "__main__":
    main()
