# news_sentiment

Fetches recent news headlines for one or more stock tickers, scores each
headline's sentiment with a local [FinBERT](https://huggingface.co/ProsusAI/finbert)
model, and aggregates the result into a BUY / HOLD / SELL rating per ticker.
No API keys or paid subscriptions required — FinBERT runs locally via
`transformers`, and news comes from Yahoo Finance via `yfinance`.

## Setup

```bash
uv sync
```

Or, with [`just`](https://github.com/casey/just):

```bash
just venv
```

## Usage

```bash
uv run news-sentiment AAPL MSFT --count 20 --output report.csv
```

- `tickers` (positional, required): one or more ticker symbols.
- `--count`: headlines to fetch per ticker (default 20).
- `--output`: optional path to also save the results as CSV.
- `--verbose`: also print each headline with its sentiment label.
- `--compare`: score the same headlines with both FinBERT and
  [Qwen2.5-0.5B-Instruct](https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct)
  and print their ratings side by side, so you can see where a classifier
  model and a general-purpose LLM agree or disagree.

The first run downloads the FinBERT model (~440 MB) from Hugging Face and
caches it locally; subsequent runs reuse the cache and need no network
access for scoring. `--compare` additionally downloads Qwen2.5-0.5B-Instruct
(~1 GB) on first use.

### Comparing FinBERT and Qwen

```bash
uv run news-sentiment AAPL --compare --verbose
```

```
TICKER  FINBERT             QWEN
------------------------------------------------
AAPL    HOLD (0.00)         HOLD (0.00)

AAPL:
  Dow Jones Futures: Market Needs Repair But Apple, Amazon, Microsoft Strong
    finbert=positive  qwen=neutral
  ...
```

FinBERT is a classifier fine-tuned on financial text, so it's fast and
decisive but only judges a headline's general tone. Qwen is a small
general-purpose instruction-following model, so it's slower and, at this
size (0.5B parameters), noticeably more cautious — it defaults to "neutral"
more often. Swap `QWEN_MODEL` in `sentiment.py` for a larger Qwen checkpoint
(e.g. `Qwen/Qwen2.5-3B-Instruct`) if you want sharper judgments at the cost
of slower local inference.

**How Qwen scoring works internally:** unlike FinBERT, which is a classifier
that returns a label directly, Qwen is a text-generation model — it replies
with free-form text. `build_sentiment_prompt()` asks it to respond with one
word (Positive/Negative/Neutral), and `parse_llm_sentiment_label()` then
scans that reply for whichever of the three label words appears first
(case-insensitive) and uses that as the label. If the model's reply doesn't
contain any of the three words, parsing raises a `ValueError` rather than
guessing. Because Qwen doesn't expose a calibrated class probability the
way FinBERT's classifier does, its `confidence` is always reported as `1.0`.

## Dashboard

```bash
uv run news-sentiment-dashboard
```

Scores a fixed watchlist (`AAPL`, `MSFT`, `NVDA`, `GOOGL`, `AMZN`, `META`,
`AVGO`, `TSLA`, `BRK-B`, `LLY`, `JPM`, `WMT` — edit `DEFAULT_WATCHLIST` in
`dashboard.py` to change it) and the 11 SPDR sector ETFs with FinBERT only (fast and
reliable enough to run unattended; `--compare`-style LLM scoring stays a
manual tool, not part of the automated job). For each ticker it also pulls
the current price and 1-day, 1-week, quarter-to-date, and year-to-date
returns from Yahoo Finance via `prices.py` (`compute_returns` is pure —
given a list of `(date, close)` pairs it finds the closest trading day on
or before each period's start and computes the percentage change, with no
network access needed to test it). Writes `docs/dashboard-data.json`,
which `docs/dashboard.html` reads and renders as cards grouped into
Watchlist and Sector ETFs, sorted most-bullish-first, with the price
return shown alongside the sentiment rating and a background heatmap
tinted by `avg_score`.

For each watchlist stock (not sector ETFs, which don't report earnings),
`earnings.py` also pulls the next earnings date from Yahoo Finance via
`yfinance`'s `Ticker.calendar`. If that date falls within the next 2 weeks,
the card gets a distinct colored border and shows the date directly — a
quick visual flag for "this one's about to move."

- `--watchlist` / `--sector-etfs`: override either ticker list.
- `--count`: headlines per ticker (default 10, lower than the plain CLI's
  default since this runs across 23 tickers at once).
- `--output`: where to write the JSON (default `docs/dashboard-data.json`).

### Viewing it locally

`docs/dashboard.html` loads its data with `fetch()`, so it only works when
served over HTTP — opening the file directly (`file://`, e.g. double-clicking
it in Finder) won't work, and the page explains this if the fetch fails.

```bash
# 1. Generate (or refresh) the data it reads
uv run news-sentiment-dashboard

# 2. Serve the docs/ folder over HTTP
cd docs
python3 -m http.server 8000
```

Then open **http://localhost:8000/dashboard.html** in a browser. Leave the
server running and re-run step 1 (then reload the page) whenever you want
fresh data. Stop the server with `Ctrl+C`.

### Automating the daily refresh

`.github/workflows/dashboard.yml` runs `news-sentiment-dashboard` on a cron
schedule (weekdays, after US market close) and commits the updated
`dashboard-data.json` back to `main`. It needs no secrets — FinBERT and
`yfinance` are both free — but one thing still needs to be done once, by
hand, in the repo's GitHub settings:

**Enable GitHub Pages**, pointed at the `main` branch, `/docs` folder
(Settings → Pages). This is the one manual, one-time step left — it's what
actually serves `dashboard.html` publicly; the workflow itself is already
on `main` and needs no secrets to run.

Until Pages is enabled, `dashboard.html` still works — see
[Viewing it locally](#viewing-it-locally) above — against whatever
`dashboard-data.json` is currently committed; it just won't refresh itself.
The page shows a banner if the data is more than 36 hours old, as a
reminder the cron isn't deployed yet.

## Project structure

Each module has one job, so the pipeline reads top to bottom:

| Module | Responsibility |
|---|---|
| `models.py` | Plain data containers: `Headline`, `ScoredHeadline`, `TickerRating`. |
| `news_source.py` | Fetches and parses raw Yahoo Finance articles into `Headline`s. |
| `sentiment.py` | Wraps FinBERT and Qwen; scores a `Headline` into a `ScoredHeadline`. |
| `rating.py` | Pure logic: averages sentiment scores into a BUY/HOLD/SELL `TickerRating`. |
| `pipeline.py` | Wires a news source and scorer(s) together: fetch → score → rate, per ticker. `analyze_tickers_multi` fetches each ticker's headlines once and scores them with multiple models, so results are directly comparable. |
| `report.py` | Formats `TickerRating`s as a console table or CSV file, including side-by-side model comparisons. |
| `cli.py` | Argument parsing and the `news-sentiment` entry point. |
| `dashboard.py` | Builds the watchlist + sector-ETF JSON blob behind the dashboard, reusing `pipeline.analyze_tickers` and enriching each entry with price/return data from `prices.py` and earnings dates from `earnings.py`. |
| `dashboard_cli.py` | Argument parsing and the `news-sentiment-dashboard` entry point. |
| `prices.py` | Pulls price history from Yahoo Finance and computes 1D/1W/QTD/YTD returns; `compute_returns` is a pure function, tested without any network access. |
| `earnings.py` | Pulls each stock's next earnings date from Yahoo Finance and flags whether it falls within the next 2 weeks; `is_earnings_soon` is a pure function. |

Each piece that talks to the outside world (`news_source.py`, `sentiment.py`,
`prices.py`, `earnings.py`) takes its dependency as a constructor argument,
so the rest of the pipeline can be tested with fakes instead of hitting the network or
loading the real model — see `tests/`.

## Running tests

```bash
uv run pytest
```
