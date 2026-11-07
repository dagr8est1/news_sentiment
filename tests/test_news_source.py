from news_sentiment.models import Headline
from news_sentiment.news_source import YFinanceNewsSource, parse_article


def test_parse_article_extracts_known_fields():
    raw = {
        "content": {
            "title": "Apple reports record iPhone sales",
            "pubDate": "2026-01-01T00:00:00Z",
            "provider": {"displayName": "Reuters"},
            "canonicalUrl": {"url": "https://example.com/a"},
        }
    }
    headline = parse_article("AAPL", raw)
    assert headline == Headline(
        ticker="AAPL",
        title="Apple reports record iPhone sales",
        publisher="Reuters",
        url="https://example.com/a",
        published_at="2026-01-01T00:00:00Z",
    )


def test_parse_article_returns_none_without_title():
    raw = {"content": {"title": ""}}
    assert parse_article("AAPL", raw) is None


def test_parse_article_handles_missing_optional_fields():
    raw = {"content": {"title": "Some headline"}}
    headline = parse_article("AAPL", raw)
    assert headline == Headline(
        ticker="AAPL",
        title="Some headline",
        publisher=None,
        url=None,
        published_at=None,
    )


class _FakeTicker:
    def __init__(self, raw_articles):
        self._raw_articles = raw_articles

    def get_news(self, count):
        return self._raw_articles[:count]


def test_fetch_filters_out_articles_without_titles():
    raw_articles = [
        {"content": {"title": "Good headline"}},
        {"content": {"title": ""}},
    ]
    source = YFinanceNewsSource(ticker_factory=lambda t: _FakeTicker(raw_articles))

    headlines = source.fetch("AAPL", count=5)

    assert headlines == [
        Headline(ticker="AAPL", title="Good headline", publisher=None, url=None, published_at=None)
    ]


def test_fetch_respects_count():
    raw_articles = [{"content": {"title": f"Headline {i}"}} for i in range(5)]
    captured = {}

    def ticker_factory(t):
        captured["ticker"] = t
        return _FakeTicker(raw_articles)

    source = YFinanceNewsSource(ticker_factory=ticker_factory)
    headlines = source.fetch("MSFT", count=2)

    assert len(headlines) == 2
    assert captured["ticker"] == "MSFT"
