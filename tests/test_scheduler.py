from datetime import date
from unittest.mock import patch

from app.scheduler import (
    calculate_daily_collection_period,
    run_scheduled_collection,
)


def test_calculate_daily_collection_period():
    start_date, end_date = calculate_daily_collection_period(
        reference_date=date(2026, 9, 22)
    )

    assert start_date == "2026-09-21"
    assert end_date == "2026-09-22"


def test_calculate_daily_collection_period_crosses_month():
    start_date, end_date = calculate_daily_collection_period(
        reference_date=date(2026, 10, 1)
    )

    assert start_date == "2026-09-30"
    assert end_date == "2026-10-01"


def test_run_scheduled_collection_calls_service():
    fake_result = {
        "records_received": 3,
        "records_inserted": 3,
        "duplicates_ignored": 0,
        "total": 15.60,
        "currency": "USD",
    }

    with patch(
        "app.scheduler.collect_and_save_aws_costs",
        return_value=fake_result,
    ) as mock_collect:
        result = run_scheduled_collection(
            reference_date=date(2026, 9, 22),
            currency="USD",
            database_file="test.db",
        )

    assert result == fake_result

    mock_collect.assert_called_once_with(
        start_date="2026-09-21",
        end_date="2026-09-22",
        currency="USD",
        database_file="test.db",
    )
