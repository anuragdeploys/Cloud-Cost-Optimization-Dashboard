async function loadDashboard() {
    const status = document.getElementById("status");

    try {
        const summaryResponse = await fetch("/costs/summary");
        const summary = await summaryResponse.json();

        const recordsResponse = await fetch("/costs");
        const recordsData = await recordsResponse.json();

        if (!summaryResponse.ok || !recordsResponse.ok) {
            throw new Error("API request failed.");
        }

        document.getElementById("total-cost").textContent =
            `${summary.total.toFixed(2)} ${summary.currency}`;

        document.getElementById("record-count").textContent =
            summary.record_count;

        document.getElementById("service-count").textContent =
            Object.keys(summary.cost_by_service).length;

        const serviceTableBody =
            document.getElementById("service-table-body");

        serviceTableBody.innerHTML = "";

        for (const [service, amount] of Object.entries(
            summary.cost_by_service
        )) {
            const row = document.createElement("tr");

            const serviceCell = document.createElement("td");
            serviceCell.textContent = service;

            const amountCell = document.createElement("td");
            amountCell.textContent =
                `${amount.toFixed(2)} ${summary.currency}`;

            row.appendChild(serviceCell);
            row.appendChild(amountCell);

            serviceTableBody.appendChild(row);
        }

        const recordsTableBody =
            document.getElementById("records-table-body");

        recordsTableBody.innerHTML = "";

        for (const record of recordsData.records) {
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

            recordsTableBody.appendChild(row);
        }

        status.textContent = "API connected";
    } catch (error) {
        console.error(error);
        status.textContent = "API error";
    }
}


loadDashboard();
