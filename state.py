import json
import os


def load_state(state_path):
    if not os.path.exists(state_path):
        return {}
    with open(state_path, encoding="utf-8") as f:
        return json.load(f)


def save_state(state_path, state):
    os.makedirs(os.path.dirname(state_path), exist_ok=True)
    with open(state_path, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def get_last_run(state, account_email):
    return state.get(account_email, 0)


def set_last_run(state, account_email, epoch_seconds):
    state[account_email] = epoch_seconds
