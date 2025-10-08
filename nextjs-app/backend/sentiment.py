"""Sentiment helpers using VADER."""
from __future__ import annotations

from functools import lru_cache

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer


@lru_cache(maxsize=1)
def _analyzer() -> SentimentIntensityAnalyzer:
    return SentimentIntensityAnalyzer()


def classify_sentiment(text: str, return_score: bool = False):
    """Classify sentiment; optionally return (label, compound score).

    Thresholds:
        compound >= 0.25 -> Positive
        compound <= -0.25 -> Negative
        otherwise -> Neutral
    """
    if not text:
        return ("Neutral", 0.0) if return_score else "Neutral"
    compound = _analyzer().polarity_scores(text)["compound"]
    if compound >= 0.25:
        label = "Positive"
    elif compound <= -0.25:
        label = "Negative"
    else:
        label = "Neutral"
    return (label, compound) if return_score else label
