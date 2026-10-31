"""
Daily streak tracking.

A streak counts consecutive UTC days on which the user did something that earns XP (a review,
a completed text/lesson, or a submitted test). Calling record_activity more than once in a day
doesn't change the streak; a one-day gap breaks it.

UTC is used because the app has no per-user timezone yet; document this if timezones are added.
"""
from datetime import date, timedelta

from models.user import User


def record_activity(user: User, today: date | None = None) -> bool:
    """Update the user's streak for activity 'today'. Returns True if the streak value changed."""
    today = today or date.today()
    last = user.last_active_on
    if last == today:
        return False                      # already counted today
    before = user.streak_days
    if last == today - timedelta(days=1):
        user.streak_days = (user.streak_days or 0) + 1   # consecutive day
    else:
        user.streak_days = 1              # first activity ever, or after a gap
    user.last_active_on = today
    return user.streak_days != before
