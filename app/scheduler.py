from datetime import date, timedelta

from app.cost_service import collect_and_save_aws_costs


def calculate_daily_collection_period(reference_date=None):
    """
    Calculate the previous day's collection period.

    The end date is exclusive.
    """
    if reference_date is None:
        reference_date = date.today()

    start_date = reference_date - timedelta(days=1)
    end_date = reference_date

    return (
        start_date.isoformat(),
        end_date.isoformat(),
    )


def run_scheduled_collection(
    reference_date=None,
    currency="USD",
    database_file=None,
):
    """
    Collect and store the previous day's AWS costs.
    """
    start_date, end_date = calculate_daily_collection_period(
        reference_date
    )

    return collect_and_save_aws_costs(
        start_date=start_date,
        end_date=end_date,
        currency=currency,
        database_file=database_file,
    )
