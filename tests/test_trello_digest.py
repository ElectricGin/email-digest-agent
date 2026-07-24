# tests/test_trello_digest.py
from datetime import datetime, timedelta, timezone

import trello_digest

UTC = timezone.utc
PACIFIC = timezone(timedelta(hours=-7))  # fixed offset for determinism (July = PDT)
NOW = datetime(2026, 7, 14, 12, 0, tzinfo=UTC)


AIDEN_ID = trello_digest.AIDEN_MEMBER_ID
ASHLEY_ID = "66f66ba209bed212be062e83"
MEMBERS_BY_ID = {
    AIDEN_ID: {"id": AIDEN_ID, "fullName": "Aiden Chu"},
    ASHLEY_ID: {"id": ASHLEY_ID, "fullName": "Ashley Shen"},
}


def _card(card_id="c1", name="Uniform Collection", due="2026-07-26T19:00:00.000Z",
          due_complete=False, id_list="l1", url="https://trello.com/c/abc",
          id_members=None):
    c = {"id": card_id, "name": name, "due": due, "dueComplete": due_complete,
         "idList": id_list, "shortUrl": url, "url": url, "closed": False}
    if id_members is not None:
        c["idMembers"] = id_members
    return c


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


def test_render_section_formats_card_line_in_local_time():
    card = _card(id_list="l-summer")
    result = trello_digest.render_trello_section(
        [card], {"l-summer": "Summer 2026"}, tz=PACIFIC
    )
    assert result.startswith("## Trello Deadlines\n\n")
    assert ("- **Uniform Collection** — due Sun Jul 26, 12:00 PM (Summer 2026) "
            "— https://trello.com/c/abc") in result
    assert result.endswith("\n")


def test_render_section_when_empty_says_no_deadlines():
    result = trello_digest.render_trello_section([], {}, tz=PACIFIC)
    assert "- No upcoming Trello deadlines." in result


def test_dedup_flags_same_title_same_day():
    items = [{"title": "[Deadline] Uniform Collection", "date": "2026-07-26"}]
    result = trello_digest.find_email_duplicates(items, [_card()], tz=PACIFIC)
    assert result == ["[Deadline] Uniform Collection"]


def test_dedup_flags_containment_match_one_day_apart():
    items = [{"title": "[Reminder] TBC uniform collection!", "date": "2026-07-27"}]
    result = trello_digest.find_email_duplicates(items, [_card()], tz=PACIFIC)
    assert result == ["[Reminder] TBC uniform collection!"]


def test_dedup_ignores_different_title():
    items = [{"title": "[Deadline] Chem lab report due", "date": "2026-07-26"}]
    assert trello_digest.find_email_duplicates(items, [_card()], tz=PACIFIC) == []


def test_dedup_ignores_matching_title_far_date():
    items = [{"title": "[Deadline] Uniform Collection", "date": "2026-07-30"}]
    assert trello_digest.find_email_duplicates(items, [_card()], tz=PACIFIC) == []


# --- find_matching_calendar_event ---

def _event(summary, start_dt_iso):
    return {"summary": summary, "start": {"dateTime": start_dt_iso}}


def test_find_matching_event_differently_worded_same_time():
    # Real case: routine created "Uniform Building Workdays" (1pm), TBC's own
    # invite was "emergency uniform building workday" (also 1pm) -- titles
    # share no long common substring but do share 3 significant words.
    card = _card(name="Uniform Building Workdays", due="2026-07-24T20:00:00.000Z")
    events = [_event("emergency uniform building workday", "2026-07-24T13:00:00-07:00")]
    match = trello_digest.find_matching_calendar_event(card, events, tz=PACIFIC)
    assert match is not None
    assert match["summary"] == "emergency uniform building workday"


def test_find_matching_event_prep_card_vs_generic_native_title():
    # Real case: "September 27th Uniform Distribution Prep" vs native
    # "Cadets Uniform Distribution", same day and time.
    card = _card(name="September 27th Uniform Distribution Prep", due="2026-09-27T20:30:00.000Z")
    events = [_event("Cadets Uniform Distribution", "2026-09-27T13:30:00-07:00")]
    match = trello_digest.find_matching_calendar_event(card, events, tz=PACIFIC)
    assert match is not None


def test_find_matching_event_ignores_far_different_day():
    # Real case: "Uniform Collection @ Great America" (Jul 25) is NOT the same
    # event as the native "great america parade uniform collection workday"
    # (Aug 1) despite heavy keyword overlap -- six days apart is too far.
    card = _card(name="Uniform Collection @ Great America", due="2026-07-25T19:00:00.000Z")
    events = [_event("great america parade uniform collection workday", "2026-08-01T09:00:00-07:00")]
    assert trello_digest.find_matching_calendar_event(card, events, tz=PACIFIC) is None


def test_find_matching_event_respects_time_window_even_with_keyword_overlap():
    # A same-day event more than max_minutes away must not match even when
    # titles overlap heavily -- keyword overlap alone isn't enough signal.
    card = _card(name="Uniform Distribution", due="2026-09-27T22:30:00.000Z")  # 3:30pm local
    events = [_event("Cadets Uniform Distribution", "2026-09-27T13:30:00-07:00")]  # 1:30pm local
    assert trello_digest.find_matching_calendar_event(card, events, tz=PACIFIC) is None


