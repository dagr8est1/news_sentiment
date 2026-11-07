from typing import Any, Callable

from news_sentiment.models import Headline, ScoredHeadline

FINBERT_MODEL = "ProsusAI/finbert"

_LABEL_SCORES = {"positive": 1, "neutral": 0, "negative": -1}

Classifier = Callable[[str], list[dict[str, Any]]]


def label_to_score(label: str) -> int:
    normalized = label.lower()
    if normalized not in _LABEL_SCORES:
        raise ValueError(f"Unknown sentiment label: {label!r}")
    return _LABEL_SCORES[normalized]


def _default_classifier() -> Classifier:
    from transformers import pipeline

    return pipeline("text-classification", model=FINBERT_MODEL)


class FinbertSentimentScorer:
    def __init__(self, classifier: Classifier | None = None):
        self._classifier = classifier

    def _get_classifier(self) -> Classifier:
        if self._classifier is None:
            self._classifier = _default_classifier()
        return self._classifier

    def score(self, headline: Headline) -> ScoredHeadline:
        result = self._get_classifier()(headline.title)[0]
        label = result["label"].lower()
        return ScoredHeadline(
            headline=headline,
            label=label,
            confidence=result["score"],
            sentiment_score=label_to_score(label),
        )

    def score_all(self, headlines: list[Headline]) -> list[ScoredHeadline]:
        return [self.score(headline) for headline in headlines]
