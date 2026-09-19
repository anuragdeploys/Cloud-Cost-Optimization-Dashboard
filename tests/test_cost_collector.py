from app.cost_collector import (
    calculate_cost_by_date,
    calculate_cost_by_service,
    calculate_total,
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
