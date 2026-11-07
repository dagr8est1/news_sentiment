import json

from news_sentiment.dashboard import (
    COMPANY_NAMES,
    DEFAULT_SECTOR_ETFS,
    DEFAULT_WATCHLIST,
    SECTOR_NAMES,
    build_dashboard_data,
    save_dashboard_data,
)
from news_sentiment.models import Headline, ScoredHeadline
from news_sentiment.prices import PriceReturns


class _FakeNewsSource:
    def __init__(self, headlines_by_ticker):
        self._headlines_by_ticker = headlines_by_ticker

    def fetch(self, ticker, count):
        return self._headlines_by_ticker.get(ticker, [])


class _FakeScorer:
    def __init__(self, sentiment_score=1, label="positive"):
        self._sentiment_score = sentiment_score
        self._label = label

    def score_all(self, headlines):
        return [
            ScoredHeadline(
                headline=h, label=self._label, confidence=0.9, sentiment_score=self._sentiment_score
            )
            for h in headlines
        ]


class _FakePriceSource:
    def fetch(self, ticker):
        return PriceReturns(
            ticker=ticker, price=100.0, change_1d=0.01, change_1w=0.02, change_qtd=0.03, change_ytd=0.04
        )


def _headline(ticker: str) -> Headline:
    return Headline(ticker=ticker, title="t", publisher=None, url=None, published_at=None)


def test_default_watchlist_has_ten_tickers():
    assert len(DEFAULT_WATCHLIST) == 10
    assert len(set(DEFAULT_WATCHLIST)) == 10


def test_default_sector_etfs_cover_all_eleven_spdr_sectors():
    assert len(DEFAULT_SECTOR_ETFS) == 11
    assert set(DEFAULT_SECTOR_ETFS) == set(SECTOR_NAMES)


def test_build_dashboard_data_includes_generated_at():
    news_source = _FakeNewsSource({})
    scorer = _FakeScorer()

    data = build_dashboard_data(
        [], [], news_source, scorer, _FakePriceSource(), generated_at="2026-11-07T00:00:00+00:00"
    )

    assert data["generated_at"] == "2026-11-07T00:00:00+00:00"


def test_build_dashboard_data_scores_each_watchlist_stock():
    news_source = _FakeNewsSource({"AAPL": [_headline("AAPL")], "MSFT": [_headline("MSFT")]})
    scorer = _FakeScorer(sentiment_score=1)

    data = build_dashboard_data(
        ["AAPL", "MSFT"],
        [],
        news_source,
        scorer,
        _FakePriceSource(),
        generated_at="2026-11-07T00:00:00+00:00",
    )

    assert data["stocks"] == [
        {
            "ticker": "AAPL",
            "company_name": COMPANY_NAMES["AAPL"],
            "rating": "BUY",
            "avg_score": 1.0,
            "num_headlines": 1,
            "price": 100.0,
            "change_1d": 0.01,
            "change_1w": 0.02,
            "change_qtd": 0.03,
            "change_ytd": 0.04,
        },
        {
            "ticker": "MSFT",
            "company_name": COMPANY_NAMES["MSFT"],
            "rating": "BUY",
            "avg_score": 1.0,
            "num_headlines": 1,
            "price": 100.0,
            "change_1d": 0.01,
            "change_1w": 0.02,
            "change_qtd": 0.03,
            "change_ytd": 0.04,
        },
    ]


def test_build_dashboard_data_falls_back_to_ticker_for_unknown_company_name():
    news_source = _FakeNewsSource({"ZZZZ": [_headline("ZZZZ")]})
    scorer = _FakeScorer(sentiment_score=1)

    data = build_dashboard_data(
        ["ZZZZ"], [], news_source, scorer, _FakePriceSource(), generated_at="2026-11-07T00:00:00+00:00"
    )

    assert data["stocks"][0]["company_name"] == "ZZZZ"


def test_build_dashboard_data_scores_each_sector_etf_with_its_name():
    news_source = _FakeNewsSource({"XLK": [_headline("XLK")]})
    scorer = _FakeScorer(sentiment_score=-1)

    data = build_dashboard_data(
        [], ["XLK"], news_source, scorer, _FakePriceSource(), generated_at="2026-11-07T00:00:00+00:00"
    )

    assert data["sectors"] == [
        {
            "ticker": "XLK",
            "sector_name": SECTOR_NAMES["XLK"],
            "rating": "SELL",
            "avg_score": -1.0,
            "num_headlines": 1,
            "price": 100.0,
            "change_1d": 0.01,
            "change_1w": 0.02,
            "change_qtd": 0.03,
            "change_ytd": 0.04,
        }
    ]


def test_save_dashboard_data_writes_readable_json(tmp_path):
    data = {"generated_at": "2026-11-07T00:00:00+00:00", "stocks": [], "sectors": []}
    path = tmp_path / "dashboard-data.json"

    save_dashboard_data(data, path)

    with path.open() as f:
        assert json.load(f) == data
