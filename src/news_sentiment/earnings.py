from datetime import date, timedelta
from typing import Callable, Protocol

CalendarProvider = Callable[[str], dict]


class EarningsSource(Protocol):
    def fetch(self, ticker: str) -> date | None:
        """Return `ticker`'s next earnings date, or None if unknown."""
        ...


def extract_next_earnings_date(calendar: dict) -> date | None:
    """Pull the nearest upcoming earnings date out of a yfinance calendar dict."""
    dates = calendar.get("Earnings Date")
    if not dates:
        return None
    return min(dates)


def is_earnings_soon(earnings_date: date | None, today: date, days: int = 7) -> bool:
    """True if `earnings_date` falls within the next `days` days from `today` (inclusive)."""
    if earnings_date is None:
        return False
    return today <= earnings_date <= today + timedelta(days=days)


def _default_calendar_provider(ticker: str) -> dict:
    """Fetch the real yfinance calendar dict for `ticker`."""
    import yfinance as yf

    return yf.Ticker(ticker).calendar or {}


class YFinanceEarningsSource:
    """Fetches each ticker's next earnings date from Yahoo Finance via yfinance."""

    def __init__(self, calendar_provider: CalendarProvider | None = None):
        self._calendar_provider = calendar_provider or _default_calendar_provider

    def fetch(self, ticker: str) -> date | None:
        """Fetch `ticker`'s calendar and extract its next earnings date."""
        calendar = self._calendar_provider(ticker)
        return extract_next_earnings_date(calendar)
