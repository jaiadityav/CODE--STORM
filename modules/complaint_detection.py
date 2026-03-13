"""
complaint_detection.py
Upgraded: LLM-style clustering (sentence-transformers + KMeans) instead of
pure keyword matching, focused on 1–3 star reviews as the problem statement requires.

Pipeline:
  1. Filter to 1–3 star / NEGATIVE reviews only
  2. Sentence-transformer embeddings + KMeans  →  data-driven clusters
  3. Map clusters back to the 5 canonical themes via keyword voting
  4. Extract top negative keywords via TF-IDF
"""

import re
import logging
from typing import List, Dict, Any, Optional
from collections import Counter

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans

logger = logging.getLogger(__name__)

# ── The 8 complaint themes ────────────────────────────────────────────────────
THEMES = {
    "Sizing / Fit Issue": [
        "size", "sizing", "fit", "fitting", "small", "large", "tight", "loose",
        "wrong size", "size chart", "measurements", "too big", "too small",
        "doesn't fit", "did not fit", "size issue", "xl", "medium", "length",
        "width", "runs small", "runs large",
    ],
    "Product Quality": [
        "quality", "poor quality", "cheap", "bad quality", "broke", "broken",
        "defective", "damage", "damaged", "not working", "stopped working",
        "fell apart", "flimsy", "durable", "durability", "build quality",
        "material", "fake", "duplicate", "original", "fragile", "cracked",
        "scratch", "smell", "chemical",
    ],
    "Misleading Listing": [
        "color", "colour", "not as described", "misleading", "different",
        "wrong color", "not same", "picture", "image", "photo",
        "not matching", "description", "listing", "fake image", "false",
        "advertised", "actual product", "shown in photo", "not what i expected",
        "not what was shown", "different from",
    ],
    "Packaging Issue": [
        "packaging", "package", "packing", "packed", "box", "damaged box",
        "open box", "torn", "broken packaging", "poorly packed", "crushed",
        "dented", "arrived broken", "not protected", "bubble wrap",
    ],
    "Delivery / Logistics": [
        "delivery", "shipping", "late", "delayed", "not delivered", "lost",
        "wrong item", "wrong product", "delivered wrong", "courier",
        "dispatch", "tracking", "never arrived", "weeks", "days late",
        "slow delivery", "missing item",
    ],
    "Customer Service": [
        "customer service", "support", "refund", "return", "replacement",
        "no response", "pathetic service", "helpless", "rude",
        "not helpful", "exchange", "complaint",
    ],
    "Price / Value": [
        "overpriced", "expensive", "not worth", "waste of money",
        "waste", "value for money", "price", "costly", "not worth it",
    ],
    "Missing Parts": [
        "missing", "incomplete", "not included", "accessories",
        "parts missing", "manual", "charger", "cable",
    ],
}


# ── Focus on 1–3 star reviews (problem statement requirement) ─────────────────

