"""
sentiment_analysis.py
Classifies reviews as POSITIVE, NEGATIVE, or NEUTRAL.
Uses TextBlob (fast, no GPU needed) with optional HuggingFace upgrade.
"""

from typing import List, Dict, Any
from textblob import TextBlob


def analyze_sentiment(text: str) -> Dict[str, Any]:
    blob = TextBlob(text)
    polarity = blob.sentiment.polarity  # -1 to 1

    if polarity > 0.1:
        label = "POSITIVE"
    elif polarity < -0.1:
        label = "NEGATIVE"
    else:
        label = "NEUTRAL"

    return {
        "label": label,
        "score": round(polarity, 3),
    }


def analyze_batch(reviews: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Add sentiment to each review dict."""
    for r in reviews:
        result = analyze_sentiment(r.get("text", ""))
        r["sentiment"] = result["label"]
        r["sentiment_score"] = result["score"]
    return reviews


def get_sentiment_summary(reviews: List[Dict[str, Any]]) -> Dict[str, Any]:
    total = len(reviews)
    if total == 0:
        return {"positive": 0, "negative": 0, "neutral": 0,
                "positive_pct": 0, "negative_pct": 0, "neutral_pct": 0, "total": 0}

    positive = sum(1 for r in reviews if r.get("sentiment") == "POSITIVE")
    negative = sum(1 for r in reviews if r.get("sentiment") == "NEGATIVE")
    neutral  = sum(1 for r in reviews if r.get("sentiment") == "NEUTRAL")

    return {
        "positive": positive,
        "negative": negative,
        "neutral": neutral,
        "positive_pct": round(positive / total * 100, 1),
        "negative_pct": round(negative / total * 100, 1),
        "neutral_pct":  round(neutral  / total * 100, 1),
        "total": total,
    }
