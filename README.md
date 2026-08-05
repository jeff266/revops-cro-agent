# RevOps CRO Query Agent

Slack-based query interface for GrowthBook CRO to ask questions about deals, calls, and rep performance. Powered by Claude and Supabase.

## What it does

Ask questions in Slack, get instant insights:
- "What competitors are we losing to?"
- "Which deals are at risk this quarter?"
- "What's our close probability for deals in negotiation?"
- "What objections are reps hearing most?"
- "Show me rep performance by MEDDICC score"
- "What feature gaps are prospects mentioning?"

## Architecture

```
Slack → Zapier → Railway (FastAPI) → Supabase → Claude → Zapier → Slack
```

1. User asks question in Slack
2. Zapier sends to Railway `/query` endpoint
3. Railway returns 200 immediately (avoids timeout)
4. Background task queries Supabase, synthesizes with Claude
5. Posts response back to Zapier webhook
6. Zapier posts threaded reply in Slack

## Deploy to Railway

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/your-template-id)

### Environment Variables

Set these in Railway:
- `ANTHROPIC_API_KEY` — Get from console.anthropic.com
- `SUPABASE_URL` — Your Supabase project URL
- `SUPABASE_SERVICE_KEY` — Supabase service role key
- `ZAP_RESPONSE_URL` — Zapier catch hook URL (Zap 2)

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set env vars
export ANTHROPIC_API_KEY="your-key"
export SUPABASE_URL="https://your-project.supabase.co"
export SUPABASE_SERVICE_KEY="your-service-key"
export ZAP_RESPONSE_URL="https://hooks.zapier.com/hooks/catch/..."

# Run server
uvicorn main:app --reload
```

Test endpoint:
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What competitors are we losing to?",
    "channel": "C12345",
    "thread_ts": "1234567890.123456"
  }'
```

## Query Examples

### Competitive Intelligence
- "What competitors appeared in calls this month?"
- "Show me all deals where LaunchDarkly was mentioned"
- "Which competitor comes up in enterprise deals?"

### Deal Risk
- "Which deals have low MEDDICC scores?"
- "Show me deals that haven't been updated in 2 weeks"
- "What's our pipeline at risk this quarter?"

### Forecasting
- "What's our close probability for deals in negotiation?"
- "Show me deals by MEDDICC score distribution"
- "Which deals have high economic buyer scores?"

### Objections
- "What objections are reps hearing most?"
- "Show me pricing objections by stage"
- "What's the most common pushback in discovery?"

### Rep Performance
- "Which rep has the highest average MEDDICC score?"
- "Show me rep performance by champion score"
- "Who needs coaching on economic buyer discovery?"

### Product Gaps
- "What feature gaps are prospects mentioning?"
- "Show me all calls with feature gap signals"
- "Which missing features block the most deals?"

## Data Sources

This service queries read-only from Supabase tables populated by the MEDDICC nightly agent:
- **deals** — 79 active deals from HubSpot
- **analyses** — MEDDICC scores and full analysis text
- **calls** — Call transcripts with automatic signal detection
- **objections** — Structured objection data (future)
- **rep_performance** — Rep scorecards (future)

## Tech Stack

- **FastAPI** — Python web framework
- **Supabase** — PostgreSQL database with REST API
- **Claude Sonnet 4.5** — LLM for synthesis
- **Railway** — Hosting platform
- **Zapier** — Slack integration

## License

MIT
