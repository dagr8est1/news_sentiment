from datetime import date

from news_sentiment.earnings import YFinanceEarningsSource, extract_next_earnings_date, is_earnings_soon


def test_extract_next_earnings_date_picks_the_earliest():
    calendar = {"Earnings Date": [date(2026, 11, 17), date(2026, 11, 18)]}
    assert extract_next_earnings_date(calendar) == date(2026, 11, 17)


def test_extract_next_earnings_date_returns_none_when_absent():
    assert extract_next_earnings_date({}) is None


def test_extract_next_earnings_date_returns_none_when_empty_list():
    assert extract_next_earnings_date({"Earnings Date": []}) is None


def test_is_earnings_soon_true_within_window():
    assert is_earnings_soon(date(2026, 11, 14), today=date(2026, 11, 7), days=7) is True


def test_is_earnings_soon_true_on_the_boundary_day():
    assert is_earnings_soon(date(2026, 11, 14), today=date(2026, 11, 7), days=7) is True
    assert is_earnings_soon(date(2026, 11, 7), today=date(2026, 11, 7), days=7) is True


def test_is_earnings_soon_false_beyond_window():
    assert is_earnings_soon(date(2026, 11, 17), today=date(2026, 11, 7), days=7) is False


def test_is_earnings_soon_false_for_a_past_date():
    assert is_earnings_soon(date(2026, 11, 1), today=date(2026, 11, 7), days=7) is False


def test_is_earnings_soon_false_when_no_date():
    assert is_earnings_soon(None, today=date(2026, 11, 7), days=7) is False


class _FakeCalendarProvider:
    def __init__(self, calendars_by_ticker):
        self._calendars_by_ticker = calendars_by_ticker

    def __call__(self, ticker):
        return self._calendars_by_ticker.get(ticker, {})


def test_yfinance_earnings_source_fetches_and_extracts():
    provider = _FakeCalendarProvider({"NVDA": {"Earnings Date": [date(2026, 11, 17)]}})
    source = YFinanceEarningsSource(calendar_provider=provider)

    assert source.fetch("NVDA") == date(2026, 11, 17)


def test_yfinance_earnings_source_returns_none_for_unknown_ticker():
    provider = _FakeCalendarProvider({})
    source = YFinanceEarningsSource(calendar_provider=provider)

    assert source.fetch("ZZZZ") is None
