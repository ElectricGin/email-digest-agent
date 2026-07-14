# tests/test_wiki_writer.py
import os
from datetime import date, datetime
import wiki_writer


def test_digest_page_path_builds_expected_path(tmp_path):
    result = wiki_writer.digest_page_path(str(tmp_path), date(2026, 7, 13))
    expected = os.path.join(str(tmp_path), "Digest", "email-digest-2026-07-13.md")
    assert result == expected


def test_append_digest_section_creates_page_with_header_on_first_call(tmp_path):
    path = wiki_writer.append_digest_section(
        str(tmp_path), date(2026, 7, 13), "7:30am Digest", "- Nothing urgent.",
        run_time=datetime(2026, 7, 13, 7, 31),
    )
    content = open(path, encoding="utf-8").read()
    assert "# Email Digest — 2026-07-13" in content
    assert "## 7:30am Digest — compiled 7:31 AM" in content
    assert "- Nothing urgent." in content


def test_append_digest_section_appends_without_duplicating_header(tmp_path):
    wiki_writer.append_digest_section(
        str(tmp_path), date(2026, 7, 13), "7:30am Digest", "- Morning summary.",
        run_time=datetime(2026, 7, 13, 7, 31),
    )
    path = wiki_writer.append_digest_section(
        str(tmp_path), date(2026, 7, 13), "4:00pm Digest", "- Afternoon summary.",
        run_time=datetime(2026, 7, 13, 16, 2),
    )
    content = open(path, encoding="utf-8").read()
    assert content.count("# Email Digest — 2026-07-13") == 1
    assert "## 7:30am Digest — compiled 7:31 AM" in content
    assert "## 4:00pm Digest — compiled 4:02 PM" in content
    assert "- Morning summary." in content
    assert "- Afternoon summary." in content


def test_append_digest_section_distinguishes_multiple_on_demand_runs(tmp_path):
    wiki_writer.append_digest_section(
        str(tmp_path), date(2026, 7, 13), "On-Demand Digest", "- First check.",
        run_time=datetime(2026, 7, 13, 13, 20),
    )
    path = wiki_writer.append_digest_section(
        str(tmp_path), date(2026, 7, 13), "On-Demand Digest", "- Second check.",
        run_time=datetime(2026, 7, 13, 15, 45),
    )
    content = open(path, encoding="utf-8").read()
    assert "## On-Demand Digest — compiled 1:20 PM" in content
    assert "## On-Demand Digest — compiled 3:45 PM" in content


def test_append_digest_section_puts_newest_section_first(tmp_path):
    wiki_writer.append_digest_section(
        str(tmp_path), date(2026, 7, 13), "7:30am Digest", "- Morning summary.",
        run_time=datetime(2026, 7, 13, 7, 31),
    )
    path = wiki_writer.append_digest_section(
        str(tmp_path), date(2026, 7, 13), "4:00pm Digest", "- Afternoon summary.",
        run_time=datetime(2026, 7, 13, 16, 2),
    )
    content = open(path, encoding="utf-8").read()
    assert content.index("4:00pm Digest") < content.index("7:30am Digest")


def test_today_pointer_path_builds_expected_path(tmp_path):
    result = wiki_writer.today_pointer_path(str(tmp_path))
    expected = os.path.join(str(tmp_path), "Digest", "today.md")
    assert result == expected


def test_write_today_pointer_creates_embed_link(tmp_path):
    path = wiki_writer.write_today_pointer(str(tmp_path), date(2026, 7, 13))
    content = open(path, encoding="utf-8").read()
    assert "![[email-digest-2026-07-13]]" in content


def test_write_today_pointer_overwrites_on_new_day(tmp_path):
    wiki_writer.write_today_pointer(str(tmp_path), date(2026, 7, 13))
    path = wiki_writer.write_today_pointer(str(tmp_path), date(2026, 7, 14))
    content = open(path, encoding="utf-8").read()
    assert "![[email-digest-2026-07-14]]" in content
    assert "2026-07-13" not in content
