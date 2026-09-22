import pytest
from unittest.mock import patch

from app.cost_service import (
    collect_and_save_aws_costs,
    get_cost_insights,
    get_cost_summary,
    get_stored_cost_records,
    save_cost_records,
)
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
    assert result["records_received"] == 2
    assert result["records_inserted"] == 2
    assert result["duplicates_ignored"] == 0

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


def test_collect_and_save_aws_costs(tmp_path):
    database_file = tmp_path / "test_costs.db"

    initialize_database(database_file)

    fake_aws_response = {
        "ResultsByTime": [
            {
                "TimePeriod": {
                    "Start": "2026-09-01",
                    "End": "2026-09-02",
                },
                "Groups": [
                    {
                        "Keys": ["Amazon EC2"],
                        "Metrics": {
                            "UnblendedCost": {
                                "Amount": "12.50",
                                "Unit": "USD",
                            }
                        },
                    },
                    {
                        "Keys": ["Amazon S3"],
                        "Metrics": {
                            "UnblendedCost": {
                                "Amount": "2.30",
                                "Unit": "USD",
                            }
                        },
                    },
                    {
                        "Keys": ["AWS Lambda"],
                        "Metrics": {
                            "UnblendedCost": {
                                "Amount": "0.80",
                                "Unit": "USD",
                            }
                        },
                    },
                ],
                "Estimated": True,
            }
        ]
    }

    with patch(
        "app.cost_service.get_daily_costs",
        return_value=fake_aws_response,
    ) as mock_get_daily_costs:
        result = collect_and_save_aws_costs(
            start_date="2026-09-01",
            end_date="2026-09-02",
            currency="USD",
            database_file=database_file,
        )

    mock_get_daily_costs.assert_called_once_with(
        "2026-09-01",
        "2026-09-02",
    )

    assert result["currency"] == "USD"
    assert result["record_count"] == 3
    assert result["total"] == pytest.approx(15.60)

    stored_records = get_cost_records(
        database_file=database_file,
    )

    assert len(stored_records) == 3

    assert stored_records[0]["service"] == "Amazon EC2"
    assert stored_records[0]["amount"] == 12.50

    assert stored_records[1]["service"] == "Amazon S3"
    assert stored_records[1]["amount"] == 2.30

    assert stored_records[2]["service"] == "AWS Lambda"
    assert stored_records[2]["amount"] == 0.80


def test_collect_and_save_aws_costs_rejects_invalid_date_range(tmp_path):
    database_file = tmp_path / "test_costs.db"

    initialize_database(database_file)

    with patch(
        "app.cost_service.get_daily_costs"
    ) as mock_get_daily_costs:
        with pytest.raises(
            ValueError,
            match="End date must be later than start date",
        ):
            collect_and_save_aws_costs(
                start_date="2026-09-10",
                end_date="2026-09-05",
                currency="USD",
                database_file=database_file,
            )

    mock_get_daily_costs.assert_not_called()

    stored_records = get_cost_records(
        database_file=database_file,
    )

    assert stored_records == []


def test_get_stored_cost_records(tmp_path):
    database_file = tmp_path / "test_costs.db"

    initialize_database(database_file)

    records = [
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
    ]

    save_cost_records(
        records=records,
        currency="USD",
        database_file=database_file,
    )

    result = get_stored_cost_records(
        database_file=database_file,
    )

    assert len(result) == 2
    assert result[0]["service"] == "Amazon EC2"
    assert result[1]["service"] == "Amazon S3"


def test_get_cost_summary_all_records(tmp_path):
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
            "date": "2026-09-02",
            "service": "AWS Lambda",
            "amount": 0.80,
        },
    ]

    save_cost_records(
        records=records,
        currency="USD",
        database_file=database_file,
    )

    result = get_cost_summary(
        database_file=database_file,
    )

    assert result["record_count"] == 3
    assert result["total"] == pytest.approx(15.60)

    assert result["cost_by_service"] == {
        "Amazon EC2": 12.50,
        "Amazon S3": 2.30,
        "AWS Lambda": 0.80,
    }

    assert result["cost_by_date"] == {
        "2026-09-01": pytest.approx(14.80),
        "2026-09-02": pytest.approx(0.80),
    }


