import pytest

from news_sentiment.models import Headline
from news_sentiment.sentiment import FinbertSentimentScorer, label_to_score


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
