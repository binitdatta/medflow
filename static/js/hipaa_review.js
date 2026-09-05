let currentReviewId = null;
let detailModal = null;

function getFilters() {
    const params = new URLSearchParams();
    const start = document.getElementById("startDate").value;
    const end = document.getElementById("endDate").value;
    const role = document.getElementById("roleFilter").value;
    const reviewed = document.getElementById("reviewedFilter").value;
    if (start) params.set("start_date", start);
    if (end) params.set("end_date", end);
    if (role) params.set("role", role);
    if (reviewed) params.set("reviewed", reviewed);
    return params;
}

async function loadSummary() {
    const params = getFilters();
    const resp = await fetch(`/api/hipaa/review/summary?${params.toString()}`);
    const data = await resp.json();

    document.getElementById("statTotal").textContent = data.total_calls;
    document.getElementById("statUnreviewed").textContent = data.unreviewed_calls;
    document.getElementById("statReviewed").textContent = data.reviewed_calls;

    if (!document.getElementById("startDate").value) document.getElementById("startDate").value = data.start_date;
    if (!document.getElementById("endDate").value) document.getElementById("endDate").value = data.end_date;
}

async function loadCalls() {
    const params = getFilters();
    params.set("limit", "200");
    const resp = await fetch(`/api/hipaa/review/calls?${params.toString()}`);
    const rows = await resp.json();

    const tbody = document.getElementById("callsBody");
    tbody.innerHTML = "";
    for (const r of rows) {
        const tr = document.createElement("tr");
        const statusBadge = r.reviewed
            ? '<span class="badge bg-success">Reviewed</span>'
            : '<span class="badge bg-danger">Unreviewed</span>';
        tr.innerHTML = `
            <td>${r.created_at ? r.created_at.replace("T", " ").slice(0, 19) : ""}</td>
            <td>${r.actor_role || ""}</td>
            <td class="text-truncate" style="max-width:280px;" title="${(r.purpose || "").replace(/"/g, '&quot;')}">${r.purpose || ""}</td>
            <td>${r.model || ""}</td>
            <td>${r.cost_usd != null ? "$" + Number(r.cost_usd).toFixed(4) : "—"}</td>
            <td>${statusBadge}</td>
            <td><button class="btn btn-sm btn-outline-primary" data-review-id="${r.review_id}">View</button></td>
        `;
        tbody.appendChild(tr);
    }

    tbody.querySelectorAll("button[data-review-id]").forEach((btn) => {
        btn.addEventListener("click", () => openDetail(btn.getAttribute("data-review-id")));
    });
}

function prettyJson(text) {
    if (!text) return "(none captured)";
    try {
        return JSON.stringify(JSON.parse(text), null, 2);
    } catch (e) {
        return text;
    }
}

async function openDetail(reviewId) {
    currentReviewId = reviewId;
    const resp = await fetch(`/api/hipaa/review/calls/${reviewId}`);
    const r = await resp.json();

    document.getElementById("modalReviewId").textContent = `#${r.review_id}`;
    document.getElementById("modalTime").textContent = r.created_at ? r.created_at.replace("T", " ").slice(0, 19) : "";
    document.getElementById("modalRoleStaff").textContent = `${r.actor_role || ""} (staff_id ${r.staff_id ?? "—"})`;
    document.getElementById("modalPurpose").textContent = r.purpose || "";
    document.getElementById("modalMethodUrl").textContent = `${r.http_method || "—"}  ${r.url || "(not captured)"}`;
    document.getElementById("modalStatus").textContent = r.response_status ?? "—";
    document.getElementById("modalMeta").textContent =
        `${r.model || ""} | in: ${r.input_tokens ?? "—"} out: ${r.output_tokens ?? "—"} | ` +
        `${r.cost_usd != null ? "$" + Number(r.cost_usd).toFixed(4) : "—"} | ${r.latency_ms ?? "—"} ms`;

    document.getElementById("modalHeaders").textContent = prettyJson(r.request_headers);
    document.getElementById("modalParams").textContent = prettyJson(r.request_params);
    document.getElementById("modalRequestBody").textContent = prettyJson(r.request_body);
    document.getElementById("modalResponseBody").textContent = prettyJson(r.response_body);

    const reviewedInfo = document.getElementById("modalReviewedInfo");
    const reviewForm = document.getElementById("modalReviewForm");
    if (r.reviewed) {
        reviewedInfo.classList.remove("d-none");
        reviewedInfo.textContent =
            `Reviewed by staff_id ${r.reviewed_by_staff_id} on ${r.reviewed_at ? r.reviewed_at.replace("T", " ").slice(0, 19) : ""}` +
            (r.review_notes ? ` — "${r.review_notes}"` : "");
        reviewForm.classList.add("d-none");
    } else {
        reviewedInfo.classList.add("d-none");
        reviewForm.classList.remove("d-none");
        document.getElementById("reviewNotes").value = "";
    }

    detailModal.show();
}

async function markReviewed() {
    if (!currentReviewId) return;
    const notes = document.getElementById("reviewNotes").value;
    await fetch(`/api/hipaa/review/calls/${currentReviewId}/mark-reviewed`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ notes }),
    });
    detailModal.hide();
    await refreshAll();
}

async function refreshAll() {
    await loadSummary();
    await loadCalls();
}

document.addEventListener("DOMContentLoaded", () => {
    detailModal = new bootstrap.Modal(document.getElementById("detailModal"));
    document.getElementById("markReviewedBtn").addEventListener("click", markReviewed);
    document.getElementById("filterForm").addEventListener("submit", (e) => {
        e.preventDefault();
        refreshAll();
    });
    refreshAll();
});