import argparse
from datetime import datetime

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError, NoCredentialsError

from app.config import get_aws_profile, get_aws_region


def get_cost_explorer_client():
    """Create an AWS Cost Explorer client using application configuration."""
    session = boto3.Session(
        profile_name=get_aws_profile()
    )

    retry_config = Config(
        retries={
            "mode": "standard",
            "max_attempts": 3,
        }
    )

    return session.client(
        "ce",
        region_name=get_aws_region(),
        config=retry_config,
    )


def get_daily_costs(start_date, end_date):
    """
    Retrieve all daily AWS costs grouped by AWS service.

    Cost Explorer may return results across multiple pages.
    This function follows NextPageToken until all pages are retrieved.
    """
    client = get_cost_explorer_client()

    results = []
    next_page_token = None
    seen_page_tokens = set()

    while True:
        request = {
            "TimePeriod": {
                "Start": start_date,
                "End": end_date,
            },
            "Granularity": "DAILY",
            "Metrics": ["UnblendedCost"],
            "GroupBy": [
                {
                    "Type": "DIMENSION",
                    "Key": "SERVICE",
                }
            ],
        }

        if next_page_token:
            if next_page_token in seen_page_tokens:
                raise RuntimeError(
                    "AWS Cost Explorer returned a repeated pagination token."
                )

            seen_page_tokens.add(next_page_token)
            request["NextPageToken"] = next_page_token

        response = client.get_cost_and_usage(**request)

        results.extend(response.get("ResultsByTime", []))

        next_page_token = response.get("NextPageToken")

        if not next_page_token:
            break

    return {
        "ResultsByTime": results,
    }


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


def format_aws_error(error):
    """
    Convert AWS/Boto3 exceptions into user-friendly messages.
    """
    if isinstance(error, NoCredentialsError):
        return "AWS credentials could not be found."

    if isinstance(error, ClientError):
        error_details = error.response.get("Error", {})
        error_code = error_details.get("Code", "Unknown")
        error_message = error_details.get(
            "Message",
            "The AWS API request failed.",
        )

        return f"AWS API error ({error_code}): {error_message}"

    if isinstance(error, BotoCoreError):
        return f"AWS connection error: {error}"

    return f"AWS request failed: {error}"


def main():
    try:
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

        return 0

    except ValueError as error:
        print(f"Input error: {error}")
        return 1

    except (NoCredentialsError, ClientError, BotoCoreError) as error:
        print(f"Error: {format_aws_error(error)}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
