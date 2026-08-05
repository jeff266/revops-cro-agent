# Local Testing Guide

Quick guide to test the CRO agent locally before deploying to Railway.

## 1. Install Dependencies

```bash
cd /Users/jeffignacio/GrowthBook/revops-cro-agent

# Create virtual environment (optional but recommended)
python3 -m venv venv
source venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

## 2. Set Environment Variables

```bash
# Required env vars
export ANTHROPIC_API_KEY="sk-ant-..."
export SUPABASE_URL="https://htgvkqycrwesdysustxd.supabase.co"
export SUPABASE_SERVICE_KEY="eyJhbGci..."
export ZAP_RESPONSE_URL="https://webhook.site/your-test-id"  # Use webhook.site for testing
```

**Getting a test webhook:**
1. Go to https://webhook.site
2. Copy the "Your unique URL" (e.g., `https://webhook.site/abc-123`)
3. Use that as `ZAP_RESPONSE_URL`
4. Keep the webhook.site tab open to see incoming requests

## 3. Start the Server

```bash
# Start in development mode (auto-reload on file changes)
uvicorn main:app --reload

# Or use the Railway command
uvicorn main:app --host 0.0.0.0 --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [xxxxx] using StatReload
INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

## 4. Test Health Endpoint

In another terminal:
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{"status":"healthy","service":"revops-cro-agent"}
```

## 5. Test Query Endpoint (Competitors Handler)

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What competitors are we losing to?",
    "channel": "C12345TEST",
    "thread_ts": "1234567890.123456"
  }'
```

**Expected immediate response:**
```json
{"status":"processing"}
```

**Then check:**
1. Server logs should show background task executing
2. Go to your webhook.site tab
3. You should see a POST request with:
   ```json
   {
     "response_text": "📊 **Competitive Analysis**\n\n...",
     "channel": "C12345TEST",
     "thread_ts": "1234567890.123456"
   }
   ```

## 6. Test Different Query Types

**Competitive query (should route to competitors handler):**
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Which competitors appear in our deals?",
    "channel": "C12345TEST",
    "thread_ts": "1234567890.123456"
  }'
```

**Unmatched query (should get default response):**
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Tell me about the weather",
    "channel": "C12345TEST",
    "thread_ts": "1234567890.123456"
  }'
```

Expected webhook response:
```
I'm not sure how to answer that yet. I can currently help with:

• **Competitive Intelligence** - Ask about competitors mentioned in calls

More handlers coming soon!
```

## 7. Verify Supabase Connection

Check server logs for any Supabase errors. If the competitors handler runs successfully, you should see:
- Query executed against `calls` table
- Competitor data aggregated
- Claude API call made
- Response posted to webhook

## 8. Common Issues

**Missing env vars:**
```
HTTPException: Missing required environment variables
```
→ Make sure all 4 env vars are set

**Supabase connection error:**
```
supabase.exceptions.AuthenticationError
```
→ Check `SUPABASE_SERVICE_KEY` is correct

**Claude API error:**
```
anthropic.exceptions.AuthenticationError
```
→ Check `ANTHROPIC_API_KEY` is valid

**No competitors found:**
```json
{
  "response_text": "📊 **Competitive Analysis**\n\nNo competitor mentions found in recent calls..."
}
```
→ Expected if calls table has no competitor data yet (nightly agent will populate)

## 9. Mock Data Test (Optional)

If you want to test without real Supabase data, you can temporarily modify `handlers/competitors.py` to return mock data:

```python
# At the top of handle() function, add:
if True:  # Mock mode
    return (
        "📊 **Competitive Analysis** (MOCK DATA)\n\n"
        "Top competitors mentioned:\n"
        "• **LaunchDarkly** - 5 deals\n"
        "• **Optimizely** - 3 deals\n"
        "• **Statsig** - 2 deals"
    )
```

## Success Criteria

✅ Server starts without errors
✅ `/health` endpoint returns 200
✅ `/query` endpoint returns `{"status":"processing"}` immediately
✅ Background task executes (check server logs)
✅ Webhook receives POST with `response_text`, `channel`, `thread_ts`
✅ Competitors handler queries Supabase and calls Claude
✅ Response formatted in Slack markdown

Once all tests pass, you're ready to deploy to Railway!
