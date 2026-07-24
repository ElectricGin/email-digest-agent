"""Check a single Trello card against candidate calendar events for a likely
duplicate (e.g. a native TBC invite for the same real-world event), before
the routine creates a new event for it.

Usage: python trello_find_dupe.py --tz-offset -7 < dupe_check_in.json
Input (stdin): {"card": <trello card dict>, "events": [<search_events results>]}
Output (stdout): the matching event dict, or null if no match found.
"""
import argparse
import json
import sys
from datetime import timedelta, timezone

import trello_digest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tz-offset", type=float, default=-7,
                         help="Fixed UTC offset in hours for the local calendar (default -7, PDT).")
    args = parser.parse_args()

    payload = json.loads(sys.stdin.buffer.read().decode("utf-8"))
    tz = timezone(timedelta(hours=args.tz_offset))
    match = trello_digest.find_matching_calendar_event(payload["card"], payload["events"], tz=tz)
    print(json.dumps(match))


if __name__ == "__main__":
    main()
