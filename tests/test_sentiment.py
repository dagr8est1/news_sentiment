import pytest

from news_sentiment.models import Headline
from news_sentiment.sentiment import (
    FinbertSentimentScorer,
    QwenSentimentScorer,
    build_sentiment_prompt,
    label_to_score,
    parse_llm_sentiment_label,
)


def test_label_to_score_positive():
    assert label_to_score("positive") == 1


def test_label_to_score_negative():
    assert label_to_score("negative") == -1


def test_label_to_score_neutral():
    assert label_to_score("neutral") == 0


def test_label_to_score_is_case_insensitive():
    assert label_to_score("POSITIVE") == 1


def test_label_to_score_rejects_unknown_label():
    with pytest.raises(ValueError):
        label_to_score("bullish")


def _headline(title: str) -> Headline:
    return Headline(ticker="AAPL", title=title, publisher=None, url=None, published_at=None)


def test_scorer_scores_a_single_headline_using_injected_classifier():
    def fake_classifier(title):
        assert title == "Apple beats earnings"
        return [{"label": "positive", "score": 0.91}]

    scorer = FinbertSentimentScorer(classifier=fake_classifier)
    result = scorer.score(_headline("Apple beats earnings"))

    assert result.headline.title == "Apple beats earnings"
    assert result.label == "positive"
    assert result.confidence == 0.91
    assert result.sentiment_score == 1


def test_scorer_scores_all_headlines_in_order():
    def fake_classifier(title):
        return [{"label": "negative", "score": 0.5}]

    scorer = FinbertSentimentScorer(classifier=fake_classifier)
    headlines = [_headline("A"), _headline("B")]

    results = scorer.score_all(headlines)

    assert [r.headline.title for r in results] == ["A", "B"]
    assert all(r.sentiment_score == -1 for r in results)


def test_build_sentiment_prompt_includes_ticker_and_title():
    prompt = build_sentiment_prompt(_headline("Apple beats earnings"))
    assert "AAPL" in prompt
    assert "Apple beats earnings" in prompt


def test_parse_llm_sentiment_label_finds_labeled_output():
    assert parse_llm_sentiment_label("Sentiment: Positive\nRating: Buy") == "positive"


def test_parse_llm_sentiment_label_is_case_insensitive():
    assert parse_llm_sentiment_label("NEGATIVE, because sales dropped") == "negative"


def test_parse_llm_sentiment_label_picks_earliest_match():
    assert parse_llm_sentiment_label("This seems neutral, not positive or negative") == "neutral"


def test_parse_llm_sentiment_label_raises_when_no_label_present():
    with pytest.raises(ValueError):
        parse_llm_sentiment_label("This looks bullish to me")


def test_qwen_scorer_scores_a_single_headline_using_injected_generator():
    def fake_generator(prompt):
        assert "Apple beats earnings" in prompt
        return "Sentiment: Positive"

    scorer = QwenSentimentScorer(generator=fake_generator)
    result = scorer.score(_headline("Apple beats earnings"))

    assert result.headline.title == "Apple beats earnings"
    assert result.label == "positive"
    assert result.sentiment_score == 1


def test_qwen_scorer_scores_all_headlines_in_order():
    def fake_generator(prompt):
        return "Negative"

    scorer = QwenSentimentScorer(generator=fake_generator)
    headlines = [_headline("A"), _headline("B")]

    results = scorer.score_all(headlines)

    assert [r.headline.title for r in results] == ["A", "B"]
    assert all(r.sentiment_score == -1 for r in results)
