from news_sentiment.models import Headline, ScoredHeadline
from news_sentiment.pipeline import analyze_ticker, analyze_tickers


class _FakeNewsSource:
    def __init__(self, headlines_by_ticker):
        self._headlines_by_ticker = headlines_by_ticker
        self.requested_counts = {}

    def fetch(self, ticker, count):
        self.requested_counts[ticker] = count
        return self._headlines_by_ticker[ticker]


class _FakeScorer:
    def score_all(self, headlines):
        return [
            ScoredHeadline(headline=h, label="positive", confidence=0.9, sentiment_score=1)
            for h in headlines
        ]


def _headline(ticker: str, title: str) -> Headline:
    return Headline(ticker=ticker, title=title, publisher=None, url=None, published_at=None)


def test_analyze_ticker_fetches_scores_and_aggregates():
    headlines = [_headline("AAPL", "Good news")]
    news_source = _FakeNewsSource({"AAPL": headlines})
    scorer = _FakeScorer()

    result = analyze_ticker("AAPL", news_source, scorer, count=10)

    assert result.ticker == "AAPL"
    assert result.rating == "BUY"
    assert news_source.requested_counts["AAPL"] == 10


def test_analyze_tickers_processes_each_ticker():
    news_source = _FakeNewsSource(
        {
            "AAPL": [_headline("AAPL", "Good news")],
            "MSFT": [_headline("MSFT", "Also good")],
        }
    )
    scorer = _FakeScorer()

    results = analyze_tickers(["AAPL", "MSFT"], news_source, scorer, count=5)

    assert [r.ticker for r in results] == ["AAPL", "MSFT"]
    assert all(r.rating == "BUY" for r in results)
