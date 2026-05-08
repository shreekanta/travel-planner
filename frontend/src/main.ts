import { marked } from "marked";

interface PlanRequest {
  pax: number;
  start_date: string;
  end_date: string;
  destination: string;
  origin: string;
}

interface PlanResponse {
  markdown: string;
  tokens?: Record<string, number>;
}

const API_BASE: string =
  (import.meta as unknown as { env: Record<string, string> }).env?.VITE_API ??
  "http://localhost:8000";

const app = document.getElementById("app") as HTMLElement;

app.innerHTML = `
  <header>
    <h1>Travel Planner Agent</h1>
    <p class="sub">Claude Agent SDK · flight · hotel · weather sub-agents</p>
  </header>

  <form id="form">
    <label>Destination
      <input name="destination" required placeholder="Tokyo" autocomplete="off" />
    </label>
    <label>Origin (IATA / city)
      <input name="origin" value="BLR" autocomplete="off" />
    </label>
    <label>Start Date
      <input name="start_date" type="date" required />
    </label>
    <label>End Date
      <input name="end_date" type="date" required />
    </label>
    <label>Pax
      <input name="pax" type="number" min="1" max="20" value="2" required />
    </label>
    <button id="submit" type="submit">Plan Trip</button>
  </form>

  <section id="status" class="status"></section>
  <article id="result" class="result"></article>
`;

const form = document.getElementById("form") as HTMLFormElement;
const submitBtn = document.getElementById("submit") as HTMLButtonElement;
const statusEl = document.getElementById("status") as HTMLElement;
const resultEl = document.getElementById("result") as HTMLElement;

function setStatus(text: string, kind: "info" | "error" | "ok" = "info"): void {
  statusEl.textContent = text;
  statusEl.dataset.kind = kind;
}

form.addEventListener("submit", async (event: SubmitEvent) => {
  event.preventDefault();
  const fd = new FormData(form);
  const payload: PlanRequest = {
    destination: String(fd.get("destination") ?? "").trim(),
    origin: String(fd.get("origin") ?? "BLR").trim() || "BLR",
    start_date: String(fd.get("start_date") ?? ""),
    end_date: String(fd.get("end_date") ?? ""),
    pax: Number(fd.get("pax") ?? 1),
  };

  if (new Date(payload.end_date) < new Date(payload.start_date)) {
    setStatus("End date must be on or after start date.", "error");
    return;
  }

  submitBtn.disabled = true;
  resultEl.innerHTML = "";
  setStatus(
    "Planning your trip… sub-agents querying flights, hotels, and weather.",
    "info",
  );

  try {
    const res = await fetch(`${API_BASE}/plan`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const txt = await res.text();
      throw new Error(`HTTP ${res.status} — ${txt}`);
    }
    const data: PlanResponse = await res.json();
    resultEl.innerHTML = await marked.parse(data.markdown ?? "");
    if (data.tokens && data.tokens.input_tokens != null) {
      const t = data.tokens;
      const total = (t.input_tokens ?? 0) + (t.output_tokens ?? 0);
      const cacheStr = t.cache_read_tokens ? ` · cache hit: ${t.cache_read_tokens.toLocaleString()}` : "";
      const el = document.createElement("p");
      el.className = "token-usage";
      el.textContent = `Tokens — in: ${(t.input_tokens ?? 0).toLocaleString()} · out: ${(t.output_tokens ?? 0).toLocaleString()}${cacheStr} · total: ${total.toLocaleString()}`;
      resultEl.appendChild(el);
    }
    setStatus("Done.", "ok");
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    setStatus(`Error: ${msg}`, "error");
  } finally {
    submitBtn.disabled = false;
  }
});
