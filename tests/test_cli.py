from pathlib import Path

from news_sentiment.cli import build_arg_parser, run, run_compare
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


def test_parser_verbose_defaults_to_false():
    parser = build_arg_parser()
    args = parser.parse_args(["AAPL"])
    assert args.verbose is False


def test_parser_accepts_verbose_flag():
    parser = build_arg_parser()
    args = parser.parse_args(["AAPL", "--verbose"])
    assert args.verbose is True


def test_parser_compare_defaults_to_false():
    parser = build_arg_parser()
    args = parser.parse_args(["AAPL"])
    assert args.compare is False


def test_parser_accepts_compare_flag():
    parser = build_arg_parser()
    args = parser.parse_args(["AAPL", "--compare"])
    assert args.compare is True


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


def test_run_omits_headlines_by_default(capsys):
    run(
        tickers=["AAPL"],
        count=10,
        output=None,
        news_source=_FakeNewsSource(),
        scorer=_FakeScorer(),
    )

    captured = capsys.readouterr()
    assert "Great news" not in captured.out


def test_run_prints_headlines_when_verbose(capsys):
    run(
        tickers=["AAPL"],
        count=10,
        output=None,
        news_source=_FakeNewsSource(),
        scorer=_FakeScorer(),
        verbose=True,
    )

    captured = capsys.readouterr()
    assert "Great news" in captured.out


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


class _FakeNegativeScorer:
    def score_all(self, headlines):
        return [
            ScoredHeadline(headline=h, label="negative", confidence=0.9, sentiment_score=-1)
            for h in headlines
        ]


def test_run_compare_prints_both_models_ratings(capsys):
    results = run_compare(
        tickers=["AAPL"],
        count=10,
        output=None,
        news_source=_FakeNewsSource(),
        scorers={"finbert": _FakeScorer(), "qwen": _FakeNegativeScorer()},
    )

    captured = capsys.readouterr()
    assert "BUY" in captured.out
    assert "SELL" in captured.out
    assert results["AAPL"]["finbert"].rating == "BUY"
    assert results["AAPL"]["qwen"].rating == "SELL"


def test_run_compare_prints_headlines_when_verbose(capsys):
    run_compare(
        tickers=["AAPL"],
        count=10,
        output=None,
        news_source=_FakeNewsSource(),
        scorers={"finbert": _FakeScorer(), "qwen": _FakeNegativeScorer()},
        verbose=True,
    )

    captured = capsys.readouterr()
    assert "Great news" in captured.out
    assert "finbert=positive" in captured.out
    assert "qwen=negative" in captured.out


def test_run_compare_saves_csv_when_output_given(tmp_path):
    output_path = tmp_path / "compare.csv"

    run_compare(
        tickers=["AAPL"],
        count=10,
        output=output_path,
        news_source=_FakeNewsSource(),
        scorers={"finbert": _FakeScorer(), "qwen": _FakeNegativeScorer()},
    )

    assert output_path.exists()
