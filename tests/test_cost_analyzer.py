import pytest

from app.cost_analyzer import (
    calculate_daily_cost_changes,
    calculate_daily_totals,
    calculate_service_concentration,
    detect_daily_spikes,
    rank_services_by_cost,
)


def test_rank_services_by_cost():
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
            "service": "Amazon EC2",
            "amount": 13.10,
        },
        {
            "date": "2026-09-02",
            "service": "Amazon S3",
            "amount": 2.45,
        },
        {
            "date": "2026-09-02",
            "service": "AWS Lambda",
            "amount": 0.92,
        },
    ]

    result = rank_services_by_cost(records)

    assert result == [
        ("Amazon EC2", pytest.approx(25.60)),
        ("Amazon S3", pytest.approx(4.75)),
        ("AWS Lambda", pytest.approx(0.92)),
    ]


def test_calculate_daily_totals():
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
            "service": "Amazon EC2",
            "amount": 13.10,
        },
    ]

    result = calculate_daily_totals(records)

    assert result["2026-09-01"] == pytest.approx(14.80)
    assert result["2026-09-02"] == pytest.approx(13.10)

    assert list(result.keys()) == [
        "2026-09-01",
        "2026-09-02",
    ]


def test_calculate_service_concentration():
    records = [
        {
            "date": "2026-09-01",
            "service": "Amazon EC2",
            "amount": 30.00,
        },
        {
            "date": "2026-09-01",
            "service": "Amazon S3",
            "amount": 10.00,
        },
        {
            "date": "2026-09-01",
            "service": "AWS Lambda",
            "amount": 10.00,
        },
    ]

    result = calculate_service_concentration(records)

    assert len(result) == 3

    assert result[0]["service"] == "Amazon EC2"
    assert result[0]["amount"] == pytest.approx(30.00)
    assert result[0]["percentage"] == pytest.approx(60.00)

    assert result[1]["service"] == "Amazon S3"
    assert result[1]["amount"] == pytest.approx(10.00)
    assert result[1]["percentage"] == pytest.approx(20.00)

    assert result[2]["service"] == "AWS Lambda"
    assert result[2]["amount"] == pytest.approx(10.00)
    assert result[2]["percentage"] == pytest.approx(20.00)


def test_calculate_daily_cost_changes():
    records = [
        {
            "date": "2026-09-01",
            "service": "Amazon EC2",
            "amount": 10.00,
        },
        {
            "date": "2026-09-01",
            "service": "Amazon S3",
            "amount": 5.00,
        },
        {
            "date": "2026-09-02",
            "service": "Amazon EC2",
            "amount": 12.00,
        },
        {
            "date": "2026-09-03",
            "service": "Amazon EC2",
            "amount": 9.00,
        },
    ]

    result = calculate_daily_cost_changes(records)

    assert len(result) == 3

    assert result[0]["date"] == "2026-09-01"
    assert result[0]["amount"] == pytest.approx(15.00)
    assert result[0]["previous_amount"] is None
    assert result[0]["percentage_change"] is None

    assert result[1]["date"] == "2026-09-02"
    assert result[1]["amount"] == pytest.approx(12.00)
    assert result[1]["previous_amount"] == pytest.approx(15.00)
    assert result[1]["percentage_change"] == pytest.approx(-20.00)

    assert result[2]["date"] == "2026-09-03"
    assert result[2]["amount"] == pytest.approx(9.00)
    assert result[2]["previous_amount"] == pytest.approx(12.00)
    assert result[2]["percentage_change"] == pytest.approx(-25.00)


def test_calculate_daily_cost_changes_handles_zero_previous_cost():
    records = [
        {
            "date": "2026-09-01",
            "service": "Amazon EC2",
            "amount": 0.00,
        },
        {
            "date": "2026-09-02",
            "service": "Amazon EC2",
            "amount": 10.00,
        },
    ]

    result = calculate_daily_cost_changes(records)

    assert len(result) == 2
    assert result[0]["percentage_change"] is None
    assert result[1]["previous_amount"] == pytest.approx(0.00)
    assert result[1]["percentage_change"] is None


def test_detect_daily_spikes_returns_empty_when_no_spike():
    records = [
        {
            "date": "2026-09-01",
            "service": "Amazon EC2",
            "amount": 10.00,
        },
        {
            "date": "2026-09-02",
            "service": "Amazon EC2",
            "amount": 11.00,
        },
        {
            "date": "2026-09-03",
            "service": "Amazon EC2",
            "amount": 11.50,
        },
    ]

    result = detect_daily_spikes(
        records,
        threshold=1.20,
    )

    assert result == []


def test_detect_daily_spikes_identifies_spike():
    records = [
        {
            "date": "2026-09-01",
            "service": "Amazon EC2",
            "amount": 10.00,
        },
        {
            "date": "2026-09-02",
            "service": "Amazon EC2",
            "amount": 11.00,
        },
        {
            "date": "2026-09-03",
            "service": "Amazon EC2",
            "amount": 30.00,
        },
    ]

    result = detect_daily_spikes(
        records,
        threshold=1.20,
    )

    assert len(result) == 1

    spike = result[0]

    assert spike["date"] == "2026-09-03"
    assert spike["amount"] == pytest.approx(30.00)
    assert spike["average_previous_amount"] == pytest.approx(10.50)
    assert spike["threshold"] == 1.20
