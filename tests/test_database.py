import sqlite3

from app.database import (
    get_cost_records,
    initialize_database,
    insert_cost_record,
)


def test_initialize_database_creates_table(tmp_path):
    database_file = tmp_path / "test_costs.db"

    initialize_database(database_file)

    connection = sqlite3.connect(database_file)

    try:
        tables = connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
            """
        ).fetchall()

        table_names = [table[0] for table in tables]

        assert "cost_records" in table_names

    finally:
        connection.close()


def test_insert_cost_record(tmp_path):
    database_file = tmp_path / "test_costs.db"

    initialize_database(database_file)

    insert_cost_record(
        date="2026-09-01",
        service="Amazon EC2",
        amount=12.50,
        currency="USD",
        database_file=database_file,
    )

    connection = sqlite3.connect(database_file)

    try:
        row = connection.execute(
            """
            SELECT date, service, amount, currency
            FROM cost_records
            """
        ).fetchone()

        assert row == (
            "2026-09-01",
            "Amazon EC2",
            12.50,
            "USD",
        )

    finally:
        connection.close()


def test_insert_multiple_cost_records(tmp_path):
    database_file = tmp_path / "test_costs.db"

    initialize_database(database_file)

    insert_cost_record(
        date="2026-09-01",
        service="Amazon EC2",
        amount=12.50,
        currency="USD",
        database_file=database_file,
    )

    insert_cost_record(
        date="2026-09-01",
        service="Amazon S3",
        amount=2.30,
        currency="USD",
        database_file=database_file,
    )

    connection = sqlite3.connect(database_file)

    try:
        rows = connection.execute(
            """
            SELECT date, service, amount, currency
            FROM cost_records
            ORDER BY id
            """
        ).fetchall()

        assert rows == [
            ("2026-09-01", "Amazon EC2", 12.50, "USD"),
            ("2026-09-01", "Amazon S3", 2.30, "USD"),
        ]

    finally:
        connection.close()


def test_get_all_cost_records(tmp_path):
    database_file = tmp_path / "test_costs.db"

    initialize_database(database_file)

    insert_cost_record(
        date="2026-09-01",
        service="Amazon EC2",
        amount=12.50,
        currency="USD",
        database_file=database_file,
    )

    insert_cost_record(
        date="2026-09-02",
        service="Amazon S3",
        amount=2.30,
        currency="USD",
        database_file=database_file,
    )

    records = get_cost_records(
        database_file=database_file,
    )

    assert len(records) == 2

    assert records[0]["date"] == "2026-09-01"
    assert records[0]["service"] == "Amazon EC2"
    assert records[0]["amount"] == 12.50
    assert records[0]["currency"] == "USD"

    assert records[1]["date"] == "2026-09-02"
    assert records[1]["service"] == "Amazon S3"
    assert records[1]["amount"] == 2.30
    assert records[1]["currency"] == "USD"


def test_get_cost_records_by_service(tmp_path):
    database_file = tmp_path / "test_costs.db"

    initialize_database(database_file)

    insert_cost_record(
        date="2026-09-01",
        service="Amazon EC2",
        amount=12.50,
        currency="USD",
        database_file=database_file,
    )

    insert_cost_record(
        date="2026-09-01",
        service="Amazon S3",
        amount=2.30,
        currency="USD",
        database_file=database_file,
    )

    insert_cost_record(
        date="2026-09-02",
        service="Amazon EC2",
        amount=13.10,
        currency="USD",
        database_file=database_file,
    )

    records = get_cost_records(
        service="Amazon EC2",
        database_file=database_file,
    )

    assert len(records) == 2
    assert records[0]["service"] == "Amazon EC2"
    assert records[1]["service"] == "Amazon EC2"
    assert records[0]["amount"] == 12.50
    assert records[1]["amount"] == 13.10


def test_get_cost_records_by_date_range(tmp_path):
    database_file = tmp_path / "test_costs.db"

    initialize_database(database_file)

    insert_cost_record(
        date="2026-09-01",
        service="Amazon EC2",
        amount=12.50,
        currency="USD",
        database_file=database_file,
    )

    insert_cost_record(
        date="2026-09-02",
        service="Amazon S3",
        amount=2.30,
        currency="USD",
        database_file=database_file,
    )

    insert_cost_record(
        date="2026-09-03",
        service="AWS Lambda",
        amount=0.80,
        currency="USD",
        database_file=database_file,
    )

    records = get_cost_records(
        start_date="2026-09-01",
        end_date="2026-09-03",
        database_file=database_file,
    )

    assert len(records) == 2
    assert records[0]["date"] == "2026-09-01"
    assert records[1]["date"] == "2026-09-02"


def test_get_cost_records_with_combined_filters(tmp_path):
    database_file = tmp_path / "test_costs.db"

    initialize_database(database_file)

    insert_cost_record(
        date="2026-09-01",
        service="Amazon EC2",
        amount=12.50,
        currency="USD",
        database_file=database_file,
    )

    insert_cost_record(
        date="2026-09-02",
        service="Amazon EC2",
        amount=13.10,
        currency="USD",
        database_file=database_file,
    )

    insert_cost_record(
        date="2026-09-02",
        service="Amazon S3",
        amount=2.30,
        currency="USD",
        database_file=database_file,
    )

    records = get_cost_records(
        service="Amazon EC2",
        start_date="2026-09-02",
        end_date="2026-09-03",
        database_file=database_file,
    )

    assert len(records) == 1
    assert records[0]["date"] == "2026-09-02"
    assert records[0]["service"] == "Amazon EC2"
    assert records[0]["amount"] == 13.10
