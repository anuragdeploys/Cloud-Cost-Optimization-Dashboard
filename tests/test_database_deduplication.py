from app.database import (
    get_cost_records,
    initialize_database,
    insert_cost_record,
    insert_cost_records,
)


def test_duplicate_cost_record_is_ignored(tmp_path):
    database_file = tmp_path / "test_costs.db"

    initialize_database(database_file)

    record = {
        "date": "2026-09-01",
        "service": "Amazon EC2",
        "amount": 12.50,
    }

    insert_cost_record(
        date=record["date"],
        service=record["service"],
        amount=record["amount"],
        currency="USD",
        database_file=database_file,
    )

    insert_cost_record(
        date=record["date"],
        service=record["service"],
        amount=record["amount"],
        currency="USD",
        database_file=database_file,
    )

    stored_records = get_cost_records(
        database_file=database_file,
    )

    assert len(stored_records) == 1
    assert stored_records[0]["service"] == "Amazon EC2"
    assert stored_records[0]["amount"] == 12.50


def test_bulk_insert_ignores_duplicates_but_keeps_new_records(tmp_path):
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
        {
            "date": "2026-09-01",
            "service": "Amazon EC2",
            "amount": 12.50,
        },
    ]

    insert_cost_records(
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

    assert stored_records[1]["service"] == "Amazon S3"
    assert stored_records[1]["amount"] == 2.30