def filter_low_star(reviews: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Returns only 1–3 star OR NEGATIVE/NEUTRAL reviews.
    Matches the hint: 'Focus on 1–3 star reviews'.
    """
    result = []
    for r in reviews:
        rating = float(r.get("rating", 0))
        sentiment = r.get("sentiment", "")
        if (1 <= rating <= 3) or sentiment in ("NEGATIVE", "NEUTRAL"):
            result.append(r)
    return result or reviews   # fallback: all reviews


# ── Keyword theme label ────────────────────────────────────────────────────────

def _keyword_theme(text: str) -> Optional[str]:
    text_lower = text.lower()
    scores: Counter = Counter()
    for theme, keywords in THEMES.items():
        for kw in keywords:
            if re.search(r"\b" + re.escape(kw) + r"\b", text_lower):
                scores[theme] += 1
    return scores.most_common(1)[0][0] if scores else None


# ── LLM-style semantic clustering ────────────────────────────────────────────

def _llm_cluster(texts: List[str], n_clusters: int) -> List[int]:
    """
    Tries sentence-transformers (semantic/LLM-style) first.
    Falls back to TF-IDF + KMeans if not installed.
    """
    n = min(n_clusters, max(1, len(texts)))

    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer("all-MiniLM-L6-v2")
        embeddings = model.encode(texts, show_progress_bar=False)
        km = KMeans(n_clusters=n, random_state=42, n_init=10)
        labels = km.fit_predict(embeddings).tolist()
        logger.info(f"LLM clustering: sentence-transformers, n={n}")
        return labels
    except ImportError:
        logger.info("sentence-transformers not installed — using TF-IDF fallback")
    except Exception as e:
        logger.warning(f"LLM clustering error: {e}")

    try:
        vec = TfidfVectorizer(max_features=300, stop_words="english")
        X = vec.fit_transform(texts)
        km = KMeans(n_clusters=n, random_state=42, n_init=10)
        return km.fit_predict(X).tolist()
    except Exception:
        return [0] * len(texts)


def _map_cluster_to_theme(cluster_texts: List[str]) -> str:
    scores: Counter = Counter()
    for text in cluster_texts:
        t = _keyword_theme(text)
        if t:
            scores[t] += 1
    return scores.most_common(1)[0][0] if scores else "Product Quality"


# ── Main public functions ──────────────────────────────────────────────────────

def detect_themes(reviews: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Hybrid: LLM semantic clustering → map clusters → canonical themes.
    Falls back to keyword-only for tiny datasets.
    """
    low_star = filter_low_star(reviews)
    total = len(low_star) or 1
    texts = [r.get("text", "") for r in low_star]

    if len(texts) >= 5:
        n_clusters = min(8, max(3, len(texts) // 5))
        labels = _llm_cluster(texts, n_clusters=n_clusters)

        cluster_bucket: Dict[int, List[str]] = {}
        for i, label in enumerate(labels):
            cluster_bucket.setdefault(label, []).append(texts[i])

        theme_counts: Counter = Counter()
        theme_examples: Dict[str, List[str]] = {t: [] for t in THEMES}

        for _, ctexts in cluster_bucket.items():
            theme = _map_cluster_to_theme(ctexts)
            theme_counts[theme] += len(ctexts)
            for t in ctexts[:3]:
                if len(theme_examples[theme]) < 3:
                    theme_examples[theme].append(t[:150])
    else:
        theme_counts = Counter()
        theme_examples = {t: [] for t in THEMES}
        for r in low_star:
            theme = _keyword_theme(r.get("text", "")) or "Product Quality"
            theme_counts[theme] += 1
            if len(theme_examples[theme]) < 3:
                theme_examples[theme].append(r.get("text", "")[:150])

    results = []
    for theme, count in theme_counts.most_common():
        if count > 0:
            results.append({
                "theme": theme,
                "count": count,
                "pct": round(count / total * 100, 1),
                "examples": theme_examples.get(theme, []),
            })
    return results


def extract_keywords(reviews: List[Dict[str, Any]], top_n: int = 20) -> List[Dict[str, Any]]:
    """TF-IDF top keywords from 1–3 star reviews."""
    low_star = filter_low_star(reviews)
    texts = [r.get("text", "") for r in low_star]

    if len(texts) < 3:
        all_words = []
        for t in texts:
            all_words.extend(re.findall(r"\b[a-z]{4,}\b", t.lower()))
        stop = {"this","that","with","have","from","they","will","been","were",
                "your","what","when","which","there","their","about","would",
                "could","should","very","just","also"}
        return [{"keyword": k, "count": v}
                for k, v in Counter(w for w in all_words if w not in stop).most_common(top_n)]

    try:
        vec = TfidfVectorizer(max_features=200, stop_words="english",
                              ngram_range=(1, 2), min_df=2)
        tfidf = vec.fit_transform(texts)
        scores = tfidf.toarray().mean(axis=0)
        features = vec.get_feature_names_out()
        top_idx = scores.argsort()[-top_n:][::-1]
        return [{"keyword": features[i], "count": round(float(scores[i]), 4)}
                for i in top_idx]
    except Exception:
        return []


def get_cluster_summary(reviews: List[Dict[str, Any]], n_clusters: int = 5) -> List[Dict[str, Any]]:
    """
    Returns per-cluster summary for the 'LLM Clusters' section of the dashboard.
    Each entry: theme, size, pct, keywords, sample review.
    """
    low_star = filter_low_star(reviews)
    texts = [r.get("text", "") for r in low_star]
    if len(texts) < 3:
        return []

    n = min(n_clusters, len(texts))
    labels = _llm_cluster(texts, n_clusters=n)

    cluster_bucket: Dict[int, List[str]] = {}
    for i, label in enumerate(labels):
        cluster_bucket.setdefault(label, []).append(texts[i])

    summary = []
    for cid, ctexts in sorted(cluster_bucket.items(), key=lambda x: -len(x[1])):
        theme = _map_cluster_to_theme(ctexts)
        try:
            cvec = TfidfVectorizer(max_features=5, stop_words="english")
            cvec.fit_transform(ctexts)
            kws = list(cvec.vocabulary_.keys())[:5]
        except Exception:
            kws = []

        summary.append({
            "cluster_id": cid,
            "theme": theme,
            "size": len(ctexts),
            "pct": round(len(ctexts) / len(texts) * 100, 1),
            "keywords": kws,
            "sample": ctexts[0][:160] if ctexts else "",
        })
    return summary
