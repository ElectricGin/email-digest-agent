"""Pure helpers for the Trello -> digest/calendar integration.

Card dicts are exactly what mcp__trello__get_board_cards returns. Trello due
dates are UTC ISO strings with a trailing 'Z' (or null). All datetimes here
are timezone-aware.
"""
from datetime import datetime, timedelta


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


def _card_payload(card, tz=None):
    start = to_local(parse_due(card["due"]), tz)
    end = start + timedelta(hours=1)
    return {
        "card_id": card["id"],
        "name": card["name"],
        "url": card.get("shortUrl") or card["url"],
        "due": card["due"],
        "start_local": start.strftime("%Y-%m-%dT%H:%M:%S"),
        "end_local": end.strftime("%Y-%m-%dT%H:%M:%S"),
        "due_date_local": start.strftime("%Y-%m-%d"),
    }


def plan_calendar_actions(state, cards, now, tz=None):
    due_cards = [c for c in cards if c.get("due")]
    current_ids = {c["id"] for c in due_cards}
    actions = {"create": [], "update": [], "delete": [], "forget": []}

    for card in due_cards:
        tracked = state.get(card["id"])
        if tracked is None:
            already_over = parse_due(card["due"]) < now and card.get("dueComplete")
            if not already_over:
                actions["create"].append(_card_payload(card, tz))
        elif tracked.get("due") != card["due"]:
            payload = _card_payload(card, tz)
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
