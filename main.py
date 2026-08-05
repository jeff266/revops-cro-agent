"""
RevOps CRO Query Agent - FastAPI Service

Receives queries from Slack via Zapier, processes in background,
and posts responses back to Slack via webhook.
"""

import os
import httpx
from typing import Optional
from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
from supabase import create_client, Client
from handlers import competitors


app = FastAPI(title="RevOps CRO Query Agent")


# Environment variables
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
ZAP_RESPONSE_URL = os.getenv("ZAP_RESPONSE_URL")

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


class QueryRequest(BaseModel):
    """Incoming query from Zapier (Slack)"""
    question: str
    channel: str
    thread_ts: str
    user_id: Optional[str] = None


class QueryResponse(BaseModel):
    """Immediate response to acknowledge query"""
    status: str


@app.get("/health")
async def health_check():
    """Health check endpoint for Railway"""
    return {"status": "healthy", "service": "revops-cro-agent"}


@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest, background_tasks: BackgroundTasks):
    """
    Receive query from Zapier, return 200 immediately,
    process in background to avoid timeout.
    """
    # Validate env vars
    if not all([ANTHROPIC_API_KEY, SUPABASE_URL, SUPABASE_SERVICE_KEY, ZAP_RESPONSE_URL]):
        raise HTTPException(
            status_code=500,
            detail="Missing required environment variables"
        )

    # Queue background task
    background_tasks.add_task(
        process_query,
        question=request.question,
        channel=request.channel,
        thread_ts=request.thread_ts
    )

    # Return immediately (avoid Zapier timeout)
    return QueryResponse(status="processing")


async def process_query(question: str, channel: str, thread_ts: str):
    """
    Background task: route query to handler, get response, post to Zapier.
    """
    try:
        # Route to appropriate handler
        response_text = await route_query(question)

        # Post response to Zapier webhook
        await post_to_zapier(
            response_text=response_text,
            channel=channel,
            thread_ts=thread_ts
        )

    except Exception as e:
        # Post error to Zapier
        error_message = f"❌ Error processing query: {str(e)}"
        await post_to_zapier(
            response_text=error_message,
            channel=channel,
            thread_ts=thread_ts
        )


async def route_query(question: str) -> str:
    """
    Route question to appropriate handler based on intent.
    Start with simple keyword matching.
    """
    question_lower = question.lower()

    # Competitive intelligence
    if any(word in question_lower for word in ['competitor', 'competition', 'losing to', 'versus']):
        return await competitors.handle(question, supabase, ANTHROPIC_API_KEY)

    # Default response for unmatched queries
    return (
        "I'm not sure how to answer that yet. I can currently help with:\n\n"
        "• **Competitive Intelligence** - Ask about competitors mentioned in calls\n"
        "\nMore handlers coming soon!"
    )


async def post_to_zapier(response_text: str, channel: str, thread_ts: str):
    """Post response back to Zapier catch hook (Zap 2)"""
    payload = {
        "response_text": response_text,
        "channel": channel,
        "thread_ts": thread_ts
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            ZAP_RESPONSE_URL,
            json=payload,
            timeout=30.0
        )
        response.raise_for_status()


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
