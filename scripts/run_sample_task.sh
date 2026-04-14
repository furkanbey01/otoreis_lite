#!/usr/bin/env bash
set -euo pipefail

API_URL=${API_URL:-http://localhost:8000}

curl -sS -X POST "$API_URL/api/tasks" \
  -H 'Content-Type: application/json' \
  -d '{
    "goal": "Open wikipedia and search for Artificial intelligence",
    "steps": [
      {"type": "navigate", "args": {"url": "https://www.wikipedia.org"}},
      {"type": "type", "args": {"selector": "input#searchInput", "text": "Artificial intelligence"}},
      {"type": "click", "args": {"selector": "button[type='"'"'submit'"'"']"}},
      {"type": "extract_text", "args": {"selector": "#firstHeading"}},
      {"type": "save_json", "args": {"path": "results/ai_heading.json"}}
    ]
  }' | jq .
