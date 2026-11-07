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
