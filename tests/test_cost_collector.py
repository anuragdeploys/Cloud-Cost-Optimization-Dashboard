import pytest
from unittest.mock import MagicMock, patch

from botocore.exceptions import BotoCoreError, ClientError, NoCredentialsError

from app.aws_cost_collector import (
    format_aws_error,
    get_daily_costs,
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


def test_get_daily_costs_single_page():
    fake_client = MagicMock()

    fake_client.get_cost_and_usage.return_value = {
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

    with patch(
        "app.aws_cost_collector.get_cost_explorer_client",
        return_value=fake_client,
    ):
        response = get_daily_costs("2026-09-01", "2026-09-02")

    assert len(response["ResultsByTime"]) == 1
    assert fake_client.get_cost_and_usage.call_count == 1

    first_call = fake_client.get_cost_and_usage.call_args_list[0]

    assert "NextPageToken" not in first_call.kwargs


def test_get_daily_costs_multiple_pages():
    fake_client = MagicMock()

    first_page = {
        "ResultsByTime": [
            {
                "TimePeriod": {
                    "Start": "2026-09-01",
                    "End": "2026-09-02",
                },
                "Groups": [],
                "Estimated": True,
            }
        ],
        "NextPageToken": "page-two-token",
    }

    second_page = {
        "ResultsByTime": [
            {
                "TimePeriod": {
                    "Start": "2026-09-02",
                    "End": "2026-09-03",
                },
                "Groups": [],
                "Estimated": True,
            }
        ]
    }

    fake_client.get_cost_and_usage.side_effect = [
        first_page,
        second_page,
    ]

    with patch(
        "app.aws_cost_collector.get_cost_explorer_client",
        return_value=fake_client,
    ):
        response = get_daily_costs("2026-09-01", "2026-09-03")

    assert len(response["ResultsByTime"]) == 2
    assert fake_client.get_cost_and_usage.call_count == 2

    first_call = fake_client.get_cost_and_usage.call_args_list[0]
    second_call = fake_client.get_cost_and_usage.call_args_list[1]

    assert "NextPageToken" not in first_call.kwargs
    assert second_call.kwargs["NextPageToken"] == "page-two-token"

def test_get_cost_explorer_client_configures_standard_retries():
    with patch("app.aws_cost_collector.boto3.Session") as mock_session:
        fake_session = mock_session.return_value
        fake_session.client.return_value = MagicMock()

        from app.aws_cost_collector import get_cost_explorer_client

        get_cost_explorer_client()

        mock_session.assert_called_once()
        fake_session.client.assert_called_once()

        call_kwargs = fake_session.client.call_args.kwargs
        retry_config = call_kwargs["config"]

        assert retry_config.retries["mode"] == "standard"
        assert retry_config.retries["max_attempts"] == 3


def test_format_no_credentials_error():
    error = NoCredentialsError()

    message = format_aws_error(error)

    assert message == "AWS credentials could not be found."


def test_format_client_error():
    error = ClientError(
        {
            "Error": {
                "Code": "AccessDeniedException",
                "Message": "User is not authorized.",
            }
        },
        "GetCostAndUsage",
    )

    message = format_aws_error(error)

    assert (
        message
        == "AWS API error (AccessDeniedException): "
        "User is not authorized."
    )


def test_format_botocore_error():
    error = BotoCoreError()

    message = format_aws_error(error)

    assert message.startswith("AWS connection error:")


def test_main_returns_one_for_invalid_dates(monkeypatch):
    monkeypatch.setattr(
        "app.aws_cost_collector.parse_arguments",
        lambda: MagicMock(
            start_date="2026-09-10",
            end_date="2026-09-05",
        ),
    )

    with patch("app.aws_cost_collector.get_daily_costs") as mock_get_costs:
        from app.aws_cost_collector import main

        result = main()

    assert result == 1
    mock_get_costs.assert_not_called()


def test_get_daily_costs_repeated_page_token():
    fake_client = MagicMock()

    first_page = {
        "ResultsByTime": [
            {
                "TimePeriod": {
                    "Start": "2026-09-01",
                    "End": "2026-09-02",
                },
                "Groups": [],
                "Estimated": True,
            }
        ],
        "NextPageToken": "same-token",
    }

    second_page = {
        "ResultsByTime": [
            {
                "TimePeriod": {
                    "Start": "2026-09-02",
                    "End": "2026-09-03",
                },
                "Groups": [],
                "Estimated": True,
            }
        ],
        "NextPageToken": "same-token",
    }

    fake_client.get_cost_and_usage.side_effect = [
        first_page,
        second_page,
    ]

    with patch(
        "app.aws_cost_collector.get_cost_explorer_client",
        return_value=fake_client,
    ):
        with pytest.raises(
            RuntimeError,
            match="repeated pagination token",
        ):
            get_daily_costs("2026-09-01", "2026-09-03")

    assert fake_client.get_cost_and_usage.call_count == 2
