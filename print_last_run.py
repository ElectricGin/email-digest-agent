import argparse
import time

import state


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--state-path", required=True)
    parser.add_argument("--account-email", required=True)
    parser.add_argument("--default-hours-ago", type=float, default=12.0)
    args = parser.parse_args()

    s = state.load_state(args.state_path)
    last_run = state.get_last_run(s, args.account_email)
    if last_run == 0:
        last_run = int(time.time() - args.default_hours_ago * 3600)
    print(last_run)


if __name__ == "__main__":
    main()
