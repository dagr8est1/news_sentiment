import argparse
from pathlib import Path

from news_sentiment.dashboard import DEFAULT_SECTOR_ETFS, DEFAULT_WATCHLIST, build_dashboard_data, save_dashboard_data
from news_sentiment.news_source import YFinanceNewsSource
from news_sentiment.pipeline import NewsSource, Scorer
from news_sentiment.sentiment import FinbertSentimentScorer


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="news-sentiment-dashboard",
        description="Score a watchlist and sector ETFs with FinBERT and write a dashboard-data.json file.",
    )
    parser.add_argument(
        "--watchlist", nargs="+", default=DEFAULT_WATCHLIST, help="Stock tickers to include (default: built-in top-10 watchlist)"
    )
    parser.add_argument(
        "--sector-etfs",
        nargs="+",
        default=DEFAULT_SECTOR_ETFS,
        help="Sector ETF tickers to include (default: the 11 SPDR sector ETFs)",
    )
    parser.add_argument("--count", type=int, default=10, help="Headlines to fetch per ticker (default: 10)")
    parser.add_argument(
        "--output", default="docs/dashboard-data.json", help="Where to write the dashboard JSON"
    )
    return parser


def run(
    watchlist: list[str],
    sector_etfs: list[str],
    count: int,
    output: str | Path,
    news_source: NewsSource,
    scorer: Scorer,
) -> dict:
    data = build_dashboard_data(watchlist, sector_etfs, news_source, scorer, count=count)
    save_dashboard_data(data, output)
    return data


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    data = run(
        watchlist=args.watchlist,
        sector_etfs=args.sector_etfs,
        count=args.count,
        output=args.output,
        news_source=YFinanceNewsSource(),
        scorer=FinbertSentimentScorer(),
    )
    print(f"Wrote {len(data['stocks'])} stocks and {len(data['sectors'])} sector ETFs to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
