# RevOps CRO Agent Setup Summary

## What's Been Created

### Repository Structure
```
/Users/jeffignacio/GrowthBook/revops-cro-agent/
├── CLAUDE.md              ← Claude Code reads this first (persistent brain)
├── README.md              ← Human docs, Railway deploy button
├── FIRST_PROMPT.md        ← Copy/paste this into Claude Code
├── SETUP_SUMMARY.md       ← This file
├── .gitignore             ← Standard Python ignores
└── handlers/
    └── __init__.py        ← Package marker
```

### Files Explained

**CLAUDE.md** — The Persistent Brain
- Claude Code reads this automatically when opening the project
- Contains: architecture, schema, handler status, current session notes
- Gets updated at the end of each Claude Code session
- Next session picks up exactly where it left off

**README.md** — Human Documentation
- For GitHub visitors and deployment
- Has Railway deploy button (once template is created)
- Query examples, architecture diagram, local dev instructions

**FIRST_PROMPT.md** — Session Starter
- Copy/paste this into Claude Code to begin
- Builds: main.py, competitors handler, requirements.txt, railway.toml
- Tests the async pattern locally

### The Pattern

**Session 1:**
1. Open project in Claude Code
2. Claude Code reads CLAUDE.md automatically
3. Paste FIRST_PROMPT.md content into Claude Code
4. Claude Code builds all files
5. At end, Claude Code updates CLAUDE.md with status

**Session 2:**
1. Open project in Claude Code
2. Claude Code reads updated CLAUDE.md
3. Knows exactly what's done, what's next
4. Give new prompt: "Build deals_at_risk handler"
5. At end, Claude Code updates CLAUDE.md again

**Session N:**
Repeat. CLAUDE.md is always current. No re-explaining.

## Next Steps

### 1. Push to GitHub
```bash
cd /Users/jeffignacio/GrowthBook/revops-cro-agent

# Create GitHub repo (via gh CLI)
gh repo create revops-cro-agent --public --source=. --remote=origin --push

# Or manually:
# Go to github.com/new, create repo, then:
git remote add origin https://github.com/YOUR_USERNAME/revops-cro-agent.git
git push -u origin main
```

### 2. Open in Claude Code
```bash
# If using VS Code with Claude Code extension
code /Users/jeffignacio/GrowthBook/revops-cro-agent

# Or open via Claude Code CLI
claude-code /Users/jeffignacio/GrowthBook/revops-cro-agent
```

### 3. Give First Prompt
Copy the entire content of `FIRST_PROMPT.md` and paste into Claude Code.

Claude Code will:
- Read CLAUDE.md (knows architecture, schema, env vars)
- Build main.py with async background processing
- Build handlers/competitors.py
- Create requirements.txt, railway.toml, Procfile
- Update CLAUDE.md with completed status

### 4. Test Locally
```bash
pip install -r requirements.txt

export ANTHROPIC_API_KEY="sk-ant-..."
export SUPABASE_URL="https://htgvkqycrwesdysustxd.supabase.co"
export SUPABASE_SERVICE_KEY="eyJhbGci..."
export ZAP_RESPONSE_URL="https://hooks.zapier.com/..."

uvicorn main:app --reload
```

In another terminal:
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What competitors are we losing to?",
    "channel": "C12345",
    "thread_ts": "1234567890.123456"
  }'
```

Should see:
- Immediate 200 response: `{"status": "processing"}`
- Server logs showing background task executing
- POST to ZAP_RESPONSE_URL with formatted response

### 5. Deploy to Railway
```bash
# Install Railway CLI
npm i -g @railway/cli

# Login
railway login

# Link to project (or create new)
railway link

# Deploy
railway up
```

Or use Railway GitHub integration:
1. Connect GitHub repo in Railway dashboard
2. Railway auto-deploys on push to main
3. Set environment variables in Railway UI

### 6. Set Up Zapier

**Zap 1: Slack → Railway**
- Trigger: New message in channel (contains "@cro")
- Action: POST to https://your-railway-app.railway.app/query
  ```json
  {
    "question": "{{trigger.text}}",
    "channel": "{{trigger.channel_id}}",
    "thread_ts": "{{trigger.ts}}",
    "user_id": "{{trigger.user_id}}"
  }
  ```

**Zap 2: Railway → Slack**
- Trigger: Catch Hook (get webhook URL, set as ZAP_RESPONSE_URL)
- Action: Send channel message
  - Channel: `{{trigger.channel}}`
  - Thread: `{{trigger.thread_ts}}`
  - Message: `{{trigger.response_text}}`

### 7. Future Sessions

**Session 2 Prompt:**
```
Build handlers/deals_at_risk.py. Query deals table for:
- Deals with overall_score < 35
- Deals not analyzed in 14+ days
- Deals in late stages (negotiation, awaiting signature) with champion_score < 5

Synthesize which deals need attention and why.
Update CLAUDE.md when done.
```

**Session 3 Prompt:**
```
Build handlers/close_probability.py. For deals in a given stage,
calculate weighted close probability based on MEDDICC component scores.
Use historical win/loss data if available.
Update CLAUDE.md when done.
```

## Why This Pattern Works

**Traditional approach:**
- Session 1: Build feature A
- Session 2: "What did we build last time? Where are the files? What's the schema?"
- You re-explain everything
- Claude Code starts from scratch

**CLAUDE.md approach:**
- Session 1: Build feature A, update CLAUDE.md
- Session 2: Claude Code reads CLAUDE.md, knows everything, builds feature B
- No re-explaining
- Consistent context across sessions

**Key insight:** README.md is for humans. CLAUDE.md is for Claude Code. Keep them separate.

## Files in This Repo vs MEDDICC Agent

**MEDDICC Agent** (`/Users/jeffignacio/GrowthBook/meddicc-agent/`):
- Nightly batch job (GitHub Actions)
- Writes to Supabase (deals, analyses, calls)
- Source of truth for data

**CRO Agent** (`/Users/jeffignacio/GrowthBook/revops-cro-agent/`):
- Always-on FastAPI service (Railway)
- Reads from Supabase (query only)
- Slack interface for CRO

They're separate repos, separate deploys, but share the same Supabase database.

## Current Repo Status

```bash
cd /Users/jeffignacio/GrowthBook/revops-cro-agent
git log --oneline
```

Output:
```
396026f Add first prompt for Claude Code session
7a84572 Initial commit: RevOps CRO Query Agent scaffold
```

Ready for:
- Push to GitHub
- Open in Claude Code
- Give first prompt
- Build and deploy
