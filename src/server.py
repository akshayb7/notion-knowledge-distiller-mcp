"""
Notion Knowledge Distiller MCP Server

A Model Context Protocol server that distills chat conversations 
into structured Notion pages with adaptive formatting based on conversation type.
"""

import os
import json
from typing import Any
from dotenv import load_dotenv
from mcp.server import Server
from mcp.types import Tool, TextContent

try:
    from .notion_client import NotionClient
    from .prompts import (
        CONVERSATION_TYPES,
        SCHEMA_TEMPLATES,
        CLASSIFY_CONVERSATION_PROMPT,
        EXTRACT_CONVERSATION_PROMPT
    )
except ImportError:
    # When running directly, use absolute imports
    from notion_client import NotionClient
    from prompts import (
        CONVERSATION_TYPES,
        SCHEMA_TEMPLATES,
        CLASSIFY_CONVERSATION_PROMPT,
        EXTRACT_CONVERSATION_PROMPT
    )

# Load environment variables
load_dotenv()

# Initialize MCP server
app = Server("notion-knowledge-distiller")

# Configuration
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_PARENT_PAGE_ID = os.getenv("NOTION_PARENT_PAGE_ID")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

# Initialize Notion client if API key is available
notion_client = NotionClient(NOTION_API_KEY) if NOTION_API_KEY else None


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    tools = [
        Tool(
            name="ping",
            description="Test tool to verify the MCP server is working correctly",
            inputSchema={
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "A message to echo back",
                    }
                },
                "required": ["message"],
            },
        ),
    ]
    
    # Only add Notion tools if API key is configured
    if NOTION_API_KEY:
        tools.extend([
            Tool(
                name="classify_conversation",
                description=(
                    "Classify the type of the current conversation. "
                    "Analyzes the conversation and returns the primary type: "
                    "project_problem_solving, idea_brainstorming, learning_educational, or general_discussion. "
                    "This should be called FIRST before creating Notion notes."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "classification": {
                            "type": "string",
                            "description": (
                                "Your classification of the conversation in JSON format with fields: "
                                "type (one of: project_problem_solving, idea_brainstorming, learning_educational, general_discussion), "
                                "confidence (high/medium/low), and reasoning (brief explanation)."
                            ),
                        }
                    },
                    "required": ["classification"],
                },
            ),
            Tool(
                name="create_notion_notes",
                description=(
                    "Create structured notes in Notion based on the classified conversation type. "
                    "This should be called AFTER classify_conversation. "
                    "Extracts relevant information and creates a well-organized Notion page."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "conversation_type": {
                            "type": "string",
                            "description": (
                                "The conversation type from classify_conversation. "
                                "Must be one of: project_problem_solving, idea_brainstorming, "
                                "learning_educational, general_discussion"
                            ),
                        },
                        "analysis": {
                            "type": "string",
                            "description": (
                                "Your structured analysis of the conversation in JSON format. "
                                "The fields should match the conversation_type:\n"
                                "- project_problem_solving: title, summary, key_insights, decisions_made, action_items, topics\n"
                                "- idea_brainstorming: title, summary, core_ideas, interesting_points, follow_up_questions, topics\n"
                                "- learning_educational: title, summary, key_concepts, examples, takeaways, topics\n"
                                "- general_discussion: title, summary, main_points, topics"
                            ),
                        }
                    },
                    "required": ["conversation_type", "analysis"],
                },
            ),
        ])
        
        # Only add search/read tools if database is configured
        if NOTION_DATABASE_ID:
            tools.extend([
                Tool(
                    name="search_notes",
                    description=(
                        "Search through past conversation notes in the Notion database. "
                        "Can search by title keywords, topics, conversation type, or combinations. "
                        "Returns a list of matching notes with their metadata."
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": (
                                    "Search query - can be keywords from title, topics to search for, or conversation type. "
                                    "Examples: 'Unity', 'Python MCP', 'brainstorming about games'"
                                ),
                            },
                            "conversation_type": {
                                "type": "string",
                                "description": (
                                    "Optional filter by conversation type. "
                                    "One of: Project Problem Solving, Idea Brainstorming, Learning Educational, General Discussion"
                                ),
                            },
                            "limit": {
                                "type": "number",
                                "description": "Maximum number of results to return (default 10, max 20)",
                            }
                        },
                        "required": ["query"],
                    },
                ),
                Tool(
                    name="read_note",
                    description=(
                        "Read the full content of a specific note from the database. "
                        "Use this after search_notes to get the complete details of a note. "
                        "Returns the formatted content including all sections."
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "note_id": {
                                "type": "string",
                                "description": "The ID of the note to read (from search_notes results)",
                            }
                        },
                        "required": ["note_id"],
                    },
                ),
            ])
    
    return tools


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls."""
    
    if name == "ping":
        message = arguments.get("message", "Hello!")
        return [
            TextContent(
                type="text",
                text=f"🏓 Pong! You said: {message}\n\n"
                f"✅ MCP Server is running!\n"
                f"📝 Notion API Key: {'✓ Configured' if NOTION_API_KEY else '✗ Missing'}\n"
                f"📄 Parent Page ID: {'✓ Configured' if NOTION_PARENT_PAGE_ID else '✗ Not set (optional)'}\n"
                f"🗄️ Database ID: {'✓ Configured' if NOTION_DATABASE_ID else '✗ Missing'}",
            )
        ]
    
    elif name == "classify_conversation":
        try:
            # Parse the classification JSON
            classification_json = arguments.get("classification", "{}")
            classification = json.loads(classification_json)
            
            # Extract fields
            conv_type = classification.get("type", "general_discussion")
            confidence = classification.get("confidence", "medium")
            reasoning = classification.get("reasoning", "No reasoning provided")
            
            # Validate conversation type
            valid_types = list(CONVERSATION_TYPES.keys())
            if conv_type not in valid_types:
                conv_type = "general_discussion"
            
            # Get type info
            type_info = CONVERSATION_TYPES[conv_type]
            type_display = conv_type.replace("_", " ").title()
            
            return [
                TextContent(
                    type="text",
                    text=f"✅ Conversation Classified!\n\n"
                    f"📑 **Type**: {type_display}\n"
                    f"🎯 **Confidence**: {confidence}\n"
                    f"💭 **Reasoning**: {reasoning}\n\n"
                    f"This conversation will be structured with sections:\n"
                    f"{', '.join(type_info['sections'])}\n\n"
                    f"Ready to create the Notion page with this structure!",
                )
            ]
        
        except json.JSONDecodeError as e:
            return [
                TextContent(
                    type="text",
                    text=f"❌ Error: Failed to parse classification JSON.\n\nError: {str(e)}",
                )
            ]
        except Exception as e:
            return [
                TextContent(
                    type="text",
                    text=f"❌ Error classifying conversation: {str(e)}",
                )
            ]
    
    elif name == "create_notion_notes":
        if not notion_client:
            return [
                TextContent(
                    type="text",
                    text="❌ Error: Notion API key not configured. Please set NOTION_API_KEY in your .env file.",
                )
            ]
        
        # Check if we should use database or pages
        use_database = bool(NOTION_DATABASE_ID)
        
        if not use_database and not NOTION_PARENT_PAGE_ID:
            return [
                TextContent(
                    type="text",
                    text="❌ Error: Neither database ID nor parent page ID configured.\n"
                    "Please set either NOTION_DATABASE_ID (recommended) or NOTION_PARENT_PAGE_ID in your .env file.",
                )
            ]
        
        try:
            # Get conversation type and analysis
            conversation_type = arguments.get("conversation_type", "general_discussion")
            analysis_json = arguments.get("analysis", "{}")
            
            # Validate conversation type
            valid_types = list(CONVERSATION_TYPES.keys())
            if conversation_type not in valid_types:
                return [
                    TextContent(
                        type="text",
                        text=f"❌ Error: Invalid conversation type '{conversation_type}'. "
                        f"Must be one of: {', '.join(valid_types)}",
                    )
                ]
            
            # Parse the analysis JSON
            analysis = json.loads(analysis_json)
            
            # Extract title and topics
            title = analysis.get("title", "Conversation Notes")
            topics = analysis.get("topics", [])
            
            # Get confidence from previous classification (default to medium if not available)
            confidence = "medium"  # We'll pass this from classify_conversation in Phase 4
            
            # Build page content based on conversation type
            content_blocks = notion_client.build_page_content(conversation_type, analysis)
            
            # Create database entry or page based on configuration
            if use_database:
                # Create database entry
                page_result = notion_client.create_database_entry(
                    database_id=NOTION_DATABASE_ID,
                    title=title,
                    conversation_type=conversation_type,
                    topics=topics,
                    confidence=confidence,
                    content_blocks=content_blocks,
                )
                storage_type = "database entry"
            else:
                # Create page (legacy support)
                page_result = notion_client.create_page(
                    title=title,
                    content_blocks=content_blocks,
                    parent_page_id=NOTION_PARENT_PAGE_ID,
                )
                storage_type = "page"
            
            # Get page details
            page_url = page_result.get("url", "")
            page_id = page_result.get("id", "")
            
            # Count sections for response
            type_name = conversation_type.replace("_", " ").title()
            
            if conversation_type == "project_problem_solving":
                section_counts = {
                    "insights": len(analysis.get("key_insights", [])),
                    "decisions": len(analysis.get("decisions_made", [])),
                    "action_items": len(analysis.get("action_items", []))
                }
                sections_text = f"- {section_counts['insights']} key insights\n- {section_counts['decisions']} decisions\n- {section_counts['action_items']} action items"
            
            elif conversation_type == "idea_brainstorming":
                section_counts = {
                    "ideas": len(analysis.get("core_ideas", [])),
                    "points": len(analysis.get("interesting_points", [])),
                    "questions": len(analysis.get("follow_up_questions", []))
                }
                sections_text = f"- {section_counts['ideas']} core ideas\n- {section_counts['points']} interesting points\n- {section_counts['questions']} follow-up questions"
            
            elif conversation_type == "learning_educational":
                section_counts = {
                    "concepts": len(analysis.get("key_concepts", [])),
                    "examples": len(analysis.get("examples", [])),
                    "takeaways": len(analysis.get("takeaways", []))
                }
                sections_text = f"- {section_counts['concepts']} key concepts\n- {section_counts['examples']} examples\n- {section_counts['takeaways']} takeaways"
            
            else:  # general_discussion
                section_counts = {
                    "points": len(analysis.get("main_points", []))
                }
                sections_text = f"- {section_counts['points']} main points"
            
            return [
                TextContent(
                    type="text",
                    text=f"✅ Successfully created Notion {storage_type}!\n\n"
                    f"📄 **Title**: {title}\n"
                    f"📑 **Type**: {type_name}\n"
                    f"🗄️ **Storage**: {'Database' if use_database else 'Page'}\n"
                    f"🔗 **URL**: {page_url}\n"
                    f"🆔 **ID**: {page_id}\n\n"
                    f"The {storage_type} includes:\n"
                    f"{sections_text}",
                )
            ]
        
        except json.JSONDecodeError as e:
            return [
                TextContent(
                    type="text",
                    text=f"❌ Error: Failed to parse analysis JSON. Please ensure the analysis is valid JSON.\n\nError: {str(e)}",
                )
            ]
        except Exception as e:
            return [
                TextContent(
                    type="text",
                    text=f"❌ Error creating Notion page: {str(e)}",
                )
            ]
    
    elif name == "search_notes":
        if not notion_client or not NOTION_DATABASE_ID:
            return [
                TextContent(
                    type="text",
                    text="❌ Error: Database not configured. Search is only available with Notion database setup.",
                )
            ]
        
        try:
            query = arguments.get("query", "")
            conversation_type = arguments.get("conversation_type")
            limit = arguments.get("limit", 10)
            limit = min(int(limit), 20)  # Cap at 20
            
            # Build filter conditions
            filter_conditions = None
            
            # If conversation type is specified, filter by it
            if conversation_type:
                filter_conditions = {
                    "property": "Type",
                    "select": {
                        "equals": conversation_type
                    }
                }
            
            # Query the database
            results = notion_client.query_database(
                database_id=NOTION_DATABASE_ID,
                filter_conditions=filter_conditions,
                sorts=[{"property": "Date", "direction": "descending"}],
                page_size=limit,
            )
            
            # Format results
            formatted_results = notion_client.format_search_results(results)
            
            # Filter by query string (title/topics) in memory since Notion API doesn't support full-text search
            if query:
                query_lower = query.lower()
                filtered_results = [
                    r for r in formatted_results
                    if query_lower in r["title"].lower() or query_lower in r["topics"].lower()
                ]
            else:
                filtered_results = formatted_results
            
            if not filtered_results:
                return [
                    TextContent(
                        type="text",
                        text=f"🔍 No notes found matching '{query}'"
                        + (f" with type '{conversation_type}'" if conversation_type else ""),
                    )
                ]
            
            # Format response
            result_text = f"🔍 Found {len(filtered_results)} note(s)"
            if query:
                result_text += f" matching '{query}'"
            if conversation_type:
                result_text += f" (Type: {conversation_type})"
            result_text += ":\n\n"
            
            for i, result in enumerate(filtered_results, 1):
                result_text += f"{i}. **{result['title']}**\n"
                result_text += f"   - Type: {result['type']}\n"
                result_text += f"   - Date: {result['date']}\n"
                result_text += f"   - Topics: {result['topics']}\n"
                result_text += f"   - Status: {result['status']}\n"
                result_text += f"   - ID: `{result['id']}`\n"
                result_text += f"   - URL: {result['url']}\n\n"
            
            result_text += "\n💡 Use `read_note` with an ID to see the full content."
            
            return [
                TextContent(
                    type="text",
                    text=result_text,
                )
            ]
        
        except Exception as e:
            return [
                TextContent(
                    type="text",
                    text=f"❌ Error searching notes: {str(e)}",
                )
            ]
    
    elif name == "read_note":
        if not notion_client:
            return [
                TextContent(
                    type="text",
                    text="❌ Error: Notion client not configured.",
                )
            ]
        
        try:
            note_id = arguments.get("note_id", "")
            
            if not note_id:
                return [
                    TextContent(
                        type="text",
                        text="❌ Error: note_id is required. Use search_notes to find note IDs.",
                    )
                ]
            
            # Get page content
            page_data = notion_client.get_page_content(note_id)
            
            # Format content
            formatted_content = notion_client.format_page_content(page_data)
            
            return [
                TextContent(
                    type="text",
                    text=f"📄 **Note Content:**\n\n{formatted_content}",
                )
            ]
        
        except Exception as e:
            return [
                TextContent(
                    type="text",
                    text=f"❌ Error reading note: {str(e)}",
                )
            ]
    
    raise ValueError(f"Unknown tool: {name}")


def main():
    """Run the MCP server."""
    import asyncio
    import mcp.server.stdio
    
    async def run():
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await app.run(
                read_stream,
                write_stream,
                app.create_initialization_options(),
            )
    
    asyncio.run(run())


if __name__ == "__main__":
    main()