import argparse
import json
import sys

import state
import trello_digest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--state-path", required=True)
    args = parser.parse_args()

    payload = json.loads(sys.stdin.buffer.read().decode("utf-8"))
    upserts = payload.get("upsert", [])
    removes = payload.get("remove", [])

    tracked = state.load_state(args.state_path)
    trello_digest.apply_state_changes(tracked, upserts, removes)
    state.save_state(args.state_path, tracked)
    print(f"recorded {len(upserts)} upserts, {len(removes)} removals")


if __name__ == "__main__":
    main()
