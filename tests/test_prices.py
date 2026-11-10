from datetime import date

import pytest

from news_sentiment.prices import PriceReturns, YFinancePriceSource, compute_returns


def test_compute_returns_handles_empty_history():
    result = compute_returns("AAPL", [])
    assert result == PriceReturns(
        ticker="AAPL", price=0.0, change_1d=None, change_1w=None, change_qtd=None, change_ytd=None
    )


def test_compute_returns_uses_latest_close_as_price():
    closes = [(date(2026, 11, 5), 100.0), (date(2026, 11, 6), 110.0)]
    result = compute_returns("AAPL", closes)
    assert result.price == 110.0


def test_compute_returns_1d_is_change_from_previous_trading_day():
    closes = [(date(2026, 11, 5), 100.0), (date(2026, 11, 6), 110.0)]
    result = compute_returns("AAPL", closes)
    assert result.change_1d == 0.1


def test_compute_returns_1d_is_none_with_only_one_data_point():
    closes = [(date(2026, 11, 6), 110.0)]
    result = compute_returns("AAPL", closes)
    assert result.change_1d is None


def test_compute_returns_1w_looks_back_roughly_seven_days():
    closes = [
        (date(2026, 10, 30), 100.0),  # ~7 days before current
        (date(2026, 11, 5), 105.0),
        (date(2026, 11, 6), 110.0),  # current
    ]
    result = compute_returns("AAPL", closes)
    assert result.change_1w == pytest.approx(0.1)


def test_compute_returns_qtd_baselines_on_prior_quarter_close():
    closes = [
        (date(2026, 9, 30), 100.0),  # last trading day of Q3 (quarter start for Q4 is Oct 1)
        (date(2026, 10, 15), 105.0),
        (date(2026, 11, 6), 120.0),  # current, inside Q4
    ]
    result = compute_returns("AAPL", closes)
    assert result.change_qtd == pytest.approx(0.2)


def test_compute_returns_ytd_baselines_on_prior_year_close():
    closes = [
        (date(2025, 12, 31), 100.0),
        (date(2026, 6, 1), 90.0),
        (date(2026, 11, 6), 150.0),  # current
    ]
    result = compute_returns("AAPL", closes)
    assert result.change_ytd == pytest.approx(0.5)


def test_compute_returns_is_none_when_no_history_reaches_back_far_enough():
    closes = [(date(2026, 11, 5), 100.0), (date(2026, 11, 6), 110.0)]
    result = compute_returns("AAPL", closes)
    assert result.change_qtd is None
    assert result.change_ytd is None


def test_compute_returns_skips_a_trailing_nan_close():
    closes = [
        (date(2026, 11, 5), 100.0),
        (date(2026, 11, 6), 110.0),
        (date(2026, 11, 9), float("nan")),
    ]
    result = compute_returns("AAPL", closes)
    assert result.price == 110.0
    assert result.change_1d == pytest.approx(0.1)


def test_compute_returns_skips_a_nan_close_in_the_middle_of_history():
    closes = [
        (date(2026, 11, 3), 90.0),
        (date(2026, 11, 4), float("nan")),
        (date(2026, 11, 5), 100.0),
        (date(2026, 11, 6), 110.0),
    ]
    result = compute_returns("AAPL", closes)
    assert result.price == 110.0
    assert result.change_1d == pytest.approx(0.1)


class _FakeHistoryProvider:
    def __init__(self, closes):
        self._closes = closes

    def __call__(self, ticker):
        return self._closes


def test_price_source_fetches_and_computes_returns():
    closes = [(date(2026, 11, 5), 100.0), (date(2026, 11, 6), 110.0)]
    source = YFinancePriceSource(history_provider=_FakeHistoryProvider(closes))

    result = source.fetch("AAPL")

    assert result.ticker == "AAPL"
    assert result.price == 110.0
    assert result.change_1d == 0.1
