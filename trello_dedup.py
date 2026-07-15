import argparse
import json
import sys
from datetime import datetime, timezone

import trello_digest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--now", default=None, help="ISO timestamp override for manual runs/tests")
    args = parser.parse_args()

    payload = json.loads(sys.stdin.buffer.read().decode("utf-8"))
    if args.now:
        now = datetime.fromisoformat(args.now.replace("Z", "+00:00"))
    else:
        now = datetime.now(timezone.utc)

    # Match only against cards that will actually be displayed — a suppressed
    # email bullet must always be represented by a visible Trello line.
    displayed = trello_digest.filter_due_cards(payload.get("cards", []), now)
    suppress = trello_digest.find_email_duplicates(payload.get("email_items", []), displayed)
    print(json.dumps({"suppress_titles": suppress}))


if __name__ == "__main__":
    main()
