import json


def load_accounts(accounts_path):
    with open(accounts_path, encoding="utf-8") as f:
        return json.load(f)
