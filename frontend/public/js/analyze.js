// --- Copy button (it was commented out, so the buttons had nothing to call) ---
function copyToClipboard(elementId) {
  const el = document.getElementById(elementId);
  if (!el) return;
  const text = el.innerText;

  const done = () => showToast("Copied to clipboard", "success");
  const fail = (err) => {
    console.error("Failed to copy:", err);
    showToast("Couldn't copy — try again", "error");
  };

  // navigator.clipboard only exists on HTTPS or http://localhost.
  if (navigator.clipboard && window.isSecureContext) {
    navigator.clipboard.writeText(text).then(done).catch(fail);
    return;
  }

  // Fallback for plain http, e.g. http://192.168.1.20:3000
  const helper = document.createElement("textarea");
  helper.value = text;
  helper.style.position = "fixed";
  helper.style.opacity = "0";
  document.body.appendChild(helper);
  helper.select();
  try {
    document.execCommand("copy")
      ? done()
      : fail(new Error("copy command refused"));
  } catch (err) {
    fail(err);
  } finally {
    helper.remove();
  }
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
    "max-w-sm font-mono text-sm",
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

// --- Typewriter reveal for freshly-received HTML ---
// Old version appended one character at a time with innerHTML +=. That re-parsed the
// whole box on every character (slow), waited ~40 ms per character (about 2 minutes
// for a long answer), and closed every tag the moment it was added, so the text
// ended up OUTSIDE its <p>, <li> and <code> tags.
//
// New version: build the final HTML structure once, empty all the text, then fill the
// text back in, many characters per frame. It always takes at most maxMs in total.
function typeWriterHtml(container, html, { maxMs = 2500 } = {}) {
  // People who asked their system for less motion get the answer straight away.
  if (
    window.matchMedia &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches
  ) {
    container.innerHTML = html;
    return;
  }

  // <template> parses the HTML without showing it, and keeps the tags intact.
  const template = document.createElement("template");
  template.innerHTML = html;
  const root = template.content;

  // Remember each piece of text, then empty it.
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
  const items = [];
  let total = 0;
  while (walker.nextNode()) {
    const node = walker.currentNode;
    items.push({ node, text: node.textContent });
    total += node.textContent.length;
    node.textContent = "";
  }

  container.replaceChildren(root); // tags appear now, the text is still empty

  // How many characters to reveal per frame so the whole thing takes ~maxMs.
  const perFrame = Math.max(1, Math.ceil(total / (maxMs / 16)));
  let i = 0;

  function frame() {
    let budget = perFrame;
    while (budget > 0 && i < items.length) {
      const { node, text } = items[i];
      const shown = node.textContent.length;
      const take = Math.min(budget, text.length - shown);
      node.textContent = text.slice(0, shown + take);
      budget -= take;
      if (node.textContent.length >= text.length) i++;
    }
    if (i < items.length) requestAnimationFrame(frame);
  }
  requestAnimationFrame(frame);
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
          <button type="button" data-copy-target="error-${entry.id}" class="flex items-center gap-1 text-xs text-muted hover:text-accent transition-colors cursor-pointer">Copy</button>
        </div>
      </div>
      <div class="border-l-4 border-teal bg-surface/50 px-4 py-3 rounded-md space-y-2 relative">
        <div class="flex items-center justify-between">
          <span class="text-teal text-xs font-bold tracking-wider">FIX</span>
          <span class="text-muted text-xs">${entry.input_tokens} in / ${entry.output_tokens} out &middot; $${parseFloat(entry.cost).toFixed(6)}</span>
        </div>
        <div id="solution-${entry.id}" class="prose max-w-none text-text/90 whitespace-pre-wrap wrap-break-words overflow-hidden"></div>
        <div class="flex justify-end">
          <button type="button" data-copy-target="solution-${entry.id}" class="flex items-center gap-1 text-xs text-muted hover:text-accent transition-colors cursor-pointer">Copy</button>
        </div>
      </div>
    `;
}

// One listener for every Copy button, including ones added later.
// A button only needs data-copy-target="<id of the element to copy>".
document.addEventListener("click", (e) => {
  const button = e.target.closest("[data-copy-target]");
  if (button) copyToClipboard(button.dataset.copyTarget);
});

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
      console.error("analyze request failed:", err);
      // The second argument is the TYPE ("error"), not the error object.
      // Passing err made this show a green "OK" toast for a network failure.
      showToast("Network error — is the server running?", "error");
    } finally {
      submitBtn.disabled = false;
      submitBtn.textContent = "Analyze";
    }
  });
});
