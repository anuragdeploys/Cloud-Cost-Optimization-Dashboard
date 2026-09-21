import pytest

from app.api import create_app
from app.database import initialize_database, insert_cost_records


def test_health_endpoint(tmp_path):
    database_file = tmp_path / "test_costs.db"

    app = create_app(database_file)
    client = app.test_client()

    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json() == {
        "status": "ok",
    }


def test_costs_endpoint_returns_records(tmp_path):
    database_file = tmp_path / "test_costs.db"

    initialize_database(database_file)

    insert_cost_records(
        records=[
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
        ],
        currency="USD",
        database_file=database_file,
    )

    app = create_app(database_file)
    client = app.test_client()

    response = client.get("/costs")

    assert response.status_code == 200

    data = response.get_json()

    assert data["count"] == 2
    assert len(data["records"]) == 2

    assert data["records"][0]["service"] == "Amazon EC2"
    assert data["records"][1]["service"] == "Amazon S3"


def test_costs_endpoint_filters_by_service(tmp_path):
    database_file = tmp_path / "test_costs.db"

    initialize_database(database_file)

    insert_cost_records(
        records=[
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
                "date": "2026-09-02",
                "service": "Amazon EC2",
                "amount": 13.10,
            },
        ],
        currency="USD",
        database_file=database_file,
    )

    app = create_app(database_file)
    client = app.test_client()

    response = client.get("/costs?service=Amazon%20EC2")

    assert response.status_code == 200

    data = response.get_json()

    assert data["count"] == 2
    assert all(
        record["service"] == "Amazon EC2"
        for record in data["records"]
    )


def test_costs_endpoint_filters_by_date_range(tmp_path):
    database_file = tmp_path / "test_costs.db"

    initialize_database(database_file)

    insert_cost_records(
        records=[
            {
                "date": "2026-09-01",
                "service": "Amazon EC2",
                "amount": 12.50,
            },
            {
                "date": "2026-09-02",
                "service": "Amazon S3",
                "amount": 2.30,
            },
            {
                "date": "2026-09-03",
                "service": "AWS Lambda",
                "amount": 0.80,
            },
        ],
        currency="USD",
        database_file=database_file,
    )

    app = create_app(database_file)
    client = app.test_client()

    response = client.get(
        "/costs?start_date=2026-09-01&end_date=2026-09-03"
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["count"] == 2
    assert data["records"][0]["date"] == "2026-09-01"
    assert data["records"][1]["date"] == "2026-09-02"


def test_costs_endpoint_requires_both_dates(tmp_path):
    database_file = tmp_path / "test_costs.db"

    app = create_app(database_file)
    client = app.test_client()

    response = client.get("/costs?start_date=2026-09-01")

    assert response.status_code == 400

    assert response.get_json() == {
        "error": (
            "start_date and end_date "
            "must be provided together."
        )
    }


def test_costs_endpoint_rejects_invalid_date_format(tmp_path):
    database_file = tmp_path / "test_costs.db"

    app = create_app(database_file)
    client = app.test_client()

    response = client.get(
        "/costs?start_date=2026-99-99&end_date=2026-09-10"
    )

    assert response.status_code == 400

    assert response.get_json() == {
        "error": "Dates must use YYYY-MM-DD format."
    }


def test_costs_endpoint_rejects_invalid_date_order(tmp_path):
    database_file = tmp_path / "test_costs.db"

    app = create_app(database_file)
    client = app.test_client()

    response = client.get(
        "/costs?start_date=2026-09-10&end_date=2026-09-05"
    )

    assert response.status_code == 400

    assert response.get_json() == {
        "error": "End date must be later than start date."
    }


def test_cost_summary_endpoint(tmp_path):
    database_file = tmp_path / "test_costs.db"

    initialize_database(database_file)

    insert_cost_records(
        records=[
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
                "date": "2026-09-02",
                "service": "AWS Lambda",
                "amount": 0.80,
            },
        ],
        currency="USD",
        database_file=database_file,
    )

    app = create_app(database_file)
    client = app.test_client()

    response = client.get("/costs/summary")

    assert response.status_code == 200

    data = response.get_json()

    assert data["currency"] == "USD"
    assert data["record_count"] == 3
    assert data["total"] == pytest.approx(15.60)

    assert data["cost_by_service"] == {
        "Amazon EC2": 12.50,
        "Amazon S3": 2.30,
        "AWS Lambda": 0.80,
    }


def test_cost_summary_requires_both_dates(tmp_path):
    database_file = tmp_path / "test_costs.db"

    app = create_app(database_file)
    client = app.test_client()

    response = client.get(
        "/costs/summary?start_date=2026-09-01"
    )

    assert response.status_code == 400

    assert response.get_json() == {
        "error": (
            "start_date and end_date "
            "must be provided together."
        )
    }


def test_cost_summary_rejects_invalid_date_format(tmp_path):
    database_file = tmp_path / "test_costs.db"

    app = create_app(database_file)
    client = app.test_client()

    response = client.get(
        "/costs/summary?"
        "start_date=2026-99-99&"
        "end_date=2026-09-10"
    )

    assert response.status_code == 400

    assert response.get_json() == {
        "error": "Dates must use YYYY-MM-DD format."
    }


def test_cost_summary_rejects_invalid_date_order(tmp_path):
    database_file = tmp_path / "test_costs.db"

    app = create_app(database_file)
    client = app.test_client()

    response = client.get(
        "/costs/summary?"
        "start_date=2026-09-10&"
        "end_date=2026-09-05"
    )

    assert response.status_code == 400

    assert response.get_json() == {
        "error": "End date must be later than start date."
    }
