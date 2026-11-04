"""
Entry point: orchestrates scrape -> clean -> export.
"""

import argparse
import logging
import sys

from cleaner import clean_dataframe
from config import SITES
from exporter import export_dataframe
from scraper import scrape_site


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Config-driven web scraper + cleaner."
    )
    parser.add_argument(
        "--site",
        required=True,
        choices=sorted(SITES.keys()),
        help="Registered site config name.",
    )
    parser.add_argument(
        "--output-dir", default="output", help="Output directory (default: output)."
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    )

    config = SITES[args.site]
    logging.info(f"=== Starting scrape: {config.name} ===")

    raw_records = scrape_site(config)
    if not raw_records:
        logging.error("No records extracted; aborting.")
        return 1

    df = clean_dataframe(raw_records, config)
    export_dataframe(df, args.output_dir, config.name)

    logging.info(f"=== Done: {len(df)} clean rows saved ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())