from news_sentiment.models import ScoredHeadline, TickerRating

BUY_THRESHOLD = 0.2
SELL_THRESHOLD = -0.2


def score_to_rating(
    avg_score: float, buy_threshold: float = BUY_THRESHOLD, sell_threshold: float = SELL_THRESHOLD
) -> str:
    if avg_score > buy_threshold:
        return "BUY"
    if avg_score < sell_threshold:
        return "SELL"
    return "HOLD"


def aggregate_rating(ticker: str, scored_headlines: list[ScoredHeadline]) -> TickerRating:
    if not scored_headlines:
        return TickerRating(ticker=ticker, rating="HOLD", avg_score=0.0, scored_headlines=[])

    avg_score = sum(s.sentiment_score for s in scored_headlines) / len(scored_headlines)
    return TickerRating(
        ticker=ticker,
        rating=score_to_rating(avg_score),
        avg_score=avg_score,
        scored_headlines=scored_headlines,
    )
