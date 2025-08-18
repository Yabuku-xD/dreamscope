from __future__ import annotations

from typing import Dict, List, Tuple

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from nrclex import NRCLex
import yake


_analyzer = SentimentIntensityAnalyzer()
_kw_extractor = yake.KeywordExtractor(lan="en", n=1, top=10)

# Simple keyword-to-theme mapping; extend as needed
THEME_TAXONOMY = {
    "chase": "anxiety",
    "fall": "anxiety",
    "test": "performance",
    "exam": "performance",
    "flying": "freedom",
    "water": "emotion",
    "ocean": "emotion",
    "death": "mortality",
    "snake": "fear",
    "teeth": "appearance",
    "naked": "vulnerability",
    "lost": "disorientation",
    "late": "time_pressure",
    "fire": "danger",
}


def extract_keywords(text: str) -> List[Tuple[str, float]]:
    if not text:
        return []
    try:
        return _kw_extractor.extract_keywords(text)
    except Exception:
        return []


def analyze_text(text: str) -> Dict:
    if not text:
        return {
            "sentiment": {"compound": 0.0},
            "emotions": {},
            "keywords": [],
            "themes": [],
        }

    sentiment = _analyzer.polarity_scores(text)

    # NRCLex returns list of (emotion, score)
    try:
        emo = NRCLex(text)
        emotions = emo.raw_emotion_scores or {}
    except Exception:
        emotions = {}

    keywords = extract_keywords(text)

    # Theme tagging based on keyword stems present in text
    text_lower = text.lower()
    themes = []
    for k, theme in THEME_TAXONOMY.items():
        if k in text_lower and theme not in themes:
            themes.append(theme)

    return {
        "sentiment": sentiment,
        "emotions": emotions,
        "keywords": keywords,
        "themes": themes,
    }
