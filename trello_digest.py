"""Pure helpers for the Trello -> digest/calendar integration.

Card dicts are exactly what mcp__trello__get_board_cards returns. Trello due
dates are UTC ISO strings with a trailing 'Z' (or null). All datetimes here
are timezone-aware.
"""
import re
from datetime import datetime, timedelta
from difflib import SequenceMatcher

_PREFIX_RE = re.compile(r"^\s*\[(deadline|reminder)\]\s*", re.IGNORECASE)
_PUNCT_RE = re.compile(r"[^a-z0-9 ]+")

AIDEN_MEMBER_ID = "66788df92709bb7c87934dd4"


def parse_due(due_iso):
    return datetime.fromisoformat(due_iso.replace("Z", "+00:00"))


def to_local(dt, tz=None):
    return dt.astimezone(tz)


def calendar_title_for_card(card, members_by_id=None):
    """Return the calendar event title for a card.

    Cards assigned to Aiden (or unassigned) use the card name as-is.
    Cards assigned exclusively to other members get a first-name prefix
    so Aiden can tell at a glance whose task it is.
    """
    members_by_id = members_by_id or {}
    assigned = card.get("idMembers") or []
    if not assigned or AIDEN_MEMBER_ID in assigned:
        return card["name"]
    first_id = assigned[0]
    full_name = members_by_id.get(first_id, {}).get("fullName", "")
    first_name = full_name.split()[0] if full_name else ""
    prefix = f"{first_name}: " if first_name else ""
    return f"{prefix}{card['name']}"


def filter_due_cards(cards, now):
    due_cards = [c for c in cards if c.get("due")]
    kept = [
        c for c in due_cards
        if not (parse_due(c["due"]) < now and c.get("dueComplete"))
    ]
    return sorted(kept, key=lambda c: parse_due(c["due"]))


def _card_payload(card, tz=None, members_by_id=None):
    start = to_local(parse_due(card["due"]), tz)
    end = start + timedelta(hours=1)
    return {
        "card_id": card["id"],
        "name": calendar_title_for_card(card, members_by_id),
        "url": card.get("shortUrl") or card["url"],
        "due": card["due"],
        "start_local": start.strftime("%Y-%m-%dT%H:%M:%S"),
        "end_local": end.strftime("%Y-%m-%dT%H:%M:%S"),
        "due_date_local": start.strftime("%Y-%m-%d"),
    }


def plan_calendar_actions(state, cards, now, tz=None, members_by_id=None):
    due_cards = [c for c in cards if c.get("due")]
    current_ids = {c["id"] for c in due_cards}
    actions = {"create": [], "update": [], "delete": [], "forget": []}

    for card in due_cards:
        tracked = state.get(card["id"])
        new_title = calendar_title_for_card(card, members_by_id)
        if tracked is None:
            already_over = parse_due(card["due"]) < now and card.get("dueComplete")
            if not already_over:
                actions["create"].append(_card_payload(card, tz, members_by_id))
        elif tracked.get("due") != card["due"] or tracked.get("name") != new_title:
            payload = _card_payload(card, tz, members_by_id)
            if tracked.get("event_id"):
                payload["event_id"] = tracked["event_id"]
                actions["update"].append(payload)
            else:
                actions["create"].append(payload)

    for card_id, tracked in state.items():
        if card_id in current_ids:
            continue
        if tracked.get("event_id"):
            actions["delete"].append({
                "card_id": card_id,
                "name": tracked.get("name", ""),
                "event_id": tracked["event_id"],
            })
        else:
            actions["forget"].append(card_id)
    return actions


def render_trello_section(cards, list_names, tz=None):
    lines = ["## Trello Deadlines", ""]
    if not cards:
        lines.append("- No upcoming Trello deadlines.")
    for card in cards:
        due_local = to_local(parse_due(card["due"]), tz)
        # %#d / %#I are the Windows no-pad flags (same convention as wiki_writer.py).
        stamp = due_local.strftime("%a %b %#d, %#I:%M %p")
        list_name = list_names.get(card["idList"], "?")
        url = card.get("shortUrl") or card["url"]
        lines.append(f"- **{card['name']}** — due {stamp} ({list_name}) — {url}")
    return "\n".join(lines) + "\n"


def _normalize_title(title):
    t = _PREFIX_RE.sub("", title.strip().lower())
    t = _PUNCT_RE.sub(" ", t)
    return " ".join(t.split())


def _titles_match(a, b):
    na, nb = _normalize_title(a), _normalize_title(b)
    if not na or not nb:
        return False
    if na in nb or nb in na:
        return True
    return SequenceMatcher(None, na, nb).ratio() >= 0.75


def find_email_duplicates(email_items, cards, tz=None):
    suppress = []
    for item in email_items:
        item_date = datetime.fromisoformat(item["date"]).date()
        for card in cards:
            if not card.get("due"):
                continue
            card_date = to_local(parse_due(card["due"]), tz).date()
            if abs((item_date - card_date).days) <= 1 and _titles_match(item["title"], card["name"]):
                suppress.append(item["title"])
                break
    return suppress


_ORDINAL_RE = re.compile(r"^\d+(st|nd|rd|th)?$")
_MONTHS = {
    "january", "february", "march", "april", "may", "june", "july",
    "august", "september", "october", "november", "december",
}
_WEEKDAYS = {"monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"}
_STOPWORDS = {"the", "a", "an", "for", "of", "on", "at", "to", "in", "and", "by", "is", "are", "due"}


def _significant_words(title):
    words = _normalize_title(title).split()
    return {
        w for w in words
        if len(w) > 2
        and w not in _STOPWORDS
        and w not in _MONTHS
        and w not in _WEEKDAYS
        and not _ORDINAL_RE.match(w)
    }


def _event_start(event):
    dt = (event or {}).get("start", {}).get("dateTime")
    return datetime.fromisoformat(dt) if dt else None


def find_matching_calendar_event(card, events, tz=None, max_minutes=60, min_shared_words=2):
    """Best-guess match between a Trello card and an existing calendar event
    (e.g. a native TBC invite), used to avoid creating a duplicate.

    Matches on start-time proximity (a native invite's real time is rarely more
    than an hour off the Trello due date) plus shared significant title words.
    Exact-substring/high-similarity title matching (see `_titles_match`, used
    for email dedup) is too strict here -- TBC's invite titles and Trello card
    names are often worded quite differently for the same real event (e.g.
    "Uniform Building Workdays" vs "emergency uniform building workday", or
    "September 27th Uniform Distribution Prep" vs "Cadets Uniform Distribution").
    Returns the closest-in-time qualifying event, or None.
    """
    card_start = to_local(parse_due(card["due"]), tz)
    card_words = _significant_words(card["name"])
    best, best_diff = None, None
    for event in events:
        ev_start = _event_start(event)
        if ev_start is None:
            continue
        diff_minutes = abs((ev_start - card_start).total_seconds()) / 60
        if diff_minutes > max_minutes:
            continue
        shared = card_words & _significant_words(event.get("summary", ""))
        if len(shared) < min_shared_words:
            continue
        if best is None or diff_minutes < best_diff:
            best, best_diff = event, diff_minutes
    return best


def apply_state_changes(state, upserts, removes):
    for entry in upserts:
        state[entry["card_id"]] = {
            "event_id": entry.get("event_id"),
            "due": entry["due"],
            "name": entry["name"],
        }
    for card_id in removes:
        state.pop(card_id, None)
    return state
