import argparse

from app.cost_service import collect_and_save_aws_costs


def parse_arguments():
    """Parse collection command arguments."""
    parser = argparse.ArgumentParser(
        description="Collect AWS costs and save them to SQLite."
    )

    parser.add_argument(
        "--start-date",
        required=True,
        help="Start date in YYYY-MM-DD format.",
    )

    parser.add_argument(
        "--end-date",
        required=True,
        help="End date in YYYY-MM-DD format. This date is exclusive.",
    )

    parser.add_argument(
        "--currency",
        default="USD",
        help="Currency for stored cost records.",
    )

    return parser.parse_args()


def main():
    """Run the AWS cost collection workflow."""
    args = parse_arguments()

    result = collect_and_save_aws_costs(
        start_date=args.start_date,
        end_date=args.end_date,
        currency=args.currency,
    )

    print("Cost collection completed successfully.")
    print(f"Period: {args.start_date} to {args.end_date}")
    print(f"Records collected: {result['record_count']}")
    print(f"Total cost: {result['total']:.2f} {result['currency']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
