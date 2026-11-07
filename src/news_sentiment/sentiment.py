from typing import Any, Callable

from news_sentiment.models import Headline, ScoredHeadline

FINBERT_MODEL = "ProsusAI/finbert"
QWEN_MODEL = "Qwen/Qwen2.5-0.5B-Instruct"

_LABEL_SCORES = {"positive": 1, "neutral": 0, "negative": -1}

Classifier = Callable[[str], list[dict[str, Any]]]
Generator = Callable[[str], str]


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


def build_sentiment_prompt(headline: Headline) -> str:
    return (
        f"You are a financial news analyst. Classify the sentiment of this headline "
        f"for {headline.ticker} as Positive, Negative, or Neutral.\n\n"
        f"Headline: {headline.title}\n\n"
        f"Respond with exactly one word: Positive, Negative, or Neutral."
    )


def parse_llm_sentiment_label(text: str) -> str:
    text_lower = text.lower()
    positions = {label: text_lower.find(label) for label in _LABEL_SCORES}
    found = {label: pos for label, pos in positions.items() if pos != -1}
    if not found:
        raise ValueError(f"Could not parse a sentiment label from LLM output: {text!r}")
    return min(found, key=found.get)


def _default_generator() -> Generator:
    from transformers import pipeline

    text_generator = pipeline("text-generation", model=QWEN_MODEL, max_new_tokens=20)

    def generate(prompt: str) -> str:
        output = text_generator([{"role": "user", "content": prompt}])
        return output[0]["generated_text"][-1]["content"]

    return generate


class QwenSentimentScorer:
    def __init__(self, generator: Generator | None = None):
        self._generator = generator

    def _get_generator(self) -> Generator:
        if self._generator is None:
            self._generator = _default_generator()
        return self._generator

    def score(self, headline: Headline) -> ScoredHeadline:
        raw_output = self._get_generator()(build_sentiment_prompt(headline))
        label = parse_llm_sentiment_label(raw_output)
        return ScoredHeadline(
            headline=headline,
            label=label,
            # Generative models don't expose a calibrated class probability like
            # the FinBERT classification pipeline does, so confidence is fixed.
            confidence=1.0,
            sentiment_score=label_to_score(label),
        )

    def score_all(self, headlines: list[Headline]) -> list[ScoredHeadline]:
        return [self.score(headline) for headline in headlines]
