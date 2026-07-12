import os
import re
from datetime import date, timedelta

DIGEST_FILENAME_RE = re.compile(r"^email-digest-(\d{4}-\d{2}-\d{2})\.md$")


def find_stale_digest_pages(personal_dir, today, retention_days=7):
    cutoff = today - timedelta(days=retention_days)
    stale = []
    for filename in os.listdir(personal_dir):
        match = DIGEST_FILENAME_RE.match(filename)
        if not match:
            continue
        page_date = date.fromisoformat(match.group(1))
        if page_date < cutoff:
            stale.append(os.path.join(personal_dir, filename))
    return sorted(stale)


def read_stale_pages(stale_paths):
    contents = {}
    for path in stale_paths:
        with open(path, encoding="utf-8") as f:
            contents[path] = f.read()
    return contents


def week_bounds(d):
    start = d - timedelta(days=d.weekday())
    end = start + timedelta(days=6)
    return start, end


def upsert_weekly_summary(personal_dir, week_start, week_end, additional_markdown):
    filename = f"email-digest-weekly-{week_start.isoformat()}-to-{week_end.isoformat()}.md"
    path = os.path.join(personal_dir, filename)

    if not os.path.exists(path):
        header = f"# Email Digest Weekly Summary ({week_start.isoformat()} to {week_end.isoformat()})\n\n"
        with open(path, "w", encoding="utf-8") as f:
            f.write(header + additional_markdown + "\n")
    else:
        with open(path, "a", encoding="utf-8") as f:
            f.write("\n" + additional_markdown + "\n")

    return path


def delete_pages(paths):
    for path in paths:
        os.remove(path)
