"""
Prompts and schemas for conversation classification and structuring.
"""

# Conversation type definitions
CONVERSATION_TYPES = {
    "project_problem_solving": {
        "description": "Technical problem solving, debugging, building projects, implementation discussions",
        "sections": ["key_insights", "decisions_made", "action_items"]
    },
    "idea_brainstorming": {
        "description": "Exploring ideas, creative discussions, conceptual thinking, what-if scenarios",
        "sections": ["core_ideas", "interesting_points", "follow_up_questions"]
    },
    "learning_educational": {
        "description": "Learning new concepts, explanations, tutorials, deep dives into topics",
        "sections": ["key_concepts", "examples", "takeaways"]
    },
    "general_discussion": {
        "description": "General Q&A, casual chat, mixed topics, simple queries",
        "sections": ["main_points"]
    }
}

# Schema templates for each conversation type
SCHEMA_TEMPLATES = {
    "project_problem_solving": {
        "title": "string (max 100 chars)",
        "summary": "string (2-3 sentences)",
        "key_insights": ["array of strings"],
        "decisions_made": ["array of strings"],
        "action_items": ["array of strings"],
        "topics": ["array of 3-5 keywords"]
    },
    "idea_brainstorming": {
        "title": "string (max 100 chars)",
        "summary": "string (2-3 sentences)",
        "core_ideas": ["array of strings"],
        "interesting_points": ["array of strings"],
        "follow_up_questions": ["array of strings"],
        "topics": ["array of 3-5 keywords"]
    },
    "learning_educational": {
        "title": "string (max 100 chars)",
        "summary": "string (2-3 sentences)",
        "key_concepts": ["array of strings"],
        "examples": ["array of strings"],
        "takeaways": ["array of strings"],
        "topics": ["array of 3-5 keywords"]
    },
    "general_discussion": {
        "title": "string (max 100 chars)",
        "summary": "string (2-3 sentences)",
        "main_points": ["array of strings"],
        "topics": ["array of 3-5 keywords"]
    }
}

CLASSIFY_CONVERSATION_PROMPT = """Analyze this conversation and classify its type.

CONVERSATION TYPES:
1. **project_problem_solving**: Technical implementation, debugging, building projects, solving problems, making decisions
2. **idea_brainstorming**: Exploring ideas, creative discussions, conceptual thinking, what-if scenarios
3. **learning_educational**: Learning concepts, explanations, tutorials, deep dives, understanding topics
4. **general_discussion**: General Q&A, casual chat, mixed topics, simple queries

Choose the PRIMARY type that best represents the conversation. If the conversation has mixed elements, choose the dominant one.

Return ONLY a valid JSON object with this structure:
{
  "type": "project_problem_solving",
  "confidence": "high",
  "reasoning": "Brief explanation of why this classification was chosen"
}

CONFIDENCE LEVELS:
- "high": Clearly fits one category
- "medium": Has elements of multiple types but one is dominant
- "low": Ambiguous or mixed, defaulting to best guess

IMPORTANT: Return ONLY the JSON object. No markdown, no code blocks, no extra text.
"""

EXTRACT_CONVERSATION_PROMPT = """Extract structured knowledge from this conversation based on its type.

CONVERSATION TYPE: {conversation_type}

Return your analysis in this EXACT JSON format:

{schema}

GUIDELINES:
- Title should be specific and descriptive (max 100 chars)
- Summary should be 2-3 sentences capturing the essence
- Be concise but informative in all sections
- Use empty arrays [] for sections with no content
- Topics should be 3-5 relevant keywords for categorization
- Focus on substance over style

CRITICAL: Return ONLY valid JSON. No markdown, no code blocks, no explanatory text. Just the raw JSON object.
"""