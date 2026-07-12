# tests/test_state.py
import os
import state


def test_load_state_returns_empty_dict_when_file_missing(tmp_path):
    path = os.path.join(tmp_path, "state.json")
    assert state.load_state(path) == {}


def test_save_and_load_roundtrip(tmp_path):
    path = os.path.join(tmp_path, "nested", "state.json")
    state.save_state(path, {"a@gmail.com": 1000})
    assert state.load_state(path) == {"a@gmail.com": 1000}


def test_get_last_run_defaults_to_zero():
    assert state.get_last_run({}, "a@gmail.com") == 0
    assert state.get_last_run({"a@gmail.com": 1234}, "a@gmail.com") == 1234


def test_set_last_run_updates_in_place():
    s = {}
    state.set_last_run(s, "a@gmail.com", 5678)
    assert s == {"a@gmail.com": 5678}
