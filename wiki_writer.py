import os
from datetime import datetime


def digest_page_path(vault_wiki_dir, run_date):
    return os.path.join(vault_wiki_dir, "Digest", f"email-digest-{run_date.isoformat()}.md")


def append_digest_section(vault_wiki_dir, run_date, run_label, body_markdown, run_time=None):
    path = digest_page_path(vault_wiki_dir, run_date)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    run_time = run_time or datetime.now()
    compiled_at = run_time.strftime("%#I:%M %p")
    header = f"# Email Digest — {run_date.isoformat()}\n"
    section = f"## {run_label} — compiled {compiled_at}\n\n{body_markdown}\n"

    if not os.path.exists(path):
        older_sections = ""
    else:
        with open(path, encoding="utf-8") as f:
            existing = f.read()
        older_sections = existing[len(header):] if existing.startswith(header) else existing
        older_sections = older_sections.lstrip("\n")

    with open(path, "w", encoding="utf-8") as f:
        f.write(header + "\n" + section + (f"\n{older_sections}" if older_sections else ""))

    return path


def today_pointer_path(vault_wiki_dir):
    return os.path.join(vault_wiki_dir, "Digest", "today.md")


def write_today_pointer(vault_wiki_dir, run_date):
    path = today_pointer_path(vault_wiki_dir)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    content = (
        "# Today's Digest\n\n"
        f"![[email-digest-{run_date.isoformat()}]]\n\n"
        "*Auto-updated by the digest routine — do not edit directly. "
        "Open this page's Bookmarks entry for one-click access.*\n"
    )
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path