def test_get_cost_summary_by_service(tmp_path):
    database_file = tmp_path / "test_costs.db"

    initialize_database(database_file)

    records = [
        {
            "date": "2026-09-01",
            "service": "Amazon EC2",
            "amount": 12.50,
        },
        {
            "date": "2026-09-02",
            "service": "Amazon EC2",
            "amount": 13.10,
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

    result = get_cost_summary(
        service="Amazon EC2",
        database_file=database_file,
    )

    assert result["record_count"] == 2
    assert result["total"] == pytest.approx(25.60)
    assert result["cost_by_service"] == {
        "Amazon EC2": 25.60,
    }


def test_get_cost_summary_by_date_range(tmp_path):
    database_file = tmp_path / "test_costs.db"

    initialize_database(database_file)

    records = [
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
    ]

    save_cost_records(
        records=records,
        currency="USD",
        database_file=database_file,
    )

    result = get_cost_summary(
        start_date="2026-09-01",
        end_date="2026-09-03",
        database_file=database_file,
    )

    assert result["record_count"] == 2
    assert result["total"] == pytest.approx(14.80)

    assert result["cost_by_service"] == {
        "Amazon EC2": 12.50,
        "Amazon S3": 2.30,
    }

    assert result["cost_by_date"] == {
        "2026-09-01": 12.50,
        "2026-09-02": 2.30,
    }
   
def test_get_stored_cost_records_passes_filters_to_database():
    expected_records = [
        {
            "id": 1,
            "date": "2026-09-02",
            "service": "Amazon EC2",
            "amount": 13.10,
            "currency": "USD",
        }
    ]

    with patch(
        "app.cost_service.get_cost_records",
        return_value=expected_records,
    ) as mock_get_cost_records:
        result = get_stored_cost_records(
            service="Amazon EC2",
            start_date="2026-09-02",
            end_date="2026-09-03",
            database_file="test.db",
        )

    assert result == expected_records

    mock_get_cost_records.assert_called_once_with(
        service="Amazon EC2",
        start_date="2026-09-02",
        end_date="2026-09-03",
        database_file="test.db",
    ) 

def test_get_cost_insights(tmp_path):
    database_file = tmp_path / "test_costs.db"

    initialize_database(database_file)

    records = [
        {
            "date": "2026-09-01",
            "service": "Amazon EC2",
            "amount": 10.00,
        },
        {
            "date": "2026-09-01",
            "service": "Amazon S3",
            "amount": 2.00,
        },
        {
            "date": "2026-09-02",
            "service": "Amazon EC2",
            "amount": 11.00,
        },
        {
            "date": "2026-09-02",
            "service": "Amazon S3",
            "amount": 2.50,
        },
        {
            "date": "2026-09-03",
            "service": "Amazon EC2",
            "amount": 30.00,
        },
    ]

    save_cost_records(
        records=records,
        currency="USD",
        database_file=database_file,
    )

    result = get_cost_insights(
        database_file=database_file,
        spike_threshold=1.20,
    )

    assert result["service_ranking"][0][0] == "Amazon EC2"
    assert result["service_ranking"][0][1] == pytest.approx(51.00)

    assert result["service_ranking"][1][0] == "Amazon S3"
    assert result["service_ranking"][1][1] == pytest.approx(4.50)

    assert result["daily_totals"]["2026-09-01"] == pytest.approx(12.00)
    assert result["daily_totals"]["2026-09-02"] == pytest.approx(13.50)
    assert result["daily_totals"]["2026-09-03"] == pytest.approx(30.00)

    assert result["daily_changes"][0]["date"] == "2026-09-01"
    assert result["daily_changes"][0]["percentage_change"] is None

    assert result["daily_changes"][1]["date"] == "2026-09-02"
    assert result["daily_changes"][1]["percentage_change"] == pytest.approx(
        12.50
    )

    assert result["daily_changes"][2]["date"] == "2026-09-03"
    assert result["daily_changes"][2]["percentage_change"] == pytest.approx(
        122.2222222222
    )

    assert len(result["daily_spikes"]) == 1
    assert result["daily_spikes"][0]["date"] == "2026-09-03"

def test_save_cost_records_reports_duplicates(tmp_path):
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

    first_result = save_cost_records(
        records=records,
        currency="USD",
        database_file=database_file,
    )

    second_result = save_cost_records(
        records=records,
        currency="USD",
        database_file=database_file,
    )

    assert first_result["records_received"] == 2
    assert first_result["records_inserted"] == 2
    assert first_result["duplicates_ignored"] == 0

    assert second_result["records_received"] == 2
    assert second_result["records_inserted"] == 0
    assert second_result["duplicates_ignored"] == 2    
