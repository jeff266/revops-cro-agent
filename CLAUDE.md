# RevOps CRO Query Agent — Claude Code Instructions

## What this is
FastAPI service deployed on Railway. Receives Slack messages from Zapier (Zap 1), processes them against a Supabase database, calls Claude for synthesis, and posts responses back to Slack via Zapier (Zap 2 catch hook).

## Architecture
```
Slack → Zap 1 → POST /query → Railway (immediate 200)
Railway (background) → Supabase SQL → Claude → POST to ZAP_RESPONSE_URL
ZAP_RESPONSE_URL → Zap 2 → Slack thread reply
```

**Why async?** Slack/Zapier timeout after 30 seconds. CRO queries can take 10-60 seconds (SQL + Claude synthesis). We return 200 immediately to avoid timeout, then process in background and post back via webhook.

## Environment variables (set in Railway)
- `ANTHROPIC_API_KEY` — Claude API key
- `SUPABASE_URL` — GrowthBook Supabase project URL (https://htgvkqycrwesdysustxd.supabase.co)
- `SUPABASE_SERVICE_KEY` — Supabase service role key
- `ZAP_RESPONSE_URL` — Zapier Zap 2 catch hook URL

## Supabase schema (read-only for this service)

### deals
- `deal_id` (TEXT PRIMARY KEY)
- `company_name` (TEXT NOT NULL)
- `company_slug` (TEXT NOT NULL)
- `stage` (TEXT) — dealstage ID
- `pipeline` (TEXT)
- `arr_usd` (NUMERIC)
- `close_date` (DATE)
- `owner_email` (TEXT)
- `deal_status` (TEXT) — active | won | lost
- `create_date` (DATE)
- `days_to_close` (INTEGER) — null for active deals
- `last_analyzed` (TIMESTAMPTZ)

### analyses
- `id` (UUID PRIMARY KEY)
- `deal_id` (TEXT REFERENCES deals)
- `company_name` (TEXT NOT NULL)
- `analyzed_at` (TIMESTAMPTZ)
- `overall_score` (INTEGER) — 0-70
- `status` (TEXT) — red | yellow | green
- `metrics_score` (INTEGER) — 0-10
- `economic_buyer_score` (INTEGER) — 0-10
- `decision_criteria_score` (INTEGER) — 0-10
- `decision_process_score` (INTEGER) — 0-10
- `pain_score` (INTEGER) — 0-10
- `champion_score` (INTEGER) — 0-10
- `competition_score` (INTEGER) — 0-10
- `iterations` (INTEGER)
- `passed` (BOOLEAN)
- `full_analysis_text` (TEXT)
- `summary` (TEXT)
- `output_file` (TEXT)

### calls
- `call_id` (TEXT PRIMARY KEY)
- `company_slug` (TEXT NOT NULL)
- `company_name` (TEXT)
- `source` (TEXT NOT NULL) — fireflies | apollo
- `call_date` (DATE)
- `duration_minutes` (NUMERIC)
- `title` (TEXT)
- `formatted_summary` (TEXT)
- `competitors_mentioned` (TEXT) — comma-separated
- `has_feature_gap` (BOOLEAN)
- `has_objection` (BOOLEAN)

### objections
- `id` (UUID PRIMARY KEY)
- `call_id` (TEXT REFERENCES calls)
- `company_slug` (TEXT)
- `rep_email` (TEXT)
- `category` (TEXT)
- `verbatim_quote` (TEXT)
- `rep_response` (TEXT)
- `stage_when_raised` (TEXT)

### rep_performance
- `id` (UUID PRIMARY KEY)
- `rep_email` (TEXT NOT NULL)
- `period_start` (DATE)
- `period_end` (DATE)
- `calls_count` (INTEGER)
- `deals_analyzed` (INTEGER)
- `meddicc_avg_score` (NUMERIC)
- `champion_avg_score` (NUMERIC)
- `economic_buyer_avg_score` (NUMERIC)
- `discovery_avg_score` (NUMERIC)

## Query routing
The router identifies intent from the user's question and passes to the correct handler. Each handler:
1. Builds a targeted SQL query
2. Executes against Supabase
3. Calls Claude to synthesize the result into natural language
4. Returns formatted Slack markdown

## Handlers

### Built
- [x] `competitors.py` — competitive intelligence from calls
- [ ] `deals_at_risk.py` — deals with low scores or stalled momentum
- [ ] `close_probability.py` — forecast accuracy based on MEDDICC scores
- [ ] `objections.py` — objection patterns across deals
- [ ] `rep_performance.py` — rep scorecards and coaching insights
- [ ] `feature_gaps.py` — product gaps from call transcripts
- [ ] `process_analysis.py` — sales process bottlenecks

### Handler Template
Each handler should follow this pattern:
```python
async def handle(question: str, supabase, anthropic_key: str) -> str:
    # 1. Build SQL query
    sql = "SELECT ..."

    # 2. Execute query
    result = supabase.rpc('exec_sql', {'sql': sql}).execute()

    # 3. Synthesize with Claude
    from anthropic import Anthropic
    client = Anthropic(api_key=anthropic_key)

    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=2000,
        messages=[{
            "role": "user",
            "content": f"Question: {question}\n\nData:\n{result.data}\n\nSynthesize a concise answer in Slack markdown."
        }]
    )

    return response.content[0].text
```

## What NOT to change
- **The async pattern** (immediate 200, background processing) — critical to avoid Zapier timeouts
- **The /health endpoint** — Railway uses it for health checks
- **The ZAP_RESPONSE_URL pattern** — Zap 2 expects specific JSON fields:
  - `response_text` (string) — the answer
  - `channel` (string) — Slack channel ID from Zap 1
  - `thread_ts` (string) — Slack thread timestamp from Zap 1

## Example Zap 1 payload (POST /query)
```json
{
  "question": "What competitors are we losing to?",
  "channel": "C12345ABC",
  "thread_ts": "1234567890.123456",
  "user_id": "U12345ABC"
}
```

## Example response to ZAP_RESPONSE_URL
```json
{
  "response_text": "*Competitive Analysis*\n\nWe've mentioned 3 competitors in the last 30 days:\n\n• **LaunchDarkly** (5 deals)\n• **Optimizely** (3 deals)\n• **Statsig** (2 deals)\n\nLaunchDarkly comes up most in enterprise deals...",
  "channel": "C12345ABC",
  "thread_ts": "1234567890.123456"
}
```

## Current status
**Session:** Session 1 - Core infrastructure
**Last updated:** 2026-08-04

**Completed:**
- Repository initialized
- CLAUDE.md created
- main.py with FastAPI, /query and /health endpoints
- Async background processing pattern (avoids Zapier timeout)
- handlers/competitors.py (first working handler)
- requirements.txt, railway.toml, Procfile
- Query routing based on keywords

**Next steps:**
1. Test locally with environment variables
2. Deploy to Railway
3. Set up Zapier integration (Zap 1 + Zap 2)
4. Build additional handlers (deals_at_risk, close_probability, etc.)

**Active issues:**
None

**Notes:**
- Supabase tables already populated with 79 deals, 35 calls
- MEDDICC analyses table empty (will populate on next nightly run)
- Competitors handler ready to test with real data
- Simple keyword-based routing (can upgrade to LLM routing later)
