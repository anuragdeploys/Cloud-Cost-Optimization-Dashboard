import json
from pathlib import Path

from app.cost_service import save_cost_records


DATA_FILE = Path(__file__).parent.parent / "data" / "sample_costs.json"


def main():
    with DATA_FILE.open("r", encoding="utf-8") as file:
        data = json.load(file)

    result = save_cost_records(
        records=data["records"],
        currency=data["currency"],
    )

    print("Sample data loaded successfully!")
    print(f"Records saved: {result['record_count']}")
    print(f"Total cost: {result['total']:.2f} {result['currency']}")


if __name__ == "__main__":
    main()
