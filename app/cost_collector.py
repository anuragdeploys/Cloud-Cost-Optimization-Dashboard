import json
from pathlib import Path


DATA_FILE = Path(__file__).parent.parent / "data" / "sample_costs.json"


def load_cost_data():
    """Load cost data from the JSON file."""
    with DATA_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def validate_cost_data(data):
    """Validate the structure and values of the cost data."""
    if not isinstance(data, dict):
        raise ValueError("Cost data must be a JSON object.")

    if "currency" not in data:
        raise ValueError("Missing required field: currency.")

    if "records" not in data:
        raise ValueError("Missing required field: records.")

    if not isinstance(data["records"], list):
        raise ValueError("The records field must be a list.")

    for index, record in enumerate(data["records"]):
        if not isinstance(record, dict):
            raise ValueError(f"Record {index} must be a JSON object.")

        required_fields = ["date", "service", "amount"]

        for field in required_fields:
            if field not in record:
                raise ValueError(
                    f"Record {index} is missing required field: {field}."
                )

        if not isinstance(record["date"], str):
            raise ValueError(f"Record {index} date must be a string.")

        if not isinstance(record["service"], str):
            raise ValueError(f"Record {index} service must be a string.")

        if not isinstance(record["amount"], (int, float)):
            raise ValueError(f"Record {index} amount must be numeric.")

        if record["amount"] < 0:
            raise ValueError(f"Record {index} amount cannot be negative.")


def calculate_total(records):
    """Calculate the total cost from all records."""
    return sum(record["amount"] for record in records)


def calculate_cost_by_service(records):
    """Calculate total cost for each AWS service."""
    service_costs = {}

    for record in records:
        service = record["service"]
        amount = record["amount"]

        service_costs[service] = service_costs.get(service, 0) + amount

    return service_costs


def calculate_cost_by_date(records):
    """Calculate total cost for each date."""
    daily_costs = {}

    for record in records:
        date = record["date"]
        amount = record["amount"]

        daily_costs[date] = daily_costs.get(date, 0) + amount

    return daily_costs


def process_cost_records(records, currency="USD"):
    """
    Validate and calculate cost information from normalized records.

    This function is independent of the data source.
    """
    data = {
        "currency": currency,
        "records": records,
    }

    validate_cost_data(data)

    return {
        "currency": currency,
        "record_count": len(records),
        "total": calculate_total(records),
        "cost_by_service": calculate_cost_by_service(records),
        "cost_by_date": calculate_cost_by_date(records),
    }


def main():
    try:
        data = load_cost_data()
        validate_cost_data(data)

        currency = data["currency"]
        records = data["records"]

        result = process_cost_records(records, currency)

        print("Cost data loaded successfully!")
        print(f"Records: {result['record_count']}")
        print(f"Currency: {result['currency']}")
        print()

        print("Cost by service:")
        for service, amount in result["cost_by_service"].items():
            print(f"{service}: {amount:.2f} {currency}")

        print()

        print("Cost by date:")
        for date, amount in result["cost_by_date"].items():
            print(f"{date}: {amount:.2f} {currency}")

        print()

        print(f"Total cost: {result['total']:.2f} {currency}")

    except (OSError, json.JSONDecodeError, ValueError) as error:
        print(f"Error: {error}")


if __name__ == "__main__":
    main()
