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
