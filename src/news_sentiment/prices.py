import math
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Callable, Protocol

HistoryProvider = Callable[[str], list[tuple[date, float]]]


class PriceSource(Protocol):
    def fetch(self, ticker: str) -> "PriceReturns":
        """Return `ticker`'s current price and 1D/1W/QTD/YTD returns."""
        ...


@dataclass(frozen=True)
class PriceReturns:
    ticker: str
    price: float
    change_1d: float | None
    change_1w: float | None
    change_qtd: float | None
    change_ytd: float | None


def _closest_close_on_or_before(closes: list[tuple[date, float]], target: date) -> float | None:
    """Return the latest close on or before `target`, or None if history doesn't reach back that far."""
    result = None
    for d, close in closes:
        if d <= target:
            result = close
        else:
            break
    return result


def _quarter_start(d: date) -> date:
    """Return the first day of the calendar quarter containing `d`."""
    quarter_start_month = 3 * ((d.month - 1) // 3) + 1
    return date(d.year, quarter_start_month, 1)


def compute_returns(ticker: str, closes: list[tuple[date, float]]) -> PriceReturns:
    """Compute current price and 1D/1W/QTD/YTD returns from ascending (date, close) pairs."""
    # yfinance occasionally reports a NaN close for a day (e.g. a still-settling
    # intraday row), which would otherwise poison every return calculated off it.
    closes = [(d, c) for d, c in closes if not math.isnan(c)]

    if not closes:
        return PriceReturns(
            ticker=ticker, price=0.0, change_1d=None, change_1w=None, change_qtd=None, change_ytd=None
        )

    current_date, price = closes[-1]
    history = closes[:-1]

    def pct_change(baseline: float | None) -> float | None:
        """Percentage change from `baseline` to the current price, or None if no baseline."""
        if not baseline:
            return None
        return (price - baseline) / baseline

    change_1d = pct_change(history[-1][1]) if history else None
    change_1w = pct_change(_closest_close_on_or_before(history, current_date - timedelta(days=7)))
    change_qtd = pct_change(
        _closest_close_on_or_before(history, _quarter_start(current_date) - timedelta(days=1))
    )
    change_ytd = pct_change(
        _closest_close_on_or_before(history, date(current_date.year, 1, 1) - timedelta(days=1))
    )

    return PriceReturns(
        ticker=ticker,
        price=price,
        change_1d=change_1d,
        change_1w=change_1w,
        change_qtd=change_qtd,
        change_ytd=change_ytd,
    )


def _default_history_provider(ticker: str) -> list[tuple[date, float]]:
    """Pull ~2 years of daily closes for `ticker` from yfinance."""
    import yfinance as yf

    hist = yf.Ticker(ticker).history(period="2y")
    return [(ts.date(), float(close)) for ts, close in hist["Close"].items()]


class YFinancePriceSource:
    """Fetches price history from Yahoo Finance and computes a ticker's returns."""

    def __init__(self, history_provider: HistoryProvider | None = None):
        """Accept an optional fake history provider for testing without network access."""
        self._history_provider = history_provider or _default_history_provider

    def fetch(self, ticker: str) -> PriceReturns:
        """Fetch `ticker`'s price history and compute its current price and returns."""
        closes = self._history_provider(ticker)
        return compute_returns(ticker, closes)
