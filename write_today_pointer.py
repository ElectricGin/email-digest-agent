import argparse
import datetime

import wiki_writer


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--vault-wiki-dir", required=True)
    parser.add_argument("--run-date", required=True, help="YYYY-MM-DD")
    args = parser.parse_args()

    run_date = datetime.date.fromisoformat(args.run_date)
    path = wiki_writer.write_today_pointer(args.vault_wiki_dir, run_date)
    print(path)


if __name__ == "__main__":
    main()
