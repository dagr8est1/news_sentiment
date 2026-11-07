from typing import Protocol

from news_sentiment.models import Headline, ScoredHeadline, TickerRating
from news_sentiment.rating import aggregate_rating


class NewsSource(Protocol):
    def fetch(self, ticker: str, count: int) -> list[Headline]: ...


class Scorer(Protocol):
    def score_all(self, headlines: list[Headline]) -> list[ScoredHeadline]: ...


def analyze_ticker(ticker: str, news_source: NewsSource, scorer: Scorer, count: int = 20) -> TickerRating:
    headlines = news_source.fetch(ticker, count)
    scored_headlines = scorer.score_all(headlines)
    return aggregate_rating(ticker, scored_headlines)


def analyze_tickers(
    tickers: list[str], news_source: NewsSource, scorer: Scorer, count: int = 20
) -> list[TickerRating]:
    return [analyze_ticker(ticker, news_source, scorer, count) for ticker in tickers]


def analyze_tickers_multi(
    tickers: list[str], news_source: NewsSource, scorers: dict[str, Scorer], count: int = 20
) -> dict[str, dict[str, TickerRating]]:
    results: dict[str, dict[str, TickerRating]] = {}
    for ticker in tickers:
        headlines = news_source.fetch(ticker, count)
        results[ticker] = {
            name: aggregate_rating(ticker, scorer.score_all(headlines)) for name, scorer in scorers.items()
        }
    return results
