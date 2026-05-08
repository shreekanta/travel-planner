---
description: Smoke-test the Travel Planner backend. Checks /health then fires a sample /plan request (Tokyo, 2 pax, 5 nights) and reports pass/fail. Invoke with /smoke-test.
---

Run a two-step smoke test against the Travel Planner backend running on http://localhost:8000.

## Step 1 — Health check

Run:
```bash
curl -s --max-time 5 http://localhost:8000/health
```

- If the request times out or fails: stop immediately and report **✗ Backend not reachable** — tell the user to start the server with `uvicorn main:app --reload --port 8000` from the `backend/` directory.
- If the response is `{"status":"ok"}`: proceed to Step 2.

## Step 2 — Plan request

Run:
```bash
curl -s --max-time 120 -X POST http://localhost:8000/plan \
  -H "Content-Type: application/json" \
  -d '{"pax":2,"start_date":"2026-06-15","end_date":"2026-06-20","destination":"Tokyo","origin":"BLR"}'
```

Evaluate the response:
- If it contains a `"markdown"` key: extract and print the first 800 characters of the value, then report **✓ Smoke test passed**.
- If it contains a `"detail"` key: print the error message and report **✗ Plan request failed — `<detail value>`**.
- If the request times out (agents can take 60–90 s): report **✗ Timed out — the agent is taking too long. Check ANTHROPIC_API_KEY in backend/.env**.

## Final summary

End with a single-line verdict:
- `✓ Travel Planner backend OK` — both steps passed.
- `✗ Travel Planner backend FAILED — <reason>` — either step failed.
