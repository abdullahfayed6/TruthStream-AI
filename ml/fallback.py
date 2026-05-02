"""Deterministic fallback classifier used until DistilBERT weights are trained.

Importable without PySpark / Torch so unit tests stay light.
"""
from __future__ import annotations

import hashlib

import pandas as pd


def fallback_predict(texts: pd.Series) -> pd.DataFrame:
    """Hash-based stand-in.

    Confidence is in [0.5, 0.99]; label flips on hash parity. Output is
    deterministic for the same input.
    """
    labels: list[str] = []
    confs: list[float] = []
    for text in texts.fillna("").astype(str):
        digest = hashlib.md5(text.encode("utf-8")).digest()
        score = 0.5 + (digest[0] / 255.0) * 0.49
        label = "Fake" if digest[1] % 2 == 0 else "Real"
        labels.append(label)
        confs.append(round(score, 4))
    return pd.DataFrame({"label": labels, "confidence": confs})
