import argparse
import json
import sys
from datetime import datetime, timezone

import state
import trello_digest


def _parse_now(now_arg):
    if now_arg:
        return datetime.fromisoformat(now_arg.replace("Z", "+00:00"))
    return datetime.now(timezone.utc)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--state-path", required=True)
    parser.add_argument("--now", default=None, help="ISO timestamp override for manual runs/tests")
    args = parser.parse_args()

    # UTF-8 stdin, always (Windows cp1252 default mangles card names).
    payload = json.loads(sys.stdin.buffer.read().decode("utf-8"))
    cards = payload["cards"]
    lists = payload.get("lists", [])
    now = _parse_now(args.now)

    tracked = state.load_state(args.state_path)
    actions = trello_digest.plan_calendar_actions(tracked, cards, now)
    list_names = {lst["id"]: lst["name"] for lst in lists}
    digest_cards = trello_digest.filter_due_cards(cards, now)
    digest_markdown = trello_digest.render_trello_section(digest_cards, list_names)

    print(json.dumps({"actions": actions, "digest_markdown": digest_markdown}))


if __name__ == "__main__":
    main()
