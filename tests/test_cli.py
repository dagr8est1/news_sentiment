from pathlib import Path

from news_sentiment.cli import build_arg_parser, run
from news_sentiment.models import Headline, ScoredHeadline


def test_parser_requires_at_least_one_ticker():
    parser = build_arg_parser()
    args = parser.parse_args(["AAPL", "MSFT"])
    assert args.tickers == ["AAPL", "MSFT"]


def test_parser_defaults():
    parser = build_arg_parser()
    args = parser.parse_args(["AAPL"])
    assert args.count == 20
    assert args.output is None


def test_parser_accepts_count_and_output():
    parser = build_arg_parser()
    args = parser.parse_args(["AAPL", "--count", "5", "--output", "out.csv"])
    assert args.count == 5
    assert args.output == "out.csv"


class _FakeNewsSource:
    def fetch(self, ticker, count):
        return [Headline(ticker=ticker, title="Great news", publisher=None, url=None, published_at=None)]


class _FakeScorer:
    def score_all(self, headlines):
        return [
            ScoredHeadline(headline=h, label="positive", confidence=0.9, sentiment_score=1)
            for h in headlines
        ]


def test_run_prints_report_and_returns_ratings(capsys):
    ratings = run(
        tickers=["AAPL"],
        count=10,
        output=None,
        news_source=_FakeNewsSource(),
        scorer=_FakeScorer(),
    )

    captured = capsys.readouterr()
    assert "AAPL" in captured.out
    assert "BUY" in captured.out
    assert ratings[0].ticker == "AAPL"


def test_run_saves_csv_when_output_given(tmp_path):
    output_path = tmp_path / "out.csv"

    run(
        tickers=["AAPL"],
        count=10,
        output=output_path,
        news_source=_FakeNewsSource(),
        scorer=_FakeScorer(),
    )

    assert output_path.exists()
