# tests/test_rollup.py
import os
from datetime import date
import rollup


def _write_page(dir_path, name, content="content"):
    os.makedirs(dir_path, exist_ok=True)
    path = os.path.join(dir_path, name)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path


def test_find_stale_digest_pages_returns_only_pages_older_than_retention(tmp_path):
    personal_dir = str(tmp_path)
    _write_page(personal_dir, "email-digest-2026-07-01.md")
    _write_page(personal_dir, "email-digest-2026-07-10.md")
    _write_page(personal_dir, "email-digest-weekly-2026-06-24-to-2026-06-30.md")
    _write_page(personal_dir, "not-a-digest.md")

    result = rollup.find_stale_digest_pages(personal_dir, today=date(2026, 7, 13), retention_days=7)

    assert result == [os.path.join(personal_dir, "email-digest-2026-07-01.md")]


def test_read_stale_pages_returns_content_keyed_by_path(tmp_path):
    personal_dir = str(tmp_path)
    path = _write_page(personal_dir, "email-digest-2026-07-01.md", content="hello world")

    result = rollup.read_stale_pages([path])

    assert result == {path: "hello world"}


def test_week_bounds_returns_monday_to_sunday_for_a_monday():
    start, end = rollup.week_bounds(date(2024, 1, 1))  # known Monday
    assert start == date(2024, 1, 1)
    assert end == date(2024, 1, 7)


def test_week_bounds_returns_monday_to_sunday_for_a_thursday():
    start, end = rollup.week_bounds(date(2024, 1, 4))  # Thursday, same week as above
    assert start == date(2024, 1, 1)
    assert end == date(2024, 1, 7)


def test_upsert_weekly_summary_creates_file_when_absent(tmp_path):
    personal_dir = str(tmp_path)

    path = rollup.upsert_weekly_summary(
        personal_dir, date(2026, 6, 22), date(2026, 6, 28), "- Monday: key thing."
    )

    assert os.path.basename(path) == "email-digest-weekly-2026-06-22-to-2026-06-28.md"
    content = open(path, encoding="utf-8").read()
    assert "Email Digest Weekly Summary (2026-06-22 to 2026-06-28)" in content
    assert "- Monday: key thing." in content


def test_upsert_weekly_summary_appends_when_present(tmp_path):
    personal_dir = str(tmp_path)
    rollup.upsert_weekly_summary(personal_dir, date(2026, 6, 22), date(2026, 6, 28), "- Monday: key thing.")

    path = rollup.upsert_weekly_summary(
        personal_dir, date(2026, 6, 22), date(2026, 6, 28), "- Tuesday: another thing."
    )

    content = open(path, encoding="utf-8").read()
    assert content.count("Email Digest Weekly Summary (2026-06-22 to 2026-06-28)") == 1
    assert "- Monday: key thing." in content
    assert "- Tuesday: another thing." in content


def test_delete_pages_removes_files(tmp_path):
    personal_dir = str(tmp_path)
    path = _write_page(personal_dir, "email-digest-2026-07-01.md")

    rollup.delete_pages([path])

    assert not os.path.exists(path)
