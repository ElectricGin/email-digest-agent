import argparse
import datetime
import json

import rollup


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--personal-dir", required=True)
    parser.add_argument("--retention-days", type=int, default=7)
    args = parser.parse_args()

    stale = rollup.find_stale_digest_pages(
        args.personal_dir, datetime.date.today(), args.retention_days
    )
    print(json.dumps(stale))


if __name__ == "__main__":
    main()
