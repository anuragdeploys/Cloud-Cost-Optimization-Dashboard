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


def main():
    start_date = "2026-09-01"
    end_date = "2026-09-02"

    response = get_daily_costs(start_date, end_date)
    records = normalize_cost_response(response)

    print("AWS Cost Explorer request successful!")
    print()

    for record in records:
        print(
            f"{record['date']} | "
            f"{record['service']} | "
            f"{record['amount']:.2f} USD"
        )


if __name__ == "__main__":
    main()
