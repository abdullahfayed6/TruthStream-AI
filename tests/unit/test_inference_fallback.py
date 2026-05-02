import pandas as pd

from ml.fallback import fallback_predict as _fallback_predict


def test_fallback_returns_label_and_confidence_for_each_row():
    titles = pd.Series(["Aliens land in NYC", "Stocks open higher", ""])
    out = _fallback_predict(titles)
    assert list(out.columns) == ["label", "confidence"]
    assert len(out) == 3
    assert set(out["label"]).issubset({"Fake", "Real"})
    assert (out["confidence"] >= 0.5).all() and (out["confidence"] <= 0.99).all()


def test_fallback_is_deterministic():
    s = pd.Series(["same input"] * 5)
    a = _fallback_predict(s)
    b = _fallback_predict(s)
    pd.testing.assert_frame_equal(a, b)
