import pytest

from app.cost_analyzer import (
    calculate_daily_totals,
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
