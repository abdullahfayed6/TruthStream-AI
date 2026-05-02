"""DistilBERT inference exposed as a Spark Pandas UDF.

The UDF loads the model **once per executor** (module-level singleton) and
batches rows of 32. If the trained weights aren't present, a deterministic
fallback classifier kicks in so the streaming pipeline still produces output
end-to-end during early development.

Label normalisation
-------------------
HuggingFace models use different label strings (FAKE/REAL, 0/1, fake/real …).
If ml/models/distilbert-fakenews/label_norm.json exists (written by
ml/download_model.py) the raw labels are remapped to 'Fake'/'Real'.
"""
from __future__ import annotations

import json
import logging
import os

import pandas as pd
from pyspark.sql.functions import pandas_udf
from pyspark.sql.types import FloatType, StringType, StructField, StructType

from ml.fallback import fallback_predict as _fallback_predict

log = logging.getLogger(__name__)

PREDICTION_SCHEMA = StructType(
    [
        StructField("label", StringType(), False),
        StructField("confidence", FloatType(), False),
    ]
)

_MAX_LEN = 256
_BATCH_SIZE = 32

_model = None
_tokenizer = None
_device = None
_label_norm: dict[str, str] = {}
_loaded = False


def _load_label_norm(model_path: str) -> dict[str, str]:
    norm_file = os.path.join(model_path, "label_norm.json")
    if os.path.isfile(norm_file):
        with open(norm_file) as f:
            return json.load(f)
    # Fallback: inspect config.json directly
    cfg_file = os.path.join(model_path, "config.json")
    if os.path.isfile(cfg_file):
        with open(cfg_file) as f:
            cfg = json.load(f)
        id2label = cfg.get("id2label", {})
        norm: dict[str, str] = {}
        for raw in id2label.values():
            upper = raw.upper()
            norm[raw] = "Fake" if ("FAKE" in upper or upper == "0") else "Real"
        return norm
    return {}


def _try_load_model() -> bool:
    """Best-effort load of fine-tuned DistilBERT. Returns True on success."""
    global _model, _tokenizer, _device, _label_norm, _loaded
    if _loaded:
        return _model is not None

    _loaded = True
    model_path = os.environ.get("MODEL_PATH", "/opt/models/distilbert-fakenews")
    fallback_ok = os.environ.get("MODEL_FALLBACK", "true").lower() == "true"

    if not os.path.isdir(model_path) or not os.listdir(model_path):
        if not fallback_ok:
            raise RuntimeError(f"Model dir empty: {model_path}")
        log.warning("No model at %s; using fallback classifier", model_path)
        return False

    try:
        import torch
        from transformers import AutoModelForSequenceClassification, AutoTokenizer

        _device = "cuda" if torch.cuda.is_available() else "cpu"
        _tokenizer = AutoTokenizer.from_pretrained(model_path)
        _model = AutoModelForSequenceClassification.from_pretrained(model_path).to(_device)
        _model.eval()
        _label_norm = _load_label_norm(model_path)
        log.info("Loaded model from %s on %s | label_norm=%s", model_path, _device, _label_norm)
        return True
    except Exception as exc:  # noqa: BLE001
        if not fallback_ok:
            raise
        log.exception("Model load failed (%s); using fallback", exc)
        _model = None
        return False


def _normalise(raw_label: str) -> str:
    """Remap model-specific label strings to 'Fake' / 'Real'."""
    if _label_norm:
        return _label_norm.get(raw_label, raw_label)
    upper = raw_label.upper()
    return "Fake" if ("FAKE" in upper or upper == "0") else "Real"


def _bert_predict(texts: pd.Series) -> pd.DataFrame:
    import torch

    labels: list[str] = []
    confs: list[float] = []
    series = texts.fillna("").astype(str).tolist()

    with torch.no_grad():
        for start in range(0, len(series), _BATCH_SIZE):
            chunk = series[start : start + _BATCH_SIZE]
            enc = _tokenizer(
                chunk,
                truncation=True,
                padding=True,
                max_length=_MAX_LEN,
                return_tensors="pt",
            ).to(_device)
            logits = _model(**enc).logits
            probs = torch.softmax(logits, dim=-1).cpu().numpy()
            id2label = _model.config.id2label
            for row in probs:
                idx = int(row.argmax())
                raw_label = id2label[idx]
                labels.append(_normalise(raw_label))
                confs.append(float(row[idx]))

    return pd.DataFrame({"label": labels, "confidence": confs})


@pandas_udf(PREDICTION_SCHEMA)
def score_udf(title: pd.Series, content: pd.Series) -> pd.DataFrame:
    """Score a batch of articles. Combines title + content for context."""
    text = (title.fillna("") + ". " + content.fillna("")).str.slice(0, 4000)
    if _try_load_model():
        return _bert_predict(text)
    return _fallback_predict(text)


def predict_single(title: str, content: str = "") -> dict:
    """Convenience function for standalone testing (no Spark needed)."""
    text = pd.Series([(title + ". " + content)[:4000]])
    if _try_load_model():
        result = _bert_predict(text)
    else:
        result = _fallback_predict(text)
    return {"label": result["label"].iloc[0], "confidence": float(result["confidence"].iloc[0])}
