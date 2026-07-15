"""Pure helpers for the Trello -> digest/calendar integration.

Card dicts are exactly what mcp__trello__get_board_cards returns. Trello due
dates are UTC ISO strings with a trailing 'Z' (or null). All datetimes here
are timezone-aware.
"""
from datetime import datetime


def parse_due(due_iso):
    return datetime.fromisoformat(due_iso.replace("Z", "+00:00"))


def to_local(dt, tz=None):
    return dt.astimezone(tz)


def filter_due_cards(cards, now):
    due_cards = [c for c in cards if c.get("due")]
    kept = [
        c for c in due_cards
        if not (parse_due(c["due"]) < now and c.get("dueComplete"))
    ]
    return sorted(kept, key=lambda c: parse_due(c["due"]))
