# tests/test_trello_digest.py
from datetime import datetime, timedelta, timezone

import trello_digest

UTC = timezone.utc
PACIFIC = timezone(timedelta(hours=-7))  # fixed offset for determinism (July = PDT)
NOW = datetime(2026, 7, 14, 12, 0, tzinfo=UTC)


def _card(card_id="c1", name="Uniform Collection", due="2026-07-26T19:00:00.000Z",
          due_complete=False, id_list="l1", url="https://trello.com/c/abc"):
    return {"id": card_id, "name": name, "due": due, "dueComplete": due_complete,
            "idList": id_list, "shortUrl": url, "url": url, "closed": False}


def test_parse_due_handles_trello_z_suffix():
    result = trello_digest.parse_due("2026-07-26T19:00:00.000Z")
    assert result == datetime(2026, 7, 26, 19, 0, tzinfo=UTC)


def test_filter_due_cards_drops_cards_without_due():
    cards = [_card(due=None), _card(card_id="c2")]
    result = trello_digest.filter_due_cards(cards, NOW)
    assert [c["id"] for c in result] == ["c2"]


def test_filter_due_cards_drops_past_completed_keeps_past_incomplete():
    past_done = _card(card_id="done", due="2026-07-12T19:00:00.000Z", due_complete=True)
    past_open = _card(card_id="overdue", due="2026-07-12T19:00:00.000Z")
    result = trello_digest.filter_due_cards([past_done, past_open], NOW)
    assert [c["id"] for c in result] == ["overdue"]


def test_filter_due_cards_sorts_ascending_by_due():
    aug = _card(card_id="aug", due="2026-08-02T01:00:00.000Z")
    jul = _card(card_id="jul", due="2026-07-24T20:00:00.000Z")
    result = trello_digest.filter_due_cards([aug, jul], NOW)
    assert [c["id"] for c in result] == ["jul", "aug"]


def test_plan_actions_creates_untracked_future_card():
    actions = trello_digest.plan_calendar_actions({}, [_card()], NOW, tz=PACIFIC)
    assert len(actions["create"]) == 1
    entry = actions["create"][0]
    assert entry["card_id"] == "c1"
    assert entry["name"] == "Uniform Collection"
    assert entry["url"] == "https://trello.com/c/abc"
    assert entry["due"] == "2026-07-26T19:00:00.000Z"
    assert entry["start_local"] == "2026-07-26T12:00:00"
    assert entry["end_local"] == "2026-07-26T13:00:00"
    assert entry["due_date_local"] == "2026-07-26"
    assert actions["update"] == [] and actions["delete"] == [] and actions["forget"] == []


def test_plan_actions_skips_create_for_past_completed_card():
    card = _card(due="2026-07-12T19:00:00.000Z", due_complete=True)
    actions = trello_digest.plan_calendar_actions({}, [card], NOW, tz=PACIFIC)
    assert actions["create"] == []


def test_plan_actions_ignores_unchanged_tracked_card():
    state = {"c1": {"event_id": "ev1", "due": "2026-07-26T19:00:00.000Z", "name": "Uniform Collection"}}
    actions = trello_digest.plan_calendar_actions(state, [_card()], NOW, tz=PACIFIC)
    assert actions == {"create": [], "update": [], "delete": [], "forget": []}


def test_plan_actions_updates_owned_event_when_due_moves():
    state = {"c1": {"event_id": "ev1", "due": "2026-07-20T19:00:00.000Z", "name": "Uniform Collection"}}
    actions = trello_digest.plan_calendar_actions(state, [_card()], NOW, tz=PACIFIC)
    assert len(actions["update"]) == 1
    assert actions["update"][0]["event_id"] == "ev1"
    assert actions["update"][0]["start_local"] == "2026-07-26T12:00:00"
    assert actions["create"] == []


def test_plan_actions_recreates_unowned_card_when_due_moves():
    state = {"c1": {"event_id": None, "due": "2026-07-20T19:00:00.000Z", "name": "Uniform Collection"}}
    actions = trello_digest.plan_calendar_actions(state, [_card()], NOW, tz=PACIFIC)
    assert len(actions["create"]) == 1
    assert actions["update"] == []


def test_plan_actions_deletes_owned_event_when_card_disappears():
    state = {"gone": {"event_id": "ev9", "due": "2026-07-20T19:00:00.000Z", "name": "Old Card"}}
    actions = trello_digest.plan_calendar_actions(state, [], NOW, tz=PACIFIC)
    assert actions["delete"] == [{"card_id": "gone", "name": "Old Card", "event_id": "ev9"}]
    assert actions["forget"] == []


def test_plan_actions_forgets_unowned_entry_when_card_disappears():
    state = {"gone": {"event_id": None, "due": "2026-07-20T19:00:00.000Z", "name": "Old Card"}}
    actions = trello_digest.plan_calendar_actions(state, [], NOW, tz=PACIFIC)
    assert actions["delete"] == []
    assert actions["forget"] == ["gone"]
