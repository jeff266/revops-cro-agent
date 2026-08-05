"""
Query handlers for CRO agent.

Each handler:
1. Queries Supabase
2. Synthesizes with Claude
3. Returns Slack-formatted markdown
"""

from . import competitors

__all__ = ['competitors']
