from dataclasses import dataclass, field


@dataclass(frozen=True)
class Headline:
    ticker: str
    title: str
    publisher: str | None
    url: str | None
    published_at: str | None


@dataclass(frozen=True)
class ScoredHeadline:
    headline: Headline
    label: str
    confidence: float
    sentiment_score: int


@dataclass(frozen=True)
class TickerRating:
    ticker: str
    rating: str
    avg_score: float
    scored_headlines: list[ScoredHeadline] = field(default_factory=list)
