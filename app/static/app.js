function buildQueryString() {
    const params = new URLSearchParams();

    const startDate = document.getElementById("start-date").value;
    const endDate = document.getElementById("end-date").value;
    const service = document.getElementById("service-filter").value;

    if (startDate) {
        params.set("start_date", startDate);
    }

    if (endDate) {
        params.set("end_date", endDate);
    }

    if (service) {
        params.set("service", service);
    }

    const query = params.toString();

    return query ? `?${query}` : "";
}


function setFilterError(message) {
    document.getElementById("filter-error").textContent = message;
}


function clearFilterError() {
    setFilterError("");
}


function validateFilters() {
    const startDate = document.getElementById("start-date").value;
    const endDate = document.getElementById("end-date").value;

    if ((startDate && !endDate) || (!startDate && endDate)) {
        return "Start date and end date must be provided together.";
    }

    if (startDate && endDate && startDate >= endDate) {
        return "End date must be later than start date.";
    }

    return null;
}


function populateServiceFilter(summary) {
    const select = document.getElementById("service-filter");
    const currentValue = select.value;

    select.innerHTML = "";

    const allOption = document.createElement("option");
    allOption.value = "";
    allOption.textContent = "All services";
    select.appendChild(allOption);

    for (const service of Object.keys(
        summary.cost_by_service
    ).sort()) {
        const option = document.createElement("option");
        option.value = service;
        option.textContent = service;
        select.appendChild(option);
    }

    if (
        currentValue &&
        Object.prototype.hasOwnProperty.call(
            summary.cost_by_service,
            currentValue
        )
    ) {
        select.value = currentValue;
    }
}


function renderServiceTable(summary) {
    const tableBody =
        document.getElementById("service-table-body");

    tableBody.innerHTML = "";

    const entries = Object.entries(
        summary.cost_by_service
    );

    if (entries.length === 0) {
        const row = document.createElement("tr");
        const cell = document.createElement("td");

        cell.colSpan = 2;
        cell.textContent = "No cost data found.";

        row.appendChild(cell);
        tableBody.appendChild(row);

        return;
    }

    entries
        .sort((a, b) => b[1] - a[1])
        .forEach(([service, amount]) => {
            const row = document.createElement("tr");

            const serviceCell = document.createElement("td");
            serviceCell.textContent = service;

            const amountCell = document.createElement("td");
            amountCell.textContent =
                `${amount.toFixed(2)} ${summary.currency}`;

            row.appendChild(serviceCell);
            row.appendChild(amountCell);

            tableBody.appendChild(row);
        });
}


function renderRecords(records) {
    const tableBody =
        document.getElementById("records-table-body");

    tableBody.innerHTML = "";

    if (records.length === 0) {
        const row = document.createElement("tr");
        const cell = document.createElement("td");

        cell.colSpan = 4;
        cell.textContent = "No cost records found.";

        row.appendChild(cell);
        tableBody.appendChild(row);

        return;
    }

    for (const record of records) {
        const row = document.createElement("tr");

        const dateCell = document.createElement("td");
        dateCell.textContent = record.date;

        const serviceCell = document.createElement("td");
        serviceCell.textContent = record.service;

        const amountCell = document.createElement("td");
        amountCell.textContent = record.amount.toFixed(2);

        const currencyCell = document.createElement("td");
        currencyCell.textContent = record.currency;

        row.appendChild(dateCell);
        row.appendChild(serviceCell);
        row.appendChild(amountCell);
        row.appendChild(currencyCell);

        tableBody.appendChild(row);
    }
}


