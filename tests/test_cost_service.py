import pytest

from app.cost_service import save_cost_records
from app.database import get_cost_records, initialize_database


def test_save_cost_records_returns_processed_summary(tmp_path):
    database_file = tmp_path / "test_costs.db"

    initialize_database(database_file)

    records = [
        {
            "date": "2026-09-01",
            "service": "Amazon EC2",
            "amount": 12.50,
        },
        {
            "date": "2026-09-01",
            "service": "Amazon S3",
            "amount": 2.30,
        },
    ]

    result = save_cost_records(
        records=records,
        currency="USD",
        database_file=database_file,
    )

    assert result["currency"] == "USD"
    assert result["record_count"] == 2
    assert result["total"] == pytest.approx(14.80)

    assert result["cost_by_service"] == {
        "Amazon EC2": 12.50,
        "Amazon S3": 2.30,
    }

    assert result["cost_by_date"]["2026-09-01"] == pytest.approx(14.80)


def test_save_cost_records_persists_records(tmp_path):
    database_file = tmp_path / "test_costs.db"

    initialize_database(database_file)

    records = [
        {
            "date": "2026-09-01",
            "service": "Amazon EC2",
            "amount": 12.50,
        },
        {
            "date": "2026-09-01",
            "service": "Amazon S3",
            "amount": 2.30,
        },
    ]

    save_cost_records(
        records=records,
        currency="USD",
        database_file=database_file,
    )

    stored_records = get_cost_records(
        database_file=database_file,
    )

    assert len(stored_records) == 2

    assert stored_records[0]["service"] == "Amazon EC2"
    assert stored_records[0]["amount"] == 12.50
    assert stored_records[0]["currency"] == "USD"

    assert stored_records[1]["service"] == "Amazon S3"
    assert stored_records[1]["amount"] == 2.30
    assert stored_records[1]["currency"] == "USD"


def test_save_cost_records_rejects_invalid_records(tmp_path):
    database_file = tmp_path / "test_costs.db"

    initialize_database(database_file)

    invalid_records = [
        {
            "date": "2026-09-01",
            "service": "Amazon EC2",
            "amount": -12.50,
        }
    ]

    with pytest.raises(
        ValueError,
        match="amount cannot be negative",
    ):
        save_cost_records(
            records=invalid_records,
            currency="USD",
            database_file=database_file,
        )

    stored_records = get_cost_records(
        database_file=database_file,
    )

    assert stored_records == []
