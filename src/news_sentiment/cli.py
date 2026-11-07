import argparse
from pathlib import Path

from news_sentiment.models import TickerRating
from news_sentiment.news_source import YFinanceNewsSource
from news_sentiment.pipeline import NewsSource, Scorer, analyze_tickers, analyze_tickers_multi
from news_sentiment.report import (
    format_comparison,
    format_comparison_headlines,
    format_headlines,
    format_report,
    save_comparison_csv,
    save_csv,
)
from news_sentiment.sentiment import FinbertSentimentScorer, QwenSentimentScorer


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
    parser.add_argument(
        "--compare",
        action="store_true",
        help="Score headlines with both FinBERT and Qwen and compare their ratings side by side",
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


def run_compare(
    tickers: list[str],
    count: int,
    output: str | Path | None,
    news_source: NewsSource,
    scorers: dict[str, Scorer],
    verbose: bool = False,
) -> dict[str, dict[str, TickerRating]]:
    results = analyze_tickers_multi(tickers, news_source, scorers, count=count)
    print(format_comparison(results))
    if verbose:
        print()
        print(format_comparison_headlines(results))
    if output is not None:
        save_comparison_csv(results, Path(output))
    return results


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    if args.compare:
        run_compare(
            tickers=args.tickers,
            count=args.count,
            output=args.output,
            news_source=YFinanceNewsSource(),
            scorers={"finbert": FinbertSentimentScorer(), "qwen": QwenSentimentScorer()},
            verbose=args.verbose,
        )
    else:
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
