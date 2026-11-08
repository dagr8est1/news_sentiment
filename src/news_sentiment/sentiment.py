from typing import Any, Callable

from news_sentiment.models import Headline, ScoredHeadline

FINBERT_MODEL = "ProsusAI/finbert"
QWEN_MODEL = "Qwen/Qwen2.5-0.5B-Instruct"

_LABEL_SCORES = {"positive": 1, "neutral": 0, "negative": -1}

Classifier = Callable[[str], list[dict[str, Any]]]
Generator = Callable[[str], str]

def label_to_score(label: str) -> int:
    """Map a positive/neutral/negative label (case-insensitive) to +1/0/-1."""
    normalized = label.lower()
    if normalized not in _LABEL_SCORES:
        raise ValueError(f"Unknown sentiment label: {label!r}")
    return _LABEL_SCORES[normalized]


def _default_classifier() -> Classifier:
    """Load the real FinBERT text-classification pipeline (lazy, first use only)."""
    from transformers import pipeline

    return pipeline("text-classification", model=FINBERT_MODEL)


class FinbertSentimentScorer:
    """Scores headlines with FinBERT, a classifier that returns a label directly."""

    def __init__(self, classifier: Classifier | None = None):
        """Accept an optional fake classifier for testing without loading the real model."""
        self._classifier = classifier

    def _get_classifier(self) -> Classifier:
        """Return the injected classifier, or lazily load the real FinBERT model."""
        if self._classifier is None:
            self._classifier = _default_classifier()
        return self._classifier

    def score(self, headline: Headline) -> ScoredHeadline:
        """Classify one headline's sentiment with FinBERT."""
        result = self._get_classifier()(headline.title)[0]
        label = result["label"].lower()
        return ScoredHeadline(
            headline=headline,
            label=label,
            confidence=result["score"],
            sentiment_score=label_to_score(label),
        )

    def score_all(self, headlines: list[Headline]) -> list[ScoredHeadline]:
        """Classify a list of headlines, preserving order."""
        return [self.score(headline) for headline in headlines]


def build_sentiment_prompt(headline: Headline) -> str:
    """Build the prompt asking an LLM to classify one headline's sentiment."""
    return (
        f"You are a financial news analyst. Classify the sentiment of this headline "
        f"for {headline.ticker} as Positive, Negative, or Neutral.\n\n"
        f"Headline: {headline.title}\n\n"
        f"Respond with exactly one word: Positive, Negative, or Neutral."
    )


def parse_llm_sentiment_label(text: str) -> str:
    """Find whichever sentiment label word appears earliest in an LLM's free-text reply."""
    text_lower = text.lower()
    positions = {label: text_lower.find(label) for label in _LABEL_SCORES}
    found = {label: pos for label, pos in positions.items() if pos != -1}
    if not found:
        raise ValueError(f"Could not parse a sentiment label from LLM output: {text!r}")
    return min(found, key=found.get)


def _default_generator() -> Generator:
    """Load the real Qwen text-generation pipeline and wrap it as a prompt -> text function."""
    from transformers import pipeline

    text_generator = pipeline("text-generation", model=QWEN_MODEL, max_new_tokens=20)

    def generate(prompt: str) -> str:
        """Run the prompt through Qwen's chat template and return the assistant's reply text."""
        output = text_generator([{"role": "user", "content": prompt}])
        return output[0]["generated_text"][-1]["content"]

    return generate


class QwenSentimentScorer:
    """Scores headlines with Qwen, an LLM prompted per headline and parsed for a label."""

    def __init__(self, generator: Generator | None = None):
        """Accept an optional fake generator for testing without loading the real model."""
        self._generator = generator

    def _get_generator(self) -> Generator:
        """Return the injected generator, or lazily load the real Qwen model."""
        if self._generator is None:
            self._generator = _default_generator()
        return self._generator

    def score(self, headline: Headline) -> ScoredHeadline:
        """Prompt the LLM about one headline and parse its reply into a ScoredHeadline."""
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
        """Prompt the LLM about each headline, preserving order."""
        return [self.score(headline) for headline in headlines]
