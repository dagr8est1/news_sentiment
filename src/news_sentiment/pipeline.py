from typing import Protocol

from news_sentiment.models import Headline, ScoredHeadline, TickerRating
from news_sentiment.rating import aggregate_rating


class NewsSource(Protocol):
    def fetch(self, ticker: str, count: int) -> list[Headline]:
        """Return up to `count` recent headlines for `ticker`."""
        ...


class Scorer(Protocol):
    def score_all(self, headlines: list[Headline]) -> list[ScoredHeadline]:
        """Score each headline's sentiment, preserving order."""
        ...


def analyze_ticker(ticker: str, news_source: NewsSource, scorer: Scorer, count: int = 20) -> TickerRating:
    """Fetch a ticker's headlines, score them, and aggregate into one TickerRating."""
    headlines = news_source.fetch(ticker, count)
    scored_headlines = scorer.score_all(headlines)
    return aggregate_rating(ticker, scored_headlines)


def analyze_tickers(
    tickers: list[str], news_source: NewsSource, scorer: Scorer, count: int = 20
) -> list[TickerRating]:
    """Run analyze_ticker for each ticker with a single scorer."""
    return [analyze_ticker(ticker, news_source, scorer, count) for ticker in tickers]


def analyze_tickers_multi(
    tickers: list[str], news_source: NewsSource, scorers: dict[str, Scorer], count: int = 20
) -> dict[str, dict[str, TickerRating]]:
    """Fetch each ticker's headlines once and score them independently with every scorer.

    Returns results[ticker][scorer_name] -> TickerRating, so each model's
    rating stays separate instead of being blended together.
    """
    results: dict[str, dict[str, TickerRating]] = {}
    for ticker in tickers:
        headlines = news_source.fetch(ticker, count)
        results[ticker] = {
            name: aggregate_rating(ticker, scorer.score_all(headlines)) for name, scorer in scorers.items()
        }
    return results
