def rank_services_by_cost(records):
    """
    Rank services from highest total cost to lowest total cost.
    """
    service_totals = {}

    for record in records:
        service = record["service"]
        amount = record["amount"]

        service_totals[service] = (
            service_totals.get(service, 0) + amount
        )

    return sorted(
        service_totals.items(),
        key=lambda item: item[1],
        reverse=True,
    )


def calculate_daily_totals(records):
    """
    Calculate the total cost for each date.
    """
    daily_totals = {}

    for record in records:
        date = record["date"]
        amount = record["amount"]

        daily_totals[date] = (
            daily_totals.get(date, 0) + amount
        )

    return dict(sorted(daily_totals.items()))


def detect_daily_spikes(records, threshold=1.20):
    """
    Detect days whose cost is at least `threshold` times
    the average cost of the previous available days.

    The first day cannot be evaluated because it has no
    previous baseline.
    """
    daily_totals = calculate_daily_totals(records)
    dates = list(daily_totals.keys())

    spikes = []

    for index in range(1, len(dates)):
        current_date = dates[index]
        current_cost = daily_totals[current_date]

        previous_costs = [
            daily_totals[dates[position]]
            for position in range(index)
        ]

        average_previous_cost = (
            sum(previous_costs) / len(previous_costs)
        )

        if (
            average_previous_cost > 0
            and current_cost >= average_previous_cost * threshold
        ):
            spikes.append(
                {
                    "date": current_date,
                    "amount": current_cost,
                    "average_previous_amount": (
                        average_previous_cost
                    ),
                    "threshold": threshold,
                }
            )

    return spikes
