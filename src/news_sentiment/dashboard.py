import json
import math
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from news_sentiment.earnings import EarningsSource, is_earnings_soon
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
    "JPM",
    "WMT",
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
    "JPM": "JPMorgan Chase",
    "WMT": "Walmart",
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
    """Fetch a ticker's price/returns and shape them as dashboard JSON fields."""
    p = price_source.fetch(ticker)
    return {
        "price": p.price,
        "change_1d": p.change_1d,
        "change_1w": p.change_1w,
        "change_qtd": p.change_qtd,
        "change_ytd": p.change_ytd,
    }


EARNINGS_SOON_DAYS = 14


def _earnings_fields(earnings_source: EarningsSource, ticker: str, today: date) -> dict:
    """Fetch a ticker's next earnings date and flag whether it's within the next 2 weeks."""
    earnings_date = earnings_source.fetch(ticker)
    return {
        "earnings_date": earnings_date.isoformat() if earnings_date else None,
        "earnings_soon": is_earnings_soon(earnings_date, today, days=EARNINGS_SOON_DAYS),
    }


def build_dashboard_data(
    watchlist: list[str],
    sector_etfs: list[str],
    news_source: NewsSource,
    scorer: Scorer,
    price_source: PriceSource,
    earnings_source: EarningsSource,
    count: int = 10,
    generated_at: str | None = None,
    today: date | None = None,
) -> dict:
    """Score the watchlist and sector ETFs and build the dashboard's JSON payload."""
    today = today or date.today()
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
                **_earnings_fields(earnings_source, r.ticker, today),
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


def _json_safe(value: Any) -> Any:
    """Replace NaN/Infinity floats with None so the output is valid (spec-compliant) JSON."""
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, dict):
        return {k: _json_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_json_safe(v) for v in value]
    return value


def save_dashboard_data(data: dict, path: str | Path) -> None:
    """Write the dashboard payload to `path` as indented, spec-compliant JSON."""
    with Path(path).open("w") as f:
        json.dump(_json_safe(data), f, indent=2)