function renderTrend(summary) {
    const container =
        document.getElementById("trend-container");

    container.innerHTML = "";

    const entries = Object.entries(
        summary.cost_by_date
    );

    if (entries.length === 0) {
        const message = document.createElement("p");
        message.textContent = "No cost data found.";
        container.appendChild(message);

        return;
    }

    const maxAmount = Math.max(
        ...entries.map((entry) => entry[1]),
        0
    );

    for (const [date, amount] of entries) {
        const row = document.createElement("div");
        row.className = "trend-row";

        const dateElement = document.createElement("div");
        dateElement.className = "trend-date";
        dateElement.textContent = date;

        const barContainer =
            document.createElement("div");

        barContainer.className =
            "trend-bar-container";

        const bar = document.createElement("div");

        bar.className = "trend-bar";

        const width = maxAmount > 0
            ? (amount / maxAmount) * 100
            : 0;

        bar.style.width = `${width}%`;

        barContainer.appendChild(bar);

        const amountElement =
            document.createElement("div");

        amountElement.className = "trend-amount";

        amountElement.textContent =
            `${amount.toFixed(2)} ${summary.currency}`;

        row.appendChild(dateElement);
        row.appendChild(barContainer);
        row.appendChild(amountElement);

        container.appendChild(row);
    }
}


function renderInsights(insights) {
    const topServices =
        document.getElementById("top-services");

    topServices.innerHTML = "";

    const rankedServices = insights.service_ranking;

    if (rankedServices.length === 0) {
        topServices.textContent =
            "No cost data available.";

    } else {
        rankedServices
            .slice(0, 3)
            .forEach((entry, index) => {
                const item = document.createElement("div");

                item.className = "insight-item";

                item.textContent =
                    `${index + 1}. ${entry[0]} — `
                    + `${entry[1].toFixed(2)} USD`;

                topServices.appendChild(item);
            });
    }

    const spikes =
        document.getElementById("cost-spikes");

    spikes.innerHTML = "";

    if (insights.daily_spikes.length === 0) {
        spikes.textContent =
            "No cost spikes detected.";

        return;
    }

    for (const spike of insights.daily_spikes) {
        const item = document.createElement("div");

        item.className = "spike-item";

        item.textContent =
            `${spike.date}: `
            + `${spike.amount.toFixed(2)} USD `
            + `(baseline: `
            + `${spike.average_previous_amount.toFixed(2)} USD)`;

        spikes.appendChild(item);
    }
}


async function loadDashboard() {
    const status =
        document.getElementById("status");

    try {
        const query = buildQueryString();

        const summaryResponse = await fetch(
            `/costs/summary${query}`
        );

        const summary =
            await summaryResponse.json();

        const recordsResponse = await fetch(
            `/costs${query}`
        );

        const recordsData =
            await recordsResponse.json();

        const insightsResponse = await fetch(
            `/costs/insights${query}`
        );

        const insights =
            await insightsResponse.json();

        if (
            !summaryResponse.ok ||
            !recordsResponse.ok ||
            !insightsResponse.ok
        ) {
            throw new Error(
                summary.error ||
                recordsData.error ||
                insights.error ||
                "API request failed."
            );
        }

        document.getElementById("total-cost").textContent =
            `${summary.total.toFixed(2)} `
            + `${summary.currency}`;

        document.getElementById("record-count")
            .textContent =
            summary.record_count;

        document.getElementById("service-count")
            .textContent =
            Object.keys(
                summary.cost_by_service
            ).length;

        populateServiceFilter(summary);
        renderServiceTable(summary);
        renderRecords(recordsData.records);
        renderTrend(summary);
        renderInsights(insights);

        status.textContent = "API connected";

        clearFilterError();

    } catch (error) {
        console.error(error);

        status.textContent = "API error";

        setFilterError(error.message);
    }
}


document
    .getElementById("apply-filters")
    .addEventListener("click", () => {
        const error = validateFilters();

        if (error) {
            setFilterError(error);
            return;
        }

        loadDashboard();
    });


document
    .getElementById("clear-filters")
    .addEventListener("click", () => {
        document.getElementById("start-date").value = "";
        document.getElementById("end-date").value = "";
        document.getElementById("service-filter").value = "";

        clearFilterError();

        loadDashboard();
    });


loadDashboard();
