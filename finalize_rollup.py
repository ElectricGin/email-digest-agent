import argparse
import datetime
import sys

import rollup


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--personal-dir", required=True)
    parser.add_argument("--page-path", required=True)
    parser.add_argument("--page-date", required=True, help="YYYY-MM-DD, parsed from the page's filename")
    args = parser.parse_args()

    summary_markdown = sys.stdin.read()
    page_date = datetime.date.fromisoformat(args.page_date)
    week_start, week_end = rollup.week_bounds(page_date)
    weekly_path = rollup.upsert_weekly_summary(args.personal_dir, week_start, week_end, summary_markdown)
    rollup.delete_pages([args.page_path])
    print(f"merged {args.page_path} into {weekly_path}")


if __name__ == "__main__":
    main()
