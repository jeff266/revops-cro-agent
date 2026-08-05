# First Prompt for Claude Code

Copy and paste this into Claude Code when you open the project:

---

Read CLAUDE.md. Build the following:

## 1. main.py — FastAPI app with:
- POST /query endpoint (returns 200 immediately, processes in background)
- GET /health endpoint
- Background task that calls handle_query() then POSTs result to ZAP_RESPONSE_URL

## 2. handlers/competitors.py — first handler:
- Queries Supabase calls table for rows where competitors_mentioned is not null
- Groups by competitor name and company
- Calls Claude to synthesize: which competitors appear most, in which deals, what the context is
- Returns Slack-formatted markdown response

## 3. requirements.txt:
```
fastapi
uvicorn
httpx
supabase>=2.0.0
anthropic>=0.40.0
```

## 4. railway.toml:
```toml
[deploy]
startCommand = "uvicorn main:app --host 0.0.0.0 --port $PORT"
```

## 5. Procfile (backup):
```
web: uvicorn main:app --host 0.0.0.0 --port $PORT
```

After building, update CLAUDE.md handlers checklist and current status section.

---

## Testing locally

After Claude Code builds the files, test with:

```bash
# Install dependencies
pip install -r requirements.txt

# Set env vars
export ANTHROPIC_API_KEY="your-key"
export SUPABASE_URL="https://htgvkqycrwesdysustxd.supabase.co"
export SUPABASE_SERVICE_KEY="your-service-key"
export ZAP_RESPONSE_URL="https://hooks.zapier.com/hooks/catch/test"

# Run server
uvicorn main:app --reload

# Test in another terminal
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What competitors are we losing to?",
    "channel": "C12345",
    "thread_ts": "1234567890.123456"
  }'
```

Should return:
```json
{"status": "processing"}
```

Then check the server logs for the background task execution and POST to ZAP_RESPONSE_URL.
