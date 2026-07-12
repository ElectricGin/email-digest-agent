# tests/test_accounts.py
import json
import os
import accounts


def test_load_accounts_returns_label_to_email_mapping(tmp_path):
    path = os.path.join(tmp_path, "accounts.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"personal1": "a@gmail.com", "personal2": "b@gmail.com"}, f)

    result = accounts.load_accounts(path)

    assert result == {"personal1": "a@gmail.com", "personal2": "b@gmail.com"}
