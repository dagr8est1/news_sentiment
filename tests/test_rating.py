import pytest

from news_sentiment.models import Headline, ScoredHeadline
from news_sentiment.rating import aggregate_rating, score_to_rating


def _scored(ticker: str, sentiment_score: int) -> ScoredHeadline:
    headline = Headline(ticker=ticker, title="t", publisher=None, url=None, published_at=None)
    return ScoredHeadline(headline=headline, label="x", confidence=1.0, sentiment_score=sentiment_score)


def test_score_to_rating_buy_above_threshold():
    assert score_to_rating(0.3) == "BUY"


def test_score_to_rating_sell_below_threshold():
    assert score_to_rating(-0.3) == "SELL"


def test_score_to_rating_hold_at_zero():
    assert score_to_rating(0.0) == "HOLD"


def test_score_to_rating_hold_on_boundary():
    assert score_to_rating(0.2) == "HOLD"
    assert score_to_rating(-0.2) == "HOLD"


def test_aggregate_rating_averages_scores():
    scored = [_scored("AAPL", 1), _scored("AAPL", 1), _scored("AAPL", -1)]
    result = aggregate_rating("AAPL", scored)
    assert result.ticker == "AAPL"
    assert result.avg_score == pytest.approx(1 / 3)
    assert result.rating == "BUY"
    assert result.scored_headlines == scored


def test_aggregate_rating_empty_list_is_hold():
    result = aggregate_rating("AAPL", [])
    assert result.rating == "HOLD"
    assert result.avg_score == 0.0
    assert result.scored_headlines == []
