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

    body_markdown = sys.stdin.read()
    run_date = datetime.date.fromisoformat(args.run_date)
    path = wiki_writer.append_digest_section(
        args.vault_wiki_dir, run_date, args.run_label, body_markdown
    )
    print(path)


if __name__ == "__main__":
    main()
