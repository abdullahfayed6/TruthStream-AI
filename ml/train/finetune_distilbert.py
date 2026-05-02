"""Fine-tune distilbert-base-uncased on the unified LIAR + FakeNewsNet split.

Usage (Colab GPU recommended):
    python -m ml.train.finetune_distilbert \
        --liar data/liar \
        --fnn  data/fakenewsnet \
        --output ml/models/distilbert-fakenews
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import logging
import os
from pathlib import Path

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
)
from sklearn.model_selection import train_test_split

from ml.train.datasets import dataset_hash, load_all

log = logging.getLogger(__name__)


def build_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--liar", default=os.environ.get("LIAR_PATH", ""))
    parser.add_argument("--fnn", default=os.environ.get("FNN_PATH", ""))
    parser.add_argument("--output", required=True)
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--lr", type=float, default=2e-5)
    parser.add_argument("--max-len", type=int, default=256)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--test-size", type=float, default=0.1)
    return parser.parse_args()


def compute_metrics(eval_pred):
    logits, labels = eval_pred
    preds = np.argmax(logits, axis=-1)
    return {
        "accuracy": accuracy_score(labels, preds),
        "f1": f1_score(labels, preds, average="binary"),
    }


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    args = build_args()

    import torch
    from datasets import Dataset
    from transformers import (
        AutoModelForSequenceClassification,
        AutoTokenizer,
        DataCollatorWithPadding,
        Trainer,
        TrainingArguments,
    )

    log.info("Loading data...")
    df = load_all(args.liar or None, args.fnn or None)
    log.info("Total samples: %d  (Fake=%d, Real=%d)",
             len(df), int((df.label == 0).sum()), int((df.label == 1).sum()))

    train_df, eval_df = train_test_split(
        df, test_size=args.test_size, random_state=args.seed, stratify=df["label"]
    )

    model_name = "distilbert-base-uncased"
    tokenizer = AutoTokenizer.from_pretrained(model_name)

    def tokenize(batch):
        return tokenizer(
            batch["text"],
            truncation=True,
            max_length=args.max_len,
        )

    train_ds = Dataset.from_pandas(train_df[["text", "label"]]).map(tokenize, batched=True)
    eval_ds = Dataset.from_pandas(eval_df[["text", "label"]]).map(tokenize, batched=True)

    model = AutoModelForSequenceClassification.from_pretrained(
        model_name, num_labels=2, id2label={0: "Fake", 1: "Real"}, label2id={"Fake": 0, "Real": 1}
    )

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    training_args = TrainingArguments(
        output_dir=str(output_dir / "trainer"),
        learning_rate=args.lr,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size,
        num_train_epochs=args.epochs,
        eval_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="f1",
        greater_is_better=True,
        logging_steps=50,
        seed=args.seed,
        fp16=torch.cuda.is_available(),
        report_to=[],
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_ds,
        eval_dataset=eval_ds,
        tokenizer=tokenizer,
        data_collator=DataCollatorWithPadding(tokenizer),
        compute_metrics=compute_metrics,
    )

    trainer.train()
    metrics = trainer.evaluate()
    log.info("Eval metrics: %s", metrics)

    preds = trainer.predict(eval_ds)
    y_true = preds.label_ids
    y_pred = np.argmax(preds.predictions, axis=-1)

    cm = confusion_matrix(y_true, y_pred).tolist()
    report = classification_report(y_true, y_pred, target_names=["Fake", "Real"], output_dict=True)

    trainer.save_model(str(output_dir))
    tokenizer.save_pretrained(str(output_dir))

    meta = {
        "trained_at": dt.datetime.utcnow().isoformat() + "Z",
        "dataset_hash": dataset_hash(df),
        "n_train": len(train_df),
        "n_eval": len(eval_df),
        "metrics": metrics,
        "confusion_matrix": cm,
        "classification_report": report,
        "args": vars(args),
    }
    with open(output_dir / "metadata.json", "w") as f:
        json.dump(meta, f, indent=2)

    log.info("Saved model + metadata to %s", output_dir)


if __name__ == "__main__":
    main()
