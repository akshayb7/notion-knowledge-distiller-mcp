"""
Notion Knowledge Distiller MCP Server

A Model Context Protocol server that distills chat conversations 
into structured Notion pages.
"""

import os
import json
from typing import Any
from dotenv import load_dotenv
from mcp.server import Server
from mcp.types import Tool, TextContent

try:
    from .notion_client import NotionClient
    from .prompts import DISTILL_CONVERSATION_PROMPT
except ImportError:
    # When running directly, use absolute imports
    from notion_client import NotionClient
    from prompts import DISTILL_CONVERSATION_PROMPT

# Load environment variables
load_dotenv()

# Initialize MCP server
app = Server("notion-knowledge-distiller")

# Configuration
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_PARENT_PAGE_ID = os.getenv("NOTION_PARENT_PAGE_ID")

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
    
    # Only add Notion tool if API key is configured
    if NOTION_API_KEY:
        tools.append(
            Tool(
                name="create_notion_notes",
                description=(
                    "Distill the current conversation into structured notes and create a Notion page. "
                    "This tool analyzes the conversation, extracts key insights, decisions, and action items, "
                    "then creates a well-organized Notion page. Use this when the user explicitly asks to "
                    "save, summarize, or create notes in Notion."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "conversation": {
                            "type": "string",
                            "description": (
                                "The full conversation text to analyze and distill. "
                                "Include all relevant messages from the conversation."
                            ),
                        },
                        "analysis": {
                            "type": "string",
                            "description": (
                                "Your analysis of the conversation in JSON format with fields: "
                                "title, summary, key_insights (array), decisions_made (array), "
                                "action_items (array), and topics (array). "
                                "This should be a structured distillation of the conversation."
                            ),
                        }
                    },
                    "required": ["conversation", "analysis"],
                },
            )
        )
    
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
                f"📝 Notion API Key: {'✓ Configured' if NOTION_API_KEY else '✗ Missing'}",
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
        
        if not NOTION_PARENT_PAGE_ID:
            return [
                TextContent(
                    type="text",
                    text="❌ Error: Parent page ID not configured. Please:\n"
                    "1. Create a page in Notion (e.g., 'Claude Notes')\n"
                    "2. Share it with your integration\n"
                    "3. Copy the page ID from the URL and add it to NOTION_PARENT_PAGE_ID in your .env file",
                )
            ]
        
        try:
            # Parse the analysis JSON
            analysis_json = arguments.get("analysis", "{}")
            analysis = json.loads(analysis_json)
            
            # Extract structured data
            title = analysis.get("title", "Conversation Notes")
            summary = analysis.get("summary", "")
            key_insights = analysis.get("key_insights", [])
            decisions_made = analysis.get("decisions_made", [])
            action_items = analysis.get("action_items", [])
            topics = analysis.get("topics", [])
            
            # Build Notion page content
            content_blocks = []
            
            # Add summary as a callout
            if summary:
                content_blocks.append(
                    notion_client.build_callout_block(summary, "📝")
                )
                content_blocks.append(notion_client.build_paragraph_block(""))
            
            # Add topics as a callout
            if topics:
                topics_text = "Topics: " + ", ".join(topics)
                content_blocks.append(
                    notion_client.build_callout_block(topics_text, "🏷️")
                )
                content_blocks.append(notion_client.build_paragraph_block(""))
            
            # Add key insights section
            if key_insights:
                content_blocks.append(notion_client.build_heading_block("💡 Key Insights", 2))
                for insight in key_insights:
                    content_blocks.append(notion_client.build_bulleted_list_block(insight))
                content_blocks.append(notion_client.build_paragraph_block(""))
            
            # Add decisions section
            if decisions_made:
                content_blocks.append(notion_client.build_heading_block("✅ Decisions Made", 2))
                for decision in decisions_made:
                    content_blocks.append(notion_client.build_bulleted_list_block(decision))
                content_blocks.append(notion_client.build_paragraph_block(""))
            
            # Add action items section
            if action_items:
                content_blocks.append(notion_client.build_heading_block("📋 Action Items", 2))
                for item in action_items:
                    content_blocks.append(notion_client.build_todo_block(item, checked=False))
                content_blocks.append(notion_client.build_paragraph_block(""))
            
            # Create the Notion page
            page_result = notion_client.create_page(
                title=title,
                content_blocks=content_blocks,
                parent_page_id=NOTION_PARENT_PAGE_ID,  # Use configured parent page
            )
            
            # Get page URL
            page_url = page_result.get("url", "")
            page_id = page_result.get("id", "")
            
            return [
                TextContent(
                    type="text",
                    text=f"✅ Successfully created Notion page!\n\n"
                    f"📄 **Title**: {title}\n"
                    f"🔗 **URL**: {page_url}\n"
                    f"🆔 **Page ID**: {page_id}\n\n"
                    f"The page has been created in your Notion workspace with:\n"
                    f"- Summary and topics\n"
                    f"- {len(key_insights)} key insights\n"
                    f"- {len(decisions_made)} decisions\n"
                    f"- {len(action_items)} action items",
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