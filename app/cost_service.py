from app.aws_cost_collector import (
    get_daily_costs,
    normalize_cost_response,
    validate_date_range,
)
from app.cost_analyzer import (
    calculate_daily_cost_changes,    
    calculate_daily_totals,
    calculate_service_concentration,
    detect_daily_spikes,
    rank_services_by_cost,
)
from app.cost_collector import process_cost_records
from app.database import get_cost_records, insert_cost_records


def save_cost_records(records, currency="USD", database_file=None):
    """
    Validate and calculate cost records, then save them to the database.

    Returns the processed cost summary together with storage statistics.
    """
    result = process_cost_records(records, currency)

    if database_file is None:
        inserted_count = insert_cost_records(
            records=records,
            currency=currency,
        )
    else:
        inserted_count = insert_cost_records(
            records=records,
            currency=currency,
            database_file=database_file,
        )

    records_received = len(records)
    duplicates_ignored = (
        records_received - inserted_count
    )

    result["records_received"] = records_received
    result["records_inserted"] = inserted_count
    result["duplicates_ignored"] = duplicates_ignored

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


def get_stored_cost_records(
    service=None,
    start_date=None,
    end_date=None,
    database_file=None,
):
    """
    Return stored cost records using database-level filtering.
    """
    return get_cost_records(
        service=service,
        start_date=start_date,
        end_date=end_date,
        database_file=database_file,
    )


def get_cost_summary(
    service=None,
    start_date=None,
    end_date=None,
    database_file=None,
):
    """
    Calculate a summary from stored cost records.

    Filtering is performed by the database before records
    are passed to the processing layer.
    """
    records = get_stored_cost_records(
        service=service,
        start_date=start_date,
        end_date=end_date,
        database_file=database_file,
    )

    return process_cost_records(
        [
            {
                "date": record["date"],
                "service": record["service"],
                "amount": record["amount"],
            }
            for record in records
        ],
        records[0]["currency"] if records else "USD",
    )


def get_cost_insights(
    service=None,
    start_date=None,
    end_date=None,
    database_file=None,
    spike_threshold=1.20,
):
    """
    Analyze stored costs and return optimization-oriented insights.

    The analysis is rule-based and transparent.
    """
    records = get_stored_cost_records(
        service=service,
        start_date=start_date,
        end_date=end_date,
        database_file=database_file,
    )

    normalized_records = [
        {
            "date": record["date"],
            "service": record["service"],
            "amount": record["amount"],
        }
        for record in records
    ]

    return {
        "service_ranking": rank_services_by_cost(
            normalized_records
        ),
        "service_concentration": (
            calculate_service_concentration(
                normalized_records
            )
        ),
        "daily_totals": calculate_daily_totals(
            normalized_records
        ),
        "daily_changes": calculate_daily_cost_changes(
            normalized_records
        ),
        "daily_spikes": detect_daily_spikes(
            normalized_records,
            threshold=spike_threshold,
        ),
    }
