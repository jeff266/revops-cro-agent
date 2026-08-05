"""
Competitive Intelligence Handler

Queries calls table for competitor mentions and synthesizes insights.
"""

from anthropic import Anthropic
from supabase import Client


async def handle(question: str, supabase: Client, anthropic_key: str) -> str:
    """
    Query calls for competitor mentions, synthesize with Claude.

    Args:
        question: User's question from Slack
        supabase: Supabase client
        anthropic_key: Anthropic API key

    Returns:
        Slack-formatted markdown response
    """

    # Query calls with competitor mentions
    response = supabase.table('calls') \
        .select('call_id, company_name, company_slug, source, call_date, title, competitors_mentioned') \
        .not_.is_('competitors_mentioned', 'null') \
        .order('call_date', desc=True) \
        .limit(100) \
        .execute()

    calls = response.data

    if not calls:
        return (
            "📊 **Competitive Analysis**\n\n"
            "No competitor mentions found in recent calls.\n\n"
            "_Note: Competitor detection runs during nightly analysis._"
        )

    # Group by competitor
    competitor_stats = {}
    call_details = []

    for call in calls:
        competitors = call.get('competitors_mentioned', '').split(',')
        company = call.get('company_name', 'Unknown')
        date = call.get('call_date', 'Unknown date')
        title = call.get('title', '')

        for comp in competitors:
            comp = comp.strip()
            if comp:
                if comp not in competitor_stats:
                    competitor_stats[comp] = {
                        'count': 0,
                        'companies': set(),
                        'calls': []
                    }

                competitor_stats[comp]['count'] += 1
                competitor_stats[comp]['companies'].add(company)
                competitor_stats[comp]['calls'].append({
                    'company': company,
                    'date': date,
                    'title': title
                })

        call_details.append({
            'company': company,
            'date': date,
            'title': title,
            'competitors': ', '.join(competitors)
        })

    # Prepare data for Claude
    competitor_summary = []
    for comp, stats in sorted(competitor_stats.items(), key=lambda x: x[1]['count'], reverse=True):
        companies_list = ', '.join(sorted(stats['companies']))
        competitor_summary.append(
            f"{comp}: {stats['count']} mentions across {len(stats['companies'])} companies ({companies_list})"
        )

    data_summary = {
        'total_calls': len(calls),
        'competitors_found': len(competitor_stats),
        'competitor_breakdown': competitor_summary[:10],  # Top 10
        'recent_examples': call_details[:15]  # Recent 15
    }

    # Synthesize with Claude
    client = Anthropic(api_key=anthropic_key)

    prompt = f"""You are analyzing competitive intelligence from sales calls.

User Question: {question}

Data Summary:
- Total calls with competitor mentions: {data_summary['total_calls']}
- Unique competitors found: {data_summary['competitors_found']}

Top Competitors:
{chr(10).join('• ' + s for s in data_summary['competitor_breakdown'])}

Recent Call Examples:
{chr(10).join(f"• {c['company']} ({c['date']}): {c['competitors']}" for c in data_summary['recent_examples'])}

Instructions:
1. Answer the user's question directly
2. Highlight the top 3-5 competitors by mention frequency
3. Note any patterns (e.g., which competitors appear in enterprise vs SMB deals)
4. Use Slack markdown formatting:
   - **Bold** for competitor names
   - • Bullets for lists
   - Keep it concise (under 300 words)
5. Start with a clear header like "📊 **Competitive Analysis**"
"""

    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=2000,
        messages=[{
            "role": "user",
            "content": prompt
        }]
    )

    return response.content[0].text
