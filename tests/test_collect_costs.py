from unittest.mock import MagicMock, patch

from scripts.collect_costs import main, parse_arguments


def test_parse_arguments(monkeypatch):
    monkeypatch.setattr(
        "sys.argv",
        [
            "collect_costs.py",
            "--start-date",
            "2026-09-01",
            "--end-date",
            "2026-09-04",
        ],
    )

    args = parse_arguments()

    assert args.start_date == "2026-09-01"
    assert args.end_date == "2026-09-04"
    assert args.currency == "USD"


def test_parse_arguments_custom_currency(monkeypatch):
    monkeypatch.setattr(
        "sys.argv",
        [
            "collect_costs.py",
            "--start-date",
            "2026-09-01",
            "--end-date",
            "2026-09-04",
            "--currency",
            "EUR",
        ],
    )

    args = parse_arguments()

    assert args.currency == "EUR"


def test_main_runs_collection_workflow(monkeypatch, capsys):
    monkeypatch.setattr(
        "sys.argv",
        [
            "collect_costs.py",
            "--start-date",
            "2026-09-01",
            "--end-date",
            "2026-09-04",
        ],
    )

    fake_result = {
        "record_count": 9,
        "total": 47.19,
        "currency": "USD",
    }

    with patch(
        "scripts.collect_costs.collect_and_save_aws_costs",
        return_value=fake_result,
    ) as mock_collect:
        result = main()

    assert result == 0

    mock_collect.assert_called_once_with(
        start_date="2026-09-01",
        end_date="2026-09-04",
        currency="USD",
    )

    output = capsys.readouterr().out

    assert "Cost collection completed successfully." in output
    assert "Records collected: 9" in output
    assert "Total cost: 47.19 USD" in output
