"""Download a pre-trained fake-news DistilBERT model from HuggingFace.

This script downloads `mrm8488/bert-tiny-finetuned-fake-news-detection` (a
lightweight model fine-tuned for binary fake-news classification) and saves it
to ml/models/distilbert-fakenews so the inference UDF picks it up automatically.

Usage:
    python -m ml.download_model
    python -m ml.download_model --model GonzaloA/fake-news --output ml/models/distilbert-fakenews
"""
from __future__ import annotations

import argparse
import json
import logging
import os
from pathlib import Path

log = logging.getLogger(__name__)

KNOWN_MODELS = {
    "primary":   "GonzaloA/fake-news",
    "small":     "mrm8488/bert-tiny-finetuned-fake-news-detection",
    "distilbert": "jy46604790/Fake-News-Bert-Detect",
}


def download(model_name: str, output_dir: str) -> None:
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    log.info("Downloading tokenizer from %s …", model_name)
    tokenizer = AutoTokenizer.from_pretrained(model_name)

    log.info("Downloading model from %s …", model_name)
    model = AutoModelForSequenceClassification.from_pretrained(model_name)

    tokenizer.save_pretrained(str(out))
    model.save_pretrained(str(out))

    meta = {
        "hf_model": model_name,
        "num_labels": model.config.num_labels,
        "id2label": model.config.id2label,
        "label2id": model.config.label2id,
    }
    with open(out / "hf_metadata.json", "w") as f:
        json.dump(meta, f, indent=2)

    log.info("✅  Model saved to %s", out)
    log.info("   id2label: %s", model.config.id2label)


def patch_inference_labels(model_dir: str) -> None:
    """Read the model's actual label map and write a normalisation file.

    The inference UDF expects labels 'Fake'/'Real'. Different HF models use
    different string labels (FAKE/REAL, 0/1, fake/real …). We write a
    normalisation JSON so inference.py can remap them at runtime.
    """
    meta_path = Path(model_dir) / "hf_metadata.json"
    if not meta_path.exists():
        return

    with open(meta_path) as f:
        meta = json.load(f)

    id2label = {int(k): v for k, v in meta.get("id2label", {}).items()}

    norm: dict[str, str] = {}
    for raw in id2label.values():
        upper = raw.upper()
        if "FAKE" in upper or upper == "0":
            norm[raw] = "Fake"
        else:
            norm[raw] = "Real"

    with open(Path(model_dir) / "label_norm.json", "w") as f:
        json.dump(norm, f, indent=2)

    log.info("Label normalisation map: %s", norm)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    parser = argparse.ArgumentParser(description="Download a fake-news HF model.")
    parser.add_argument(
        "--model",
        default=os.environ.get("HF_MODEL", KNOWN_MODELS["primary"]),
        help="HuggingFace model repo (default: GonzaloA/fake-news)",
    )
    parser.add_argument(
        "--output",
        default=os.environ.get("MODEL_PATH", "ml/models/distilbert-fakenews"),
        help="Local output directory",
    )
    parser.add_argument(
        "--small",
        action="store_true",
        help="Use the small/fast model instead of the primary one",
    )
    args = parser.parse_args()

    model_name = KNOWN_MODELS["small"] if args.small else args.model

    download(model_name, args.output)
    patch_inference_labels(args.output)


if __name__ == "__main__":
    main()
