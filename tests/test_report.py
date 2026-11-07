import csv

from news_sentiment.models import Headline, ScoredHeadline, TickerRating
from news_sentiment.report import format_report, save_csv


def _rating(ticker: str, rating: str, avg_score: float, n_headlines: int) -> TickerRating:
    headline = Headline(ticker=ticker, title="t", publisher=None, url=None, published_at=None)
    scored = [
        ScoredHeadline(headline=headline, label="positive", confidence=0.9, sentiment_score=1)
        for _ in range(n_headlines)
    ]
    return TickerRating(ticker=ticker, rating=rating, avg_score=avg_score, scored_headlines=scored)


def test_format_report_includes_ticker_rating_and_headline_count():
    ratings = [_rating("AAPL", "BUY", 0.5, 3)]
    output = format_report(ratings)

    assert "AAPL" in output
    assert "BUY" in output
    assert "0.50" in output
    assert "3" in output


def test_format_report_handles_multiple_tickers():
    ratings = [_rating("AAPL", "BUY", 0.5, 1), _rating("MSFT", "SELL", -0.6, 2)]
    output = format_report(ratings)

    assert "AAPL" in output
    assert "MSFT" in output
    assert "SELL" in output


def test_save_csv_writes_one_row_per_ticker(tmp_path):
    ratings = [_rating("AAPL", "BUY", 0.5, 2), _rating("MSFT", "HOLD", 0.0, 0)]
    path = tmp_path / "report.csv"

    save_csv(ratings, path)

    with path.open() as f:
        rows = list(csv.DictReader(f))

    assert rows == [
        {"ticker": "AAPL", "rating": "BUY", "avg_score": "0.5", "num_headlines": "2"},
        {"ticker": "MSFT", "rating": "HOLD", "avg_score": "0.0", "num_headlines": "0"},
    ]
