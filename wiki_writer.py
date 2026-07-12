import os


def digest_page_path(vault_wiki_dir, run_date):
    return os.path.join(vault_wiki_dir, "Personal", f"email-digest-{run_date.isoformat()}.md")


def append_digest_section(vault_wiki_dir, run_date, run_label, body_markdown):
    path = digest_page_path(vault_wiki_dir, run_date)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    section = f"\n## {run_label}\n\n{body_markdown}\n"

    if not os.path.exists(path):
        header = f"# Email Digest — {run_date.isoformat()}\n"
        with open(path, "w", encoding="utf-8") as f:
            f.write(header + section)
    else:
        with open(path, "a", encoding="utf-8") as f:
            f.write(section)

    return path
