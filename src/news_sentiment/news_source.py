from typing import Any, Callable, Protocol

from news_sentiment.models import Headline


class _YFTicker(Protocol):
    def get_news(self, count: int) -> list[dict[str, Any]]:
        """Return up to `count` raw yfinance article dicts."""
        ...


def _default_ticker_factory(ticker: str) -> _YFTicker:
    """Build the real yfinance Ticker used when no fake is injected."""
    import yfinance as yf

    return yf.Ticker(ticker)


def parse_article(ticker: str, raw: dict[str, Any]) -> Headline | None:
    """Parse one raw yfinance article into a Headline, or None if it has no title."""
    content = raw.get("content", {})
    title = content.get("title", "")
    if not title:
        return None

    provider = content.get("provider") or {}
    canonical_url = content.get("canonicalUrl") or {}

    return Headline(
        ticker=ticker,
        title=title,
        publisher=provider.get("displayName"),
        url=canonical_url.get("url"),
        published_at=content.get("pubDate"),
    )


class YFinanceNewsSource:
    """Fetches recent headlines for a ticker from Yahoo Finance via yfinance."""

    def __init__(self, ticker_factory: Callable[[str], _YFTicker] = _default_ticker_factory):
        """Accept an optional fake ticker factory for testing without network access."""
        self._ticker_factory = ticker_factory

    def fetch(self, ticker: str, count: int = 20) -> list[Headline]:
        """Fetch up to `count` recent headlines for `ticker`, dropping titleless articles."""
        raw_articles = self._ticker_factory(ticker).get_news(count)
        headlines = (parse_article(ticker, raw) for raw in raw_articles)
        return [headline for headline in headlines if headline is not None]
