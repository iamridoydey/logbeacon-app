
function copyToClipboard(elementId) {
    const el = document.getElementById(elementId);
    if (!el) return;
    navigator.clipboard.writeText(el.innerText).then(() => {
        showToast("Copied to clipboard", "success");
    }).catch(err => {
        console.error("Failed to copy:", err);
        showToast("Couldn't copy — try again", "error");
    });
}

function escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
}

// --- Toast popup, replaces the old inline error banner ---
function showToast(message, type = "error", duration = 4000) {
    const container = document.getElementById("toast-container");
    if (!container) return;

    const isError = type === "error";
    const toast = document.createElement("div");
    toast.className = [
        "flex items-start gap-3 px-4 py-3 rounded-md border shadow-lg",
        "translate-x-full opacity-0 transition-all duration-300 ease-out",
        isError
            ? "bg-danger/10 border-danger/40 text-danger"
            : "bg-teal/10 border-teal/40 text-teal",
        "max-w-sm font-mono text-sm"
    ].join(" ");
    toast.innerHTML = `
        <span class="font-bold text-xs tracking-wider shrink-0">${isError ? "ERROR" : "OK"}</span>
        <span class="flex-1">${escapeHtml(message)}</span>
        <button type="button" class="text-muted hover:text-text cursor-pointer shrink-0" aria-label="Dismiss">&times;</button>
    `;

    container.appendChild(toast);
    requestAnimationFrame(() => {
        toast.classList.remove("translate-x-full", "opacity-0");
    });

    function dismiss() {
        toast.classList.add("translate-x-full", "opacity-0");
        setTimeout(() => toast.remove(), 300);
    }

    toast.querySelector("button").addEventListener("click", dismiss);
    setTimeout(dismiss, duration);
}

// --- Auto-growing textarea: expands upward since the composer is pinned to the bottom ---
function autoGrow(textarea) {
    textarea.style.height = "auto";
    textarea.style.height = textarea.scrollHeight + "px";
}

// --- Typewriter reveal for freshly-received HTML, preserving real tags (no broken mid-tag typing) ---
function typeWriterHtml(container, html, speed=24) {
    const tokens = html.split(/(<[^>]+>)/g).filter(Boolean);
    let tokenIndex = 0, charIndex = 0;

    function step() {
        if (tokenIndex >= tokens.length) return;
        const token = tokens[tokenIndex];

        if (token.startsWith("<")) {
            container.innerHTML += token;
            tokenIndex++;
            return requestAnimationFrame(step);
        }

        container.innerHTML += token[charIndex];
        charIndex++;
        if (charIndex >= token.length) {
            tokenIndex++;
            charIndex = 0;
        }
        setTimeout(() => requestAnimationFrame(step), speed);
    }
    step();
}

function buildEntryHtml(entry) {
    return `
      <div class="border-l-4 border-danger/70 bg-surface/50 px-4 py-3 rounded-md space-y-2 relative">
        <div class="flex items-center justify-between">
          <span class="text-danger text-xs font-bold tracking-wider">ERROR</span>
          <span class="text-muted text-xs">${new Date(entry.created_at).toLocaleString()}</span>
        </div>
        <pre id="error-${entry.id}" class="text-text/90 font-mono text-sm whitespace-pre-wrap wrap-break-words overflow-hidden">${escapeHtml(entry.error_log)}</pre>
        <div class="flex justify-end">
          <button type="button" onclick="copyToClipboard('error-${entry.id}')" class="flex items-center gap-1 text-xs text-muted hover:text-accent transition-colors cursor-pointer">Copy</button>
        </div>
      </div>
      <div class="border-l-4 border-teal bg-surface/50 px-4 py-3 rounded-md space-y-2 relative">
        <div class="flex items-center justify-between">
          <span class="text-teal text-xs font-bold tracking-wider">FIX</span>
          <span class="text-muted text-xs">${entry.input_tokens} in / ${entry.output_tokens} out &middot; $${parseFloat(entry.cost).toFixed(6)}</span>
        </div>
        <div id="solution-${entry.id}" class="prose max-w-none text-text/90 whitespace-pre-wrap wrap-break-words overflow-hidden"></div>
        <div class="flex justify-end">
          <button type="button" onclick="copyToClipboard('solution-${entry.id}')" class="flex items-center gap-1 text-xs text-muted hover:text-accent transition-colors cursor-pointer">Copy</button>
        </div>
      </div>
    `;
}

document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("analyze-form");
    const textarea = document.getElementById("error-log-input");
    const submitBtn = document.getElementById("analyze-submit");
    const entriesList = document.getElementById("entries-list");
    const emptyState = document.getElementById("empty-state");

    if (!form) return;

    textarea.addEventListener("input", () => autoGrow(textarea));

    form.addEventListener("submit", async (e) => {
        e.preventDefault();

        const error_log = textarea.value.trim();
        if (!error_log) return;

        submitBtn.disabled = true;
        submitBtn.textContent = "Analyzing...";

        try {
            const res = await fetch("/analyze", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ error_log }),
            });
            const body = await res.json();

            if (res.status === 401) {
                window.location.href = "/auth/signin";
                return;
            }

            if (!res.ok) {
                showToast(body.error || "Something went wrong.", "error");
                return;
            }

            if (emptyState) emptyState.classList.add("hidden");
            entriesList.insertAdjacentHTML("beforeend", buildEntryHtml(body.entry));

            const solutionEl = document.getElementById(`solution-${body.entry.id}`);
            typeWriterHtml(solutionEl, body.entry.error_solution_html);

            textarea.value = "";
            textarea.style.height = "auto";
            form.scrollIntoView({ behavior: "smooth", block: "end" });

        } catch (err) {
            showToast("Network error — is the server running?", "error");
        } finally {
            submitBtn.disabled = false;
            submitBtn.textContent = "Analyze";
        }
    });
});