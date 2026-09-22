from unittest.mock import patch

import pytest

from app.cost_service import collect_and_save_aws_costs
from app.database import get_cost_records, initialize_database


def test_repeated_collection_does_not_duplicate_records(tmp_path):
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

        first_result = collect_and_save_aws_costs(
            start_date="2026-09-01",
            end_date="2026-09-02",
            currency="USD",
            database_file=database_file,
        )

        second_result = collect_and_save_aws_costs(
            start_date="2026-09-01",
            end_date="2026-09-02",
            currency="USD",
            database_file=database_file,
        )

    assert mock_get_daily_costs.call_count == 2

    assert first_result["record_count"] == 3
    assert first_result["total"] == pytest.approx(15.60)

    assert second_result["record_count"] == 3
    assert second_result["total"] == pytest.approx(15.60)

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
