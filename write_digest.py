import argparse
import datetime
import sys

import wiki_writer


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--vault-wiki-dir", required=True)
    parser.add_argument("--run-date", required=True, help="YYYY-MM-DD")
    parser.add_argument("--run-label", required=True)
    args = parser.parse_args()

    # Windows decodes piped stdin as cp1252 by default, which mangles or crashes
    # on UTF-8 email content (em-dashes, emoji) — read raw bytes and decode as UTF-8.
    body_markdown = sys.stdin.buffer.read().decode("utf-8")
    run_date = datetime.date.fromisoformat(args.run_date)
    path = wiki_writer.append_digest_section(
        args.vault_wiki_dir, run_date, args.run_label, body_markdown
    )
    print(path)


if __name__ == "__main__":
    main()