def test_find_matching_event_ignores_unrelated_title_same_time():
    card = _card(name="Department Report", due="2026-08-24T04:00:00.000Z")
    events = [_event("Full Band Rehearsal #9", "2026-08-23T21:00:00-07:00")]
    assert trello_digest.find_matching_calendar_event(card, events, tz=PACIFIC) is None


def test_find_matching_event_no_candidates_returns_none():
    card = _card()
    assert trello_digest.find_matching_calendar_event(card, [], tz=PACIFIC) is None


def test_find_matching_event_skips_all_day_events():
    card = _card(due="2026-07-25T19:00:00.000Z")
    events = [{"summary": "Uniform Collection", "start": {"date": "2026-07-25"}}]
    assert trello_digest.find_matching_calendar_event(card, events, tz=PACIFIC) is None


def test_find_matching_event_picks_closest_in_time_among_multiple():
    card = _card(name="Uniform Collection", due="2026-07-26T19:00:00.000Z")  # 12:00pm local
    far = _event("uniform collection meeting", "2026-07-26T12:30:00-07:00")   # 30 min away
    near = _event("uniform collection", "2026-07-26T11:50:00-07:00")          # 10 min away
    match = trello_digest.find_matching_calendar_event(card, [far, near], tz=PACIFIC)
    assert match is near


def test_apply_state_changes_upserts_and_removes():
    state = {"old": {"event_id": "ev0", "due": "2026-07-01T00:00:00.000Z", "name": "Old"}}
    upserts = [
        {"card_id": "c1", "event_id": "ev1", "due": "2026-07-26T19:00:00.000Z", "name": "Uniform Collection"},
        {"card_id": "c2", "event_id": None, "due": "2026-08-02T01:00:00.000Z", "name": "Uniform Washing"},
    ]
    result = trello_digest.apply_state_changes(state, upserts, ["old", "never-existed"])
    assert result == {
        "c1": {"event_id": "ev1", "due": "2026-07-26T19:00:00.000Z", "name": "Uniform Collection"},
        "c2": {"event_id": None, "due": "2026-08-02T01:00:00.000Z", "name": "Uniform Washing"},
    }


def test_apply_state_changes_overwrites_existing_entry():
    state = {"c1": {"event_id": "ev1", "due": "2026-07-20T19:00:00.000Z", "name": "Uniform Collection"}}
    trello_digest.apply_state_changes(
        state,
        [{"card_id": "c1", "event_id": "ev1", "due": "2026-07-26T19:00:00.000Z", "name": "Uniform Collection"}],
        [],
    )
    assert state["c1"]["due"] == "2026-07-26T19:00:00.000Z"


# --- calendar_title_for_card ---

def test_calendar_title_unassigned_uses_card_name():
    card = _card(id_members=[])
    assert trello_digest.calendar_title_for_card(card, MEMBERS_BY_ID) == "Uniform Collection"


def test_calendar_title_missing_idmembers_uses_card_name():
    card = _card()  # no idMembers key at all
    assert trello_digest.calendar_title_for_card(card, MEMBERS_BY_ID) == "Uniform Collection"


def test_calendar_title_aiden_only_uses_card_name():
    card = _card(id_members=[AIDEN_ID])
    assert trello_digest.calendar_title_for_card(card, MEMBERS_BY_ID) == "Uniform Collection"


def test_calendar_title_aiden_plus_other_uses_card_name():
    card = _card(id_members=[AIDEN_ID, ASHLEY_ID])
    assert trello_digest.calendar_title_for_card(card, MEMBERS_BY_ID) == "Uniform Collection"


def test_calendar_title_other_only_prefixes_first_name():
    card = _card(name="Trello Testing", id_members=[ASHLEY_ID])
    assert trello_digest.calendar_title_for_card(card, MEMBERS_BY_ID) == "Ashley: Trello Testing"


def test_calendar_title_unknown_member_id_omits_prefix():
    card = _card(name="Some Task", id_members=["unknown-id"])
    assert trello_digest.calendar_title_for_card(card, MEMBERS_BY_ID) == "Some Task"


# --- plan_calendar_actions with member-based titles ---

def test_plan_actions_create_uses_member_prefixed_title():
    card = _card(name="Trello Testing", id_members=[ASHLEY_ID])
    actions = trello_digest.plan_calendar_actions({}, [card], NOW, tz=PACIFIC, members_by_id=MEMBERS_BY_ID)
    assert len(actions["create"]) == 1
    assert actions["create"][0]["name"] == "Ashley: Trello Testing"


def test_plan_actions_update_triggered_by_title_change():
    # State has the old card-name title; member context now produces a prefixed title.
    state = {"c1": {"event_id": "ev1", "due": "2026-07-26T19:00:00.000Z", "name": "Trello Testing"}}
    card = _card(name="Trello Testing", id_members=[ASHLEY_ID])
    actions = trello_digest.plan_calendar_actions(state, [card], NOW, tz=PACIFIC, members_by_id=MEMBERS_BY_ID)
    assert len(actions["update"]) == 1
    assert actions["update"][0]["name"] == "Ashley: Trello Testing"
    assert actions["update"][0]["event_id"] == "ev1"
    assert actions["create"] == []
