import pytest

from app.aws_cost_collector import (
    normalize_cost_response,
    parse_arguments,
    validate_date_range,
)
from app.cost_collector import (
    calculate_cost_by_date,
    calculate_cost_by_service,
    calculate_total,
    process_cost_records,
    validate_cost_data,
)


def test_calculate_total():
    records = [
        {"date": "2026-09-01", "service": "Amazon EC2", "amount": 10.00},
        {"date": "2026-09-01", "service": "Amazon S3", "amount": 5.00},
    ]

    assert calculate_total(records) == 15.00


def test_calculate_cost_by_service():
    records = [
        {"date": "2026-09-01", "service": "Amazon EC2", "amount": 10.00},
        {"date": "2026-09-01", "service": "Amazon EC2", "amount": 5.00},
        {"date": "2026-09-01", "service": "Amazon S3", "amount": 3.00},
    ]

    result = calculate_cost_by_service(records)

    assert result["Amazon EC2"] == 15.00
    assert result["Amazon S3"] == 3.00


def test_calculate_cost_by_date():
    records = [
        {"date": "2026-09-01", "service": "Amazon EC2", "amount": 10.00},
        {"date": "2026-09-01", "service": "Amazon S3", "amount": 5.00},
        {"date": "2026-09-02", "service": "Amazon EC2", "amount": 7.00},
    ]

    result = calculate_cost_by_date(records)

    assert result["2026-09-01"] == 15.00
    assert result["2026-09-02"] == 7.00


def test_valid_cost_data():
    data = {
        "currency": "USD",
        "records": [
            {
                "date": "2026-09-01",
                "service": "Amazon EC2",
                "amount": 10.00,
            }
        ],
    }

    validate_cost_data(data)


def test_invalid_amount_type():
    data = {
        "currency": "USD",
        "records": [
            {
                "date": "2026-09-01",
                "service": "Amazon EC2",
                "amount": "10.00",
            }
        ],
    }

    try:
        validate_cost_data(data)
        assert False, "Expected ValueError"
    except ValueError as error:
        assert "amount must be numeric" in str(error)


def test_negative_amount():
    data = {
        "currency": "USD",
        "records": [
            {
                "date": "2026-09-01",
                "service": "Amazon EC2",
                "amount": -10.00,
            }
        ],
    }

    try:
        validate_cost_data(data)
        assert False, "Expected ValueError"
    except ValueError as error:
        assert "amount cannot be negative" in str(error)


def test_normalize_cost_response():
    fake_aws_response = {
        "ResultsByTime": [
            {
                "TimePeriod": {
                    "Start": "2026-09-01",
                    "End": "2026-09-02",
                },
                "Groups": [],
                "Estimated": True,
            }
        ]
    }

    records = normalize_cost_response(fake_aws_response)

    assert records == []


def test_normalize_service_cost_response():
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

    records = normalize_cost_response(fake_aws_response)

    assert records == [
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
            "service": "AWS Lambda",
            "amount": 0.80,
        },
    ]


def test_process_cost_records():
    records = [
        {"date": "2026-09-01", "service": "Amazon EC2", "amount": 12.50},
        {"date": "2026-09-01", "service": "Amazon S3", "amount": 2.30},
        {"date": "2026-09-01", "service": "AWS Lambda", "amount": 0.80},
    ]

    result = process_cost_records(records, "USD")

    assert result["currency"] == "USD"
    assert result["record_count"] == 3
    assert result["total"] == pytest.approx(15.60)

    assert result["cost_by_service"] == {
        "Amazon EC2": 12.50,
        "Amazon S3": 2.30,
        "AWS Lambda": 0.80,
    }

    assert result["cost_by_date"]["2026-09-01"] == pytest.approx(15.60)


def test_aws_records_can_use_processing_layer():
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
                ],
                "Estimated": True,
            }
        ]
    }

    records = normalize_cost_response(fake_aws_response)
    result = process_cost_records(records, "USD")

    assert result["total"] == pytest.approx(14.80)
    assert result["cost_by_service"]["Amazon EC2"] == 12.50
    assert result["cost_by_service"]["Amazon S3"] == 2.30


def test_parse_arguments(monkeypatch):
    monkeypatch.setattr(
        "sys.argv",
        [
            "aws_cost_collector.py",
            "--start-date",
            "2026-09-01",
            "--end-date",
            "2026-09-04",
        ],
    )

    args = parse_arguments()

    assert args.start_date == "2026-09-01"
    assert args.end_date == "2026-09-04"

def test_validate_valid_date_range():
    validate_date_range("2026-09-01", "2026-09-04")


def test_validate_invalid_date_format():
    with pytest.raises(ValueError, match="YYYY-MM-DD"):
        validate_date_range("2026-99-01", "2026-09-04")


def test_validate_end_date_before_start_date():
    with pytest.raises(
        ValueError,
        match="End date must be later than start date",
    ):
        validate_date_range("2026-09-10", "2026-09-05")


def test_validate_same_start_and_end_date():
    with pytest.raises(
        ValueError,
        match="End date must be later than start date",
    ):
        validate_date_range("2026-09-01", "2026-09-01")
