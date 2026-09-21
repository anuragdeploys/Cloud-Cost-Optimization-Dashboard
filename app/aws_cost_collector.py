import argparse
from datetime import datetime

import boto3


AWS_PROFILE = "cost-dashboard"
AWS_REGION = "us-east-1"


def get_cost_explorer_client():
    """Create an AWS Cost Explorer client using the project IAM profile."""
    session = boto3.Session(profile_name=AWS_PROFILE)
    return session.client("ce", region_name=AWS_REGION)


def get_daily_costs(start_date, end_date):
    """
    Retrieve daily AWS costs grouped by AWS service.

    The end_date is exclusive, following the AWS Cost Explorer API format.
    """
    client = get_cost_explorer_client()

    response = client.get_cost_and_usage(
        TimePeriod={
            "Start": start_date,
            "End": end_date,
        },
        Granularity="DAILY",
        Metrics=["UnblendedCost"],
        GroupBy=[
            {
                "Type": "DIMENSION",
                "Key": "SERVICE",
            }
        ],
    )

    return response


def normalize_cost_response(response):
    """
    Convert an AWS Cost Explorer response into application records.

    Each record contains:
        date
        service
        amount
    """
    records = []

    for result in response.get("ResultsByTime", []):
        date = result["TimePeriod"]["Start"]

        for group in result.get("Groups", []):
            service = group["Keys"][0]

            amount = float(
                group["Metrics"]["UnblendedCost"]["Amount"]
            )

            records.append(
                {
                    "date": date,
                    "service": service,
                    "amount": amount,
                }
            )

    return records


def validate_date_range(start_date, end_date):
    """
    Validate an AWS Cost Explorer date range.

    Dates must use YYYY-MM-DD format.
    The end date must be later than the start date.
    """
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError as error:
        raise ValueError(
            "Dates must use YYYY-MM-DD format."
        ) from error

    if start >= end:
        raise ValueError(
            "End date must be later than start date."
        )


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Collect AWS daily costs by service."
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

    return parser.parse_args()


def main():
    args = parse_arguments()

    validate_date_range(
        args.start_date,
        args.end_date,
    )

    response = get_daily_costs(
        args.start_date,
        args.end_date,
    )

    records = normalize_cost_response(response)

    print("AWS Cost Explorer request successful!")
    print(f"Period: {args.start_date} to {args.end_date}")
    print()

    for record in records:
        print(
            f"{record['date']} | "
            f"{record['service']} | "
            f"{record['amount']:.2f} USD"
        )


if __name__ == "__main__":
    main()
