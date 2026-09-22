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


def calculate_service_concentration(records):
    """
    Calculate each service's percentage of total cost.

    Returns services ordered from highest concentration
    to lowest concentration.
    """
    service_ranking = rank_services_by_cost(records)

    total_cost = sum(
        amount for _, amount in service_ranking
    )

    if total_cost == 0:
        return []

    return [
        {
            "service": service,
            "amount": amount,
            "percentage": (amount / total_cost) * 100,
        }
        for service, amount in service_ranking
    ]

def calculate_daily_cost_changes(records):
    """
    Calculate day-over-day cost percentage changes.

    The first available day has no previous baseline and
    therefore returns None for its percentage change.
    """
    daily_totals = calculate_daily_totals(records)
    dates = list(daily_totals.keys())

    changes = []

    for index, date in enumerate(dates):
        current_amount = daily_totals[date]

        if index == 0:
            changes.append(
                {
                    "date": date,
                    "amount": current_amount,
                    "previous_amount": None,
                    "percentage_change": None,
                }
            )
            continue

        previous_date = dates[index - 1]
        previous_amount = daily_totals[previous_date]

        if previous_amount == 0:
            percentage_change = None
        else:
            percentage_change = (
                (current_amount - previous_amount)
                / previous_amount
            ) * 100

        changes.append(
            {
                "date": date,
                "amount": current_amount,
                "previous_amount": previous_amount,
                "percentage_change": percentage_change,
            }
        )

    return changes

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
