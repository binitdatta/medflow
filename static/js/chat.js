let sessionId = null;

function escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
}

async function ensureSession() {
    if (sessionId) return sessionId;
    const resp = await fetch("/api/chat/sessions", { method: "POST" });
    const data = await resp.json();
    sessionId = data.session_id;
    return sessionId;
}

function appendBubble(text, sender) {
    const win = document.getElementById("chatWindow");

    const row = document.createElement("div");
    row.className = sender === "USER" ? "chat-row chat-row-user" : "chat-row chat-row-assistant";

    const avatar = document.createElement("div");
    avatar.className = "chat-avatar";
    avatar.innerHTML = sender === "USER"
        ? '<i class="bi bi-person-fill"></i>'
        : '<i class="bi bi-heart-pulse-fill"></i>';

    const bubble = document.createElement("div");
    bubble.className = sender === "USER" ? "chat-bubble-user" : "chat-bubble-assistant";

    if (sender === "USER") {
        // User's own text -- render as plain text, no markdown parsing needed.
        bubble.textContent = text;
    } else {
        // Assistant output may contain markdown (tables, bold, lists) --
        // parse it, then sanitize before inserting as HTML. Sanitizing is
        // essential here: this is model output, and while MedFlow's own
        // prompts don't ask it to emit HTML, treating any dynamic content
        // as trusted before rendering is not a habit worth forming.
        const rawHtml = (typeof marked !== "undefined") ? marked.parse(text) : escapeHtml(text);
        bubble.innerHTML = (typeof DOMPurify !== "undefined") ? DOMPurify.sanitize(rawHtml) : escapeHtml(text);
    }

    if (sender === "USER") {
        row.appendChild(bubble);
        row.appendChild(avatar);
    } else {
        row.appendChild(avatar);
        row.appendChild(bubble);
    }

    win.appendChild(row);
    win.scrollTop = win.scrollHeight;
    return bubble;
}

document.getElementById("chatForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const input = document.getElementById("chatInput");
    const message = input.value.trim();
    if (!message) return;

    appendBubble(message, "USER");
    input.value = "";

    const sid = await ensureSession();
    const thinkingBubble = appendBubble("Thinking…", "ASSISTANT");
    const thinkingRow = thinkingBubble.closest(".chat-row");

    try {
        const resp = await fetch(`/api/chat/sessions/${sid}/messages`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message }),
        });
        const data = await resp.json();
        thinkingRow.remove();
        appendBubble(data.response || data.error || "No response.", "ASSISTANT");
    } catch (err) {
        thinkingRow.remove();
        appendBubble("Error contacting the assistant: " + err, "ASSISTANT");
    }
});