"""
SM-2 spaced repetition algorithm.

Reference: https://www.supermemo.com/en/blog/application-of-a-computer-to-improve-the-results-obtained-in-working-with-the-supermemo-method

quality: 0-5
  0 = complete blackout
  1 = incorrect, but remembered after hint
  2 = incorrect, but seemed easy on seeing answer
  3 = correct with serious difficulty
  4 = correct after hesitation
  5 = perfect response
"""

from datetime import datetime, timedelta, timezone
from models.vocabulary import UserWordProgress


def sm2_update(progress: UserWordProgress, quality: int) -> UserWordProgress:
    """Apply one SM-2 review cycle. Mutates and returns progress."""
    now = datetime.now(timezone.utc)
    progress.last_reviewed = now

    if quality < 3:
        # Failed — reset repetitions, keep ease factor, retry soon
        progress.repetitions = 0
        progress.interval_days = 1
    else:
        # Successful recall
        if progress.repetitions == 0:
            progress.interval_days = 1
        elif progress.repetitions == 1:
            progress.interval_days = 6
        else:
            progress.interval_days = round(
                progress.interval_days * progress.ease_factor
            )
        progress.repetitions += 1

    # Update ease factor: EF' = EF + (0.1 - (5-q)*(0.08 + (5-q)*0.02))
    ef = progress.ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    progress.ease_factor = max(1.3, round(ef, 2))  # never below 1.3

    progress.next_review = now + timedelta(days=progress.interval_days)

    # Mark as "learned" after 3+ successful repetitions with interval >= 21 days
    if progress.repetitions >= 3 and progress.interval_days >= 21:
        progress.is_learned = True

    return progress
