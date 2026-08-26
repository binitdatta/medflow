let costByRoleChart = null;
let costByDayChart = null;

function getDateRange() {
    const start = document.getElementById("startDate").value;
    const end = document.getElementById("endDate").value;
    const params = new URLSearchParams();
    if (start) params.set("start_date", start);
    if (end) params.set("end_date", end);
    return params;
}

function fmtMoney(n) {
    return "$" + Number(n || 0).toFixed(4);
}

async function loadCostSummary() {
    const params = getDateRange();
    const resp = await fetch(`/api/admin/usage/cost-summary?${params.toString()}`);
    const data = await resp.json();

    document.getElementById("statTotalCost").textContent = fmtMoney(data.total_cost_usd);
    document.getElementById("statTotalCalls").textContent = data.total_calls;
    document.getElementById("statDateRange").textContent = `${data.start_date} → ${data.end_date}`;
    const avg = data.total_calls ? data.total_cost_usd / data.total_calls : 0;
    document.getElementById("statAvgCost").textContent = fmtMoney(avg);

    if (!document.getElementById("startDate").value) document.getElementById("startDate").value = data.start_date;
    if (!document.getElementById("endDate").value) document.getElementById("endDate").value = data.end_date;

    renderCostByRole(data.by_role);
    renderCostByDay(data.by_day);
}

function renderCostByRole(byRole) {
    const ctx = document.getElementById("costByRoleChart");
    const labels = byRole.map(r => r.actor_role);
    const costs = byRole.map(r => r.total_cost_usd);

    if (costByRoleChart) costByRoleChart.destroy();
    costByRoleChart = new Chart(ctx, {
        type: "bar",
        data: {
            labels: labels,
            datasets: [{
                label: "Cost (USD)",
                data: costs,
                backgroundColor: "#368fd1",
                borderRadius: 4,
            }],
        },
        options: {
            plugins: { legend: { display: false } },
            scales: { y: { beginAtZero: true } },
        },
    });
}

function renderCostByDay(byDay) {
    const ctx = document.getElementById("costByDayChart");
    const labels = byDay.map(d => d.date);
    const costs = byDay.map(d => d.total_cost_usd);

    if (costByDayChart) costByDayChart.destroy();
    costByDayChart = new Chart(ctx, {
        type: "line",
        data: {
            labels: labels,
            datasets: [{
                label: "Cost (USD)",
                data: costs,
                borderColor: "#2571ac",
                backgroundColor: "rgba(54, 143, 209, 0.15)",
                fill: true,
                tension: 0.25,
            }],
        },
        options: {
            plugins: { legend: { display: false } },
            scales: { y: { beginAtZero: true } },
        },
    });
}

async function loadLlmCalls() {
    const params = getDateRange();
    params.set("limit", "200");
    const resp = await fetch(`/api/admin/usage/llm-calls?${params.toString()}`);
    const rows = await resp.json();

    const tbody = document.getElementById("llmCallsBody");
    tbody.innerHTML = "";
    for (const r of rows) {
        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td>${r.created_at ? r.created_at.replace("T", " ").slice(0, 19) : ""}</td>
            <td>${r.actor_role || ""}</td>
            <td>${r.model || ""}</td>
            <td>${r.input_tokens ?? ""}</td>
            <td>${r.output_tokens ?? ""}</td>
            <td>${r.cost_usd != null ? fmtMoney(r.cost_usd) : "—"}</td>
            <td>${r.latency_ms != null ? r.latency_ms + " ms" : ""}</td>
        `;
        tbody.appendChild(tr);
    }
}

async function loadHttpCalls() {
    const params = getDateRange();
    params.set("limit", "200");
    const resp = await fetch(`/api/admin/usage/http-calls?${params.toString()}`);
    const rows = await resp.json();

    const tbody = document.getElementById("httpCallsBody");
    tbody.innerHTML = "";
    for (const r of rows) {
        const tr = document.createElement("tr");
        const statusClass = r.response_status >= 400 ? "text-danger fw-bold" : "text-success";
        tr.innerHTML = `
            <td>${r.created_at ? r.created_at.replace("T", " ").slice(0, 19) : ""}</td>
            <td>${r.actor_role || ""}</td>
            <td>${r.method || ""}</td>
            <td>${r.path || ""}</td>
            <td class="${statusClass}">${r.response_status ?? ""}</td>
            <td>${r.duration_ms != null ? r.duration_ms + " ms" : ""}</td>
        `;
        tbody.appendChild(tr);
    }
}

function updateExportLinks() {
    const params = getDateRange();
    document.getElementById("exportLlmCsv").href = `/api/admin/usage/llm-calls.csv?${params.toString()}`;
    document.getElementById("exportHttpCsv").href = `/api/admin/usage/http-calls.csv?${params.toString()}`;
}

async function refreshAll() {
    await loadCostSummary();
    await loadLlmCalls();
    await loadHttpCalls();
    updateExportLinks();
}

document.getElementById("filterForm").addEventListener("submit", (e) => {
    e.preventDefault();
    refreshAll();
});

refreshAll();