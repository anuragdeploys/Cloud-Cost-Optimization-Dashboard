from app.aws_cost_collector import (
    get_daily_costs,
    normalize_cost_response,
    validate_date_range,
)
from app.cost_collector import process_cost_records
from app.database import insert_cost_records


def save_cost_records(records, currency="USD", database_file=None):
    """
    Validate and calculate cost records, then save them to the database.

    Returns the processed cost summary.
    """
    result = process_cost_records(records, currency)

    if database_file is None:
        insert_cost_records(
            records=records,
            currency=currency,
        )
    else:
        insert_cost_records(
            records=records,
            currency=currency,
            database_file=database_file,
        )

    return result


def collect_and_save_aws_costs(
    start_date,
    end_date,
    currency="USD",
    database_file=None,
):
    """
    Collect AWS costs, normalize them, process them,
    and persist them to SQLite.
    """
    validate_date_range(start_date, end_date)

    response = get_daily_costs(
        start_date,
        end_date,
    )

    records = normalize_cost_response(response)

    return save_cost_records(
        records=records,
        currency=currency,
        database_file=database_file,
    )
