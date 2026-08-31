"""
StudyOS - SM-2 Spaced Repetition Engine
Implementation of the SuperMemo 2 algorithm for scheduling flashcard reviews.

Algorithm reference: https://www.supermemo.com/en/archives1990-2015/english/ol/sm2
"""

from datetime import date, timedelta


def update_card_schedule(
    ease_factor: float,
    interval_days: int,
    repetitions: int,
    quality: int,          # 0–5 scale (0=blackout, 5=perfect)
) -> tuple[float, int, int, date]:
    """
    SM-2 Algorithm: calculates the next review date for a flashcard.

    Args:
        ease_factor:   Current ease factor (default 2.5, min 1.3)
        interval_days: Current interval in days
        repetitions:   Number of successful repetitions so far
        quality:       Response quality 0-5:
                         0 = complete blackout
                         1 = incorrect (serious)
                         2 = incorrect (but easy to recall after seeing)
                         3 = correct with serious difficulty
                         4 = correct with some hesitation
                         5 = perfect response

    Returns:
        Tuple of (new_ease_factor, new_interval, new_repetitions, next_review_date)
    """
    # Failed: reset repetitions
    if quality < 3:
        repetitions = 0
        interval_days = 1
    else:
        # Successful recall
        if repetitions == 0:
            interval_days = 1
        elif repetitions == 1:
            interval_days = 6
        else:
            interval_days = round(interval_days * ease_factor)
        repetitions += 1

    # Update ease factor
    ease_factor = ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    ease_factor = max(1.3, ease_factor)   # Never drop below 1.3

    next_review = date.today() + timedelta(days=interval_days)
    return ease_factor, interval_days, repetitions, next_review


def get_due_cards(flashcards: list[dict]) -> list[dict]:
    """
    Filters flashcards that are due for review today or earlier.

    Args:
        flashcards: List of flashcard dicts with 'next_review_at' field.

    Returns:
        List of flashcards that need reviewing today.
    """
    today = date.today()
    due = []
    for card in flashcards:
        review_date_str = card.get("next_review_at")
        if review_date_str:
            review_date = date.fromisoformat(str(review_date_str))
            if review_date <= today:
                due.append(card)
    return due


# --- Quality scale helper for the UI ---
QUALITY_MAP = {
    "😵 Complete blackout":    0,
    "😖 Wrong (hard to recall)": 1,
    "😕 Wrong (easy to recall after seeing)": 2,
    "😐 Correct with difficulty": 3,
    "🙂 Correct with hesitation": 4,
    "😄 Perfect recall!":      5,
}
