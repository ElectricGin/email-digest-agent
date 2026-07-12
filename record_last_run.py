import argparse

import state


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--state-path", required=True)
    parser.add_argument("--account-email", required=True)
    parser.add_argument("--epoch", type=int, required=True)
    args = parser.parse_args()

    s = state.load_state(args.state_path)
    state.set_last_run(s, args.account_email, args.epoch)
    state.save_state(args.state_path, s)
    print(f"recorded last-run {args.epoch} for {args.account_email}")


if __name__ == "__main__":
    main()
