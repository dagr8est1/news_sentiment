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

The first run downloads the FinBERT model (~440 MB) from Hugging Face and
caches it locally; subsequent runs reuse the cache and need no network
access for scoring.

## Project structure

Each module has one job, so the pipeline reads top to bottom:

| Module | Responsibility |
|---|---|
| `models.py` | Plain data containers: `Headline`, `ScoredHeadline`, `TickerRating`. |
| `news_source.py` | Fetches and parses raw Yahoo Finance articles into `Headline`s. |
| `sentiment.py` | Wraps FinBERT; scores a `Headline` into a `ScoredHeadline`. |
| `rating.py` | Pure logic: averages sentiment scores into a BUY/HOLD/SELL `TickerRating`. |
| `pipeline.py` | Wires a news source and scorer together: fetch → score → rate, per ticker. |
| `report.py` | Formats `TickerRating`s as a console table or CSV file. |
| `cli.py` | Argument parsing and the `news-sentiment` entry point. |

Each piece that talks to the outside world (`news_source.py`, `sentiment.py`)
takes its dependency as a constructor argument, so the rest of the pipeline
can be tested with fakes instead of hitting the network or loading the real
model — see `tests/`.

## Running tests

```bash
uv run pytest
```
