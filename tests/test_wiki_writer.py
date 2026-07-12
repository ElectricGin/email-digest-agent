# tests/test_wiki_writer.py
import os
from datetime import date
import wiki_writer


def test_digest_page_path_builds_expected_path(tmp_path):
    result = wiki_writer.digest_page_path(str(tmp_path), date(2026, 7, 13))
    expected = os.path.join(str(tmp_path), "Personal", "email-digest-2026-07-13.md")
    assert result == expected


def test_append_digest_section_creates_page_with_header_on_first_call(tmp_path):
    path = wiki_writer.append_digest_section(
        str(tmp_path), date(2026, 7, 13), "7:30am Digest", "- Nothing urgent."
    )
    content = open(path, encoding="utf-8").read()
    assert "# Email Digest — 2026-07-13" in content
    assert "## 7:30am Digest" in content
    assert "- Nothing urgent." in content


def test_append_digest_section_appends_without_duplicating_header(tmp_path):
    wiki_writer.append_digest_section(
        str(tmp_path), date(2026, 7, 13), "7:30am Digest", "- Morning summary."
    )
    path = wiki_writer.append_digest_section(
        str(tmp_path), date(2026, 7, 13), "4:00pm Digest", "- Afternoon summary."
    )
    content = open(path, encoding="utf-8").read()
    assert content.count("# Email Digest — 2026-07-13") == 1
    assert "## 7:30am Digest" in content
    assert "## 4:00pm Digest" in content
    assert "- Morning summary." in content
    assert "- Afternoon summary." in content
