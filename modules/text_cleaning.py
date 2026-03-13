"""
text_cleaning.py
Cleans and preprocesses raw review text.
"""

import re
import string
from typing import List, Dict, Any

# Common spam patterns
SPAM_PATTERNS = [
    r"follow me", r"check my profile", r"subscribe", r"click here",
    r"buy now", r"limited offer", r"www\.", r"http", r"\.com",
    r"whatsapp", r"telegram", r"discount code",
]

def remove_emojis(text: str) -> str:
    emoji_pattern = re.compile(
        "["
        u"\U0001F600-\U0001F64F"
        u"\U0001F300-\U0001F5FF"
        u"\U0001F680-\U0001F6FF"
        u"\U0001F1E0-\U0001F1FF"
        u"\U00002702-\U000027B0"
        u"\U000024C2-\U0001F251"
        "]+", flags=re.UNICODE
    )
    return emoji_pattern.sub("", text)


def clean_text(text: str) -> str:
    if not text or not isinstance(text, str):
        return ""
    text = remove_emojis(text)
    text = re.sub(r"http\S+|www\S+", "", text)        # remove URLs
    text = re.sub(r"@\w+", "", text)                   # remove mentions
    text = re.sub(r"#\w+", "", text)                   # remove hashtags
    text = re.sub(r"\s+", " ", text)                   # normalize spaces
    text = text.strip()
    return text


def is_spam(text: str) -> bool:
    text_lower = text.lower()
    for pattern in SPAM_PATTERNS:
        if re.search(pattern, text_lower):
            return True
    return False


def is_relevant(text: str, min_words: int = 5) -> bool:
    words = text.split()
    return len(words) >= min_words


def deduplicate(reviews: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen = set()
    unique = []
    for r in reviews:
        text = r.get("text", "").strip().lower()[:100]
        if text not in seen:
            seen.add(text)
            unique.append(r)
    return unique


def preprocess_reviews(reviews: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Full cleaning pipeline."""
    cleaned = []
    for r in reviews:
        text = clean_text(r.get("text", ""))
        if not text:
            continue
        if is_spam(text):
            continue
        if not is_relevant(text):
            continue
        r["text"] = text
        cleaned.append(r)

    cleaned = deduplicate(cleaned)
    return cleaned
