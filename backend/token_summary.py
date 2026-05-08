#!/usr/bin/env python3
"""Stop-hook helper: reads ~/.claude/travel_tokens.log and shows aggregate."""
import json
import pathlib
import subprocess

log = pathlib.Path.home() / ".claude" / "travel_tokens.log"

if not log.exists():
    summary = "no runs yet"
else:
    lines = [json.loads(l) for l in log.read_text().splitlines() if l.strip()]
    if lines:
        n = len(lines)
        ti = sum(l.get("input_tokens", 0) for l in lines)
        to_ = sum(l.get("output_tokens", 0) for l in lines)
        last = lines[-1]
        summary = (
            f"{n} plan run(s) · "
            f"last: in={last.get('input_tokens', 0):,} out={last.get('output_tokens', 0):,} · "
            f"total: in={ti:,} out={to_:,}"
        )
    else:
        summary = "no runs yet"

subprocess.run(
    [
        "osascript", "-e",
        f'display notification "Claude has finished" with title "Claude Code" subtitle "Travel Planner"',
    ],
    capture_output=True,
)
print(json.dumps({"systemMessage": f"Travel Planner tokens — {summary}"}))
