import csv
from pathlib import Path

from news_sentiment.models import TickerRating

_COLUMNS = ("ticker", "rating", "avg_score", "num_headlines")


def format_report(ratings: list[TickerRating]) -> str:
    header = f"{'TICKER':<8}{'RATING':<8}{'AVG SCORE':<12}{'HEADLINES':<10}"
    lines = [header, "-" * len(header)]
    for r in ratings:
        lines.append(f"{r.ticker:<8}{r.rating:<8}{r.avg_score:<12.2f}{len(r.scored_headlines):<10}")
    return "\n".join(lines)


def format_headlines(ratings: list[TickerRating]) -> str:
    lines = []
    for r in ratings:
        lines.append(f"{r.ticker} ({r.rating}):")
        if not r.scored_headlines:
            lines.append("  no headlines")
            continue
        for scored in r.scored_headlines:
            publisher = f" [{scored.headline.publisher}]" if scored.headline.publisher else ""
            lines.append(f"  {scored.label:<10} {scored.headline.title}{publisher}")
        lines.append("")
    return "\n".join(lines).rstrip()


def save_csv(ratings: list[TickerRating], path: Path) -> None:
    with Path(path).open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=_COLUMNS)
        writer.writeheader()
        for r in ratings:
            writer.writerow(
                {
                    "ticker": r.ticker,
                    "rating": r.rating,
                    "avg_score": r.avg_score,
                    "num_headlines": len(r.scored_headlines),
                }
            )


def format_comparison(results: dict[str, dict[str, TickerRating]]) -> str:
    if not results:
        return ""

    model_names = list(next(iter(results.values())).keys())
    column_width = 20
    header = f"{'TICKER':<8}" + "".join(f"{name.upper():<{column_width}}" for name in model_names)
    lines = [header, "-" * len(header)]
    for ticker, by_model in results.items():
        cells = []
        for name in model_names:
            rating = by_model[name]
            cells.append(f"{rating.rating} ({rating.avg_score:.2f})")
        lines.append(f"{ticker:<8}" + "".join(f"{cell:<{column_width}}" for cell in cells))
    return "\n".join(lines)


def format_comparison_headlines(results: dict[str, dict[str, TickerRating]]) -> str:
    lines = []
    for ticker, by_model in results.items():
        lines.append(f"{ticker}:")
        model_names = list(by_model.keys())
        scored_lists = [by_model[name].scored_headlines for name in model_names]
        num_headlines = len(scored_lists[0]) if scored_lists else 0

        if num_headlines == 0:
            lines.append("  no headlines")
            lines.append("")
            continue

        for i in range(num_headlines):
            title = scored_lists[0][i].headline.title
            labels = "  ".join(f"{name}={scored_lists[j][i].label}" for j, name in enumerate(model_names))
            lines.append(f"  {title}")
            lines.append(f"    {labels}")
        lines.append("")
    return "\n".join(lines).rstrip()


def save_comparison_csv(results: dict[str, dict[str, TickerRating]], path: Path) -> None:
    with Path(path).open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=("ticker", "model") + _COLUMNS[1:])
        writer.writeheader()
        for ticker, by_model in results.items():
            for model_name, rating in by_model.items():
                writer.writerow(
                    {
                        "ticker": ticker,
                        "model": model_name,
                        "rating": rating.rating,
                        "avg_score": rating.avg_score,
                        "num_headlines": len(rating.scored_headlines),
                    }
                )
