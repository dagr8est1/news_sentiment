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

Each piece that talks to the outside world (`news_source.py`, `sentiment.py`)
takes its dependency as a constructor argument, so the rest of the pipeline
can be tested with fakes instead of hitting the network or loading the real
model — see `tests/`.

## Running tests

```bash
uv run pytest
```
