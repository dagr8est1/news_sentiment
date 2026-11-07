import json
from datetime import datetime, timezone
from pathlib import Path

from news_sentiment.pipeline import NewsSource, Scorer, analyze_tickers
from news_sentiment.prices import PriceSource

DEFAULT_WATCHLIST = [
    "AAPL",
    "MSFT",
    "NVDA",
    "GOOGL",
    "AMZN",
    "META",
    "AVGO",
    "TSLA",
    "BRK-B",
    "LLY",
]

COMPANY_NAMES = {
    "AAPL": "Apple",
    "MSFT": "Microsoft",
    "NVDA": "NVIDIA",
    "GOOGL": "Alphabet",
    "AMZN": "Amazon",
    "META": "Meta Platforms",
    "AVGO": "Broadcom",
    "TSLA": "Tesla",
    "BRK-B": "Berkshire Hathaway",
    "LLY": "Eli Lilly",
}

SECTOR_NAMES = {
    "XLK": "Technology",
    "XLF": "Financials",
    "XLE": "Energy",
    "XLV": "Health Care",
    "XLY": "Consumer Discretionary",
    "XLP": "Consumer Staples",
    "XLI": "Industrials",
    "XLB": "Materials",
    "XLU": "Utilities",
    "XLRE": "Real Estate",
    "XLC": "Communication Services",
}

DEFAULT_SECTOR_ETFS = list(SECTOR_NAMES)


def _price_fields(price_source: PriceSource, ticker: str) -> dict:
    p = price_source.fetch(ticker)
    return {
        "price": p.price,
        "change_1d": p.change_1d,
        "change_1w": p.change_1w,
        "change_qtd": p.change_qtd,
        "change_ytd": p.change_ytd,
    }


def build_dashboard_data(
    watchlist: list[str],
    sector_etfs: list[str],
    news_source: NewsSource,
    scorer: Scorer,
    price_source: PriceSource,
    count: int = 10,
    generated_at: str | None = None,
) -> dict:
    stock_ratings = analyze_tickers(watchlist, news_source, scorer, count=count)
    sector_ratings = analyze_tickers(sector_etfs, news_source, scorer, count=count)

    return {
        "generated_at": generated_at or datetime.now(timezone.utc).isoformat(),
        "stocks": [
            {
                "ticker": r.ticker,
                "company_name": COMPANY_NAMES.get(r.ticker, r.ticker),
                "rating": r.rating,
                "avg_score": r.avg_score,
                "num_headlines": len(r.scored_headlines),
                **_price_fields(price_source, r.ticker),
            }
            for r in stock_ratings
        ],
        "sectors": [
            {
                "ticker": r.ticker,
                "sector_name": SECTOR_NAMES[r.ticker],
                "rating": r.rating,
                "avg_score": r.avg_score,
                "num_headlines": len(r.scored_headlines),
                **_price_fields(price_source, r.ticker),
            }
            for r in sector_ratings
        ],
    }


def save_dashboard_data(data: dict, path: str | Path) -> None:
    with Path(path).open("w") as f:
        json.dump(data, f, indent=2)
