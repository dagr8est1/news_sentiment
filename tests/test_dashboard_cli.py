from news_sentiment.dashboard_cli import build_arg_parser, run
from news_sentiment.models import Headline, ScoredHeadline


class _FakeNewsSource:
    def fetch(self, ticker, count):
        return [Headline(ticker=ticker, title="t", publisher=None, url=None, published_at=None)]


class _FakeScorer:
    def score_all(self, headlines):
        return [
            ScoredHeadline(headline=h, label="positive", confidence=0.9, sentiment_score=1)
            for h in headlines
        ]


def test_parser_defaults_to_the_built_in_watchlist_and_sectors():
    parser = build_arg_parser()
    args = parser.parse_args([])
    assert "AAPL" in args.watchlist
    assert "XLK" in args.sector_etfs


def test_parser_accepts_custom_watchlist_and_output():
    parser = build_arg_parser()
    args = parser.parse_args(
        ["--watchlist", "AAPL", "MSFT", "--sector-etfs", "XLK", "--output", "out.json"]
    )
    assert args.watchlist == ["AAPL", "MSFT"]
    assert args.sector_etfs == ["XLK"]
    assert args.output == "out.json"


def test_run_writes_dashboard_json(tmp_path):
    output_path = tmp_path / "dashboard-data.json"

    run(
        watchlist=["AAPL"],
        sector_etfs=["XLK"],
        count=5,
        output=output_path,
        news_source=_FakeNewsSource(),
        scorer=_FakeScorer(),
    )

    assert output_path.exists()
