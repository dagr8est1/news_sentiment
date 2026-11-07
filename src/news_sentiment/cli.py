import argparse
from pathlib import Path

from news_sentiment.models import TickerRating
from news_sentiment.news_source import YFinanceNewsSource
from news_sentiment.pipeline import NewsSource, Scorer, analyze_tickers
from news_sentiment.report import format_headlines, format_report, save_csv
from news_sentiment.sentiment import FinbertSentimentScorer


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="news-sentiment",
        description="Fetch financial news headlines and rate tickers BUY/HOLD/SELL using FinBERT sentiment.",
    )
    parser.add_argument("tickers", nargs="+", help="One or more ticker symbols, e.g. AAPL MSFT")
    parser.add_argument("--count", type=int, default=20, help="Headlines to fetch per ticker (default: 20)")
    parser.add_argument("--output", default=None, help="Optional path to save results as CSV")
    parser.add_argument(
        "--verbose", action="store_true", help="Also print each headline with its sentiment label"
    )
    return parser


def run(
    tickers: list[str],
    count: int,
    output: str | Path | None,
    news_source: NewsSource,
    scorer: Scorer,
    verbose: bool = False,
) -> list[TickerRating]:
    ratings = analyze_tickers(tickers, news_source, scorer, count=count)
    print(format_report(ratings))
    if verbose:
        print()
        print(format_headlines(ratings))
    if output is not None:
        save_csv(ratings, Path(output))
    return ratings


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    run(
        tickers=args.tickers,
        count=args.count,
        output=args.output,
        news_source=YFinanceNewsSource(),
        scorer=FinbertSentimentScorer(),
        verbose=args.verbose,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
