"""Loaders for LIAR + FakeNewsNet, unified to a binary {Fake=0, Real=1} label.

LIAR's original 6-way ruling is collapsed:
    pants-fire, false, barely-true   -> Fake (0)
    half-true, mostly-true, true     -> Real (1)

FakeNewsNet ships labels per dataset (politifact / gossipcop) where each
record is already labeled fake/real.
"""
from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

log = logging.getLogger(__name__)

LIAR_LABELS_FAKE = {"pants-fire", "false", "barely-true"}
LIAR_LABELS_REAL = {"half-true", "mostly-true", "true"}


@dataclass
class Sample:
    text: str
    label: int
    source: str


def load_liar(path: str) -> list[Sample]:
    """LIAR comes as TSV with columns:
    [id, label, statement, subject, speaker, job, state, party, ...]
    """
    samples: list[Sample] = []
    files = ["train.tsv", "valid.tsv", "test.tsv"]
    for name in files:
        full = Path(path) / name
        if not full.exists():
            log.warning("LIAR file missing: %s", full)
            continue
        df = pd.read_csv(full, sep="\t", header=None, on_bad_lines="skip")
        for _, row in df.iterrows():
            label = str(row[1]).strip().lower()
            statement = str(row[2]).strip()
            if not statement:
                continue
            if label in LIAR_LABELS_FAKE:
                samples.append(Sample(statement, 0, "liar"))
            elif label in LIAR_LABELS_REAL:
                samples.append(Sample(statement, 1, "liar"))
    log.info("LIAR samples: %d", len(samples))
    return samples


def load_fakenewsnet(path: str) -> list[Sample]:
    """FakeNewsNet folder layout (post-extraction):

        path/
            politifact_fake.csv
            politifact_real.csv
            gossipcop_fake.csv
            gossipcop_real.csv

    Each CSV has at least `title` and optionally `text`/`news_url`.
    """
    samples: list[Sample] = []
    files = {
        "politifact_fake.csv": 0,
        "politifact_real.csv": 1,
        "gossipcop_fake.csv": 0,
        "gossipcop_real.csv": 1,
    }
    for name, label in files.items():
        full = Path(path) / name
        if not full.exists():
            log.warning("FakeNewsNet file missing: %s", full)
            continue
        df = pd.read_csv(full, on_bad_lines="skip")
        title_col = next((c for c in df.columns if c.lower() == "title"), None)
        text_col = next((c for c in df.columns if c.lower() in {"text", "content"}), None)
        if title_col is None:
            log.warning("No title column in %s", name)
            continue
        for _, row in df.iterrows():
            title = str(row.get(title_col, "")).strip()
            body = str(row.get(text_col, "")).strip() if text_col else ""
            text = (title + ". " + body).strip(". ").strip()
            if text:
                samples.append(Sample(text, label, name.split("_")[0]))
    log.info("FakeNewsNet samples: %d", len(samples))
    return samples


def load_all(liar_path: str | None, fnn_path: str | None) -> pd.DataFrame:
    samples: list[Sample] = []
    if liar_path and os.path.isdir(liar_path):
        samples.extend(load_liar(liar_path))
    if fnn_path and os.path.isdir(fnn_path):
        samples.extend(load_fakenewsnet(fnn_path))
    if not samples:
        raise RuntimeError("No samples loaded; check --liar and --fnn paths")
    return pd.DataFrame([s.__dict__ for s in samples])


def dataset_hash(df: pd.DataFrame) -> str:
    import hashlib

    buf = json.dumps(
        {"n": len(df), "pos": int((df.label == 1).sum()), "neg": int((df.label == 0).sum())},
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha1(buf).hexdigest()[:8]
