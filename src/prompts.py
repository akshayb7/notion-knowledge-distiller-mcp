"""
Prompts for structuring conversation content.
"""

DISTILL_CONVERSATION_PROMPT = """Analyze this conversation and extract structured knowledge from it.

Your task is to distill the conversation into a clean, organized format suitable for a knowledge base.

Return your analysis in the following JSON format:

{
  "title": "A concise, descriptive title for this conversation (max 100 chars)",
  "summary": "A 2-3 sentence high-level summary of what was discussed",
  "key_insights": [
    "First key insight or learning from the conversation",
    "Second key insight or learning",
    "etc."
  ],
  "decisions_made": [
    "Any decisions that were reached",
    "Technical choices or approaches agreed upon",
    "etc."
  ],
  "action_items": [
    "Concrete next steps or tasks to complete",
    "Implementation todos",
    "etc."
  ],
  "topics": [
    "topic1",
    "topic2",
    "topic3"
  ]
}

Guidelines:
- **Title**: Should be specific and descriptive, not generic
- **Summary**: Capture the essence of the conversation
- **Key Insights**: Important learnings, realizations, or conclusions
- **Decisions Made**: Concrete choices or agreements (empty array if none)
- **Action Items**: Specific tasks or next steps (empty array if none)
- **Topics**: 3-5 relevant keywords/tags for categorization

Only include sections that are relevant. If there are no decisions or action items, use empty arrays.

Be concise but informative. Focus on substance over style.

IMPORTANT: Return ONLY valid JSON. Do not include any markdown formatting, code blocks, or explanatory text. Just the raw JSON object.
"""