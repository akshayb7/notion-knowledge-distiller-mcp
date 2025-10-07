"""
Notion API client for creating structured knowledge pages and database entries.
"""

import requests
from typing import Optional, Dict, Any, List
from datetime import datetime


class NotionClient:
    """Client for interacting with the Notion API."""
    
    def __init__(self, api_key: str):
        """
        Initialize Notion client.
        
        Args:
            api_key: Notion integration API key
        """
        self.api_key = api_key
        self.base_url = "https://api.notion.com/v1"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28",
        }
    
    def create_database_entry(
        self,
        database_id: str,
        title: str,
        conversation_type: str,
        topics: List[str],
        confidence: str,
        content_blocks: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Create a new entry in a Notion database.
        
        Args:
            database_id: The database ID to create the entry in
            title: Entry title
            conversation_type: Type of conversation (project_problem_solving, etc.)
            topics: List of topic tags
            confidence: Classification confidence (high, medium, low)
            content_blocks: List of Notion block objects for page content
        
        Returns:
            Dictionary containing the created page data including URL
        
        Raises:
            Exception: If the API request fails
        """
        # Map conversation types to display names
        type_mapping = {
            "project_problem_solving": "Project Problem Solving",
            "idea_brainstorming": "Idea Brainstorming",
            "learning_educational": "Learning Educational",
            "general_discussion": "General Discussion"
        }
        
        # Prepare database entry data
        entry_data = {
            "parent": {
                "type": "database_id",
                "database_id": database_id
            },
            "properties": {
                "Title": {
                    "title": [
                        {
                            "text": {
                                "content": title
                            }
                        }
                    ]
                },
                "Type": {
                    "select": {
                        "name": type_mapping.get(conversation_type, "General Discussion")
                    }
                },
                "Date": {
                    "date": {
                        "start": datetime.now().isoformat()
                    }
                },
                "Topics": {
                    "multi_select": [
                        {"name": topic} for topic in topics
                    ]
                },
                "Status": {
                    "select": {
                        "name": "New"
                    }
                },
                "Confidence": {
                    "select": {
                        "name": confidence.capitalize()
                    }
                }
            },
            "children": content_blocks,
        }
        
        # Make API request
        response = requests.post(
            f"{self.base_url}/pages",
            headers=self.headers,
            json=entry_data,
        )
        
        if response.status_code != 200:
            error_data = response.json()
            raise Exception(
                f"Failed to create Notion database entry: {response.status_code} - "
                f"{error_data.get('message', 'Unknown error')}"
            )
        
        return response.json()
    
    def query_database(
        self,
        database_id: str,
        filter_conditions: Optional[Dict[str, Any]] = None,
        sorts: Optional[List[Dict[str, Any]]] = None,
        page_size: int = 10,
    ) -> Dict[str, Any]:
        """
        Query a Notion database with filters and sorting.
        
        Args:
            database_id: The database ID to query
            filter_conditions: Optional filter object (Notion API format)
            sorts: Optional list of sort objects
            page_size: Number of results to return (default 10, max 100)
        
        Returns:
            Dictionary containing query results
        
        Raises:
            Exception: If the API request fails
        """
        query_data = {
            "page_size": min(page_size, 100)
        }
        
        if filter_conditions:
            query_data["filter"] = filter_conditions
        
        if sorts:
            query_data["sorts"] = sorts
        
        response = requests.post(
            f"{self.base_url}/databases/{database_id}/query",
            headers=self.headers,
            json=query_data,
        )
        
        if response.status_code != 200:
            error_data = response.json()
            raise Exception(
                f"Failed to query Notion database: {response.status_code} - "
                f"{error_data.get('message', 'Unknown error')}"
            )
        
        return response.json()
    
    def get_page_content(self, page_id: str) -> Dict[str, Any]:
        """
        Get the full content of a Notion page including all blocks.
        
        Args:
            page_id: The page ID to retrieve
        
        Returns:
            Dictionary containing page data and content blocks
        
        Raises:
            Exception: If the API request fails
        """
        # Get page properties
        page_response = requests.get(
            f"{self.base_url}/pages/{page_id}",
            headers=self.headers,
        )
        
        if page_response.status_code != 200:
            error_data = page_response.json()
            raise Exception(
                f"Failed to get page: {page_response.status_code} - "
                f"{error_data.get('message', 'Unknown error')}"
            )
        
        page_data = page_response.json()
        
        # Get page blocks (content)
        blocks_response = requests.get(
            f"{self.base_url}/blocks/{page_id}/children",
            headers=self.headers,
        )
        
        if blocks_response.status_code != 200:
            error_data = blocks_response.json()
            raise Exception(
                f"Failed to get page blocks: {blocks_response.status_code} - "
                f"{error_data.get('message', 'Unknown error')}"
            )
        
        blocks_data = blocks_response.json()
        
        return {
            "page": page_data,
            "blocks": blocks_data.get("results", [])
        }
    
    def format_search_results(self, query_results: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Format database query results into a readable structure.
        
        Args:
            query_results: Raw query results from Notion API
        
        Returns:
            List of formatted result dictionaries
        """
        formatted_results = []
        
        for page in query_results.get("results", []):
            properties = page.get("properties", {})
            
            # Extract title
            title_prop = properties.get("Title", {}).get("title", [])
            title = title_prop[0].get("text", {}).get("content", "Untitled") if title_prop else "Untitled"
            
            # Extract type
            type_prop = properties.get("Type", {}).get("select")
            page_type = type_prop.get("name") if type_prop else "Unknown"
            
            # Extract date
            date_prop = properties.get("Date", {}).get("date")
            date = date_prop.get("start") if date_prop else "Unknown"
            
            # Extract topics
            topics_prop = properties.get("Topics", {}).get("multi_select", [])
            topics = [topic.get("name") for topic in topics_prop]
            
            # Extract status
            status_prop = properties.get("Status", {}).get("select")
            status = status_prop.get("name") if status_prop else "Unknown"
            
            formatted_results.append({
                "id": page.get("id"),
                "title": title,
                "type": page_type,
                "date": date,
                "topics": ", ".join(topics) if topics else "None",
                "status": status,
                "url": page.get("url", "")
            })
        
        return formatted_results
    
    def format_page_content(self, page_data: Dict[str, Any]) -> str:
        """
        Format page content into readable text.
        
        Args:
            page_data: Page data including blocks from get_page_content()
        
        Returns:
            Formatted string of page content
        """
        page = page_data.get("page", {})
        blocks = page_data.get("blocks", [])
        
        # Get title
        properties = page.get("properties", {})
        title_prop = properties.get("Title", {}).get("title", [])
        title = title_prop[0].get("text", {}).get("content", "Untitled") if title_prop else "Untitled"
        
        # Start with title
        content_lines = [f"# {title}\n"]
        
        # Process blocks
        for block in blocks:
            block_type = block.get("type")
            
            if block_type == "heading_2":
                text = self._extract_text_from_block(block, block_type)
                content_lines.append(f"\n## {text}\n")
            
            elif block_type == "heading_3":
                text = self._extract_text_from_block(block, block_type)
                content_lines.append(f"\n### {text}\n")
            
            elif block_type == "paragraph":
                text = self._extract_text_from_block(block, block_type)
                if text:
                    content_lines.append(f"{text}\n")
            
            elif block_type == "bulleted_list_item":
                text = self._extract_text_from_block(block, block_type)
                content_lines.append(f"- {text}")
            
            elif block_type == "to_do":
                text = self._extract_text_from_block(block, block_type)
                checked = block.get(block_type, {}).get("checked", False)
                checkbox = "[x]" if checked else "[ ]"
                content_lines.append(f"{checkbox} {text}")
            
            elif block_type == "callout":
                text = self._extract_text_from_block(block, block_type)
                content_lines.append(f"> {text}\n")
            
            elif block_type == "divider":
                content_lines.append("---\n")
        
        return "\n".join(content_lines)
    
    def _extract_text_from_block(self, block: Dict[str, Any], block_type: str) -> str:
        """Extract plain text from a block's rich_text array."""
        rich_text = block.get(block_type, {}).get("rich_text", [])
        return "".join([text.get("plain_text", "") for text in rich_text])
    
    def append_to_page(
        self,
        page_id: str,
        new_blocks: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Append new blocks to an existing Notion page.
        
        Args:
            page_id: The page ID to append to
            new_blocks: List of Notion block objects to append
        
        Returns:
            Response from Notion API
        
        Raises:
            Exception: If the API request fails
        """
        response = requests.patch(
            f"{self.base_url}/blocks/{page_id}/children",
            headers=self.headers,
            json={"children": new_blocks},
        )
        
        if response.status_code != 200:
            error_data = response.json()
            raise Exception(
                f"Failed to append to page: {response.status_code} - "
                f"{error_data.get('message', 'Unknown error')}"
            )
        
        return response.json()
    
    def update_page_properties(
        self,
        page_id: str,
        properties: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Update properties of an existing Notion page.
        
        Args:
            page_id: The page ID to update
            properties: Properties to update (Notion API format)
        
        Returns:
            Updated page data
        
        Raises:
            Exception: If the API request fails
        """
        response = requests.patch(
            f"{self.base_url}/pages/{page_id}",
            headers=self.headers,
            json={"properties": properties},
        )
        
        if response.status_code != 200:
            error_data = response.json()
            raise Exception(
                f"Failed to update page properties: {response.status_code} - "
                f"{error_data.get('message', 'Unknown error')}"
            )
        
        return response.json()
    
    def build_update_content(
        self,
        conversation_type: str,
        analysis: Dict[str, Any],
        session_number: int = 2,
    ) -> List[Dict[str, Any]]:
        """
        Build content blocks for updating a note with a new session.
        
        Args:
            conversation_type: Type of conversation
            analysis: Structured analysis data for the new session
            session_number: Session number for the header
        
        Returns:
            List of Notion block objects for the update
        """
        blocks = []
        
        # Add divider
        blocks.append(self.build_divider_block())
        blocks.append(self.build_paragraph_block(""))
        
        # Add update header with date
        update_date = datetime.now().strftime("%B %d, %Y")
        blocks.append(self.build_heading_block(f"Update - {update_date}", 2))
        blocks.append(self.build_paragraph_block(""))
        
        # Add new content based on conversation type
        if conversation_type == "project_problem_solving":
            blocks.extend(self._build_project_content(analysis))
        elif conversation_type == "idea_brainstorming":
            blocks.extend(self._build_brainstorming_content(analysis))
        elif conversation_type == "learning_educational":
            blocks.extend(self._build_learning_content(analysis))
        elif conversation_type == "general_discussion":
            blocks.extend(self._build_general_content(analysis))
        
        return blocks
    
    def create_page(
        self,
        title: str,
        content_blocks: List[Dict[str, Any]],
        parent_page_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a new Notion page.
        
        Args:
            title: Page title
            content_blocks: List of Notion block objects for page content
            parent_page_id: Optional parent page ID. If None, creates at workspace root.
        
        Returns:
            Dictionary containing the created page data including URL
        
        Raises:
            Exception: If the API request fails
        """
        # Prepare parent location
        if parent_page_id:
            # Create as child of specific page
            parent = {"type": "page_id", "page_id": parent_page_id}
        else:
            # Create at workspace root (user's private pages)
            parent = {"type": "workspace", "workspace": True}
        
        # Prepare page data
        page_data = {
            "parent": parent,
            "properties": {
                "title": {
                    "title": [
                        {
                            "text": {
                                "content": title
                            }
                        }
                    ]
                }
            },
            "children": content_blocks,
        }
        
        # Make API request
        response = requests.post(
            f"{self.base_url}/pages",
            headers=self.headers,
            json=page_data,
        )
        
        if response.status_code != 200:
            error_data = response.json()
            raise Exception(
                f"Failed to create Notion page: {response.status_code} - "
                f"{error_data.get('message', 'Unknown error')}"
            )
        
        return response.json()
    
    def build_page_content(self, conversation_type: str, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Build Notion page content based on conversation type.
        
        Args:
            conversation_type: Type of conversation (project_problem_solving, idea_brainstorming, etc.)
            analysis: Structured analysis data
        
        Returns:
            List of Notion block objects
        """
        blocks = []
        
        # Add summary callout
        summary = analysis.get("summary", "")
        if summary:
            blocks.append(self.build_callout_block(summary, "📝"))
            blocks.append(self.build_paragraph_block(""))
        
        # Add topics
        topics = analysis.get("topics", [])
        if topics:
            topics_text = "Topics: " + ", ".join(topics)
            blocks.append(self.build_callout_block(topics_text, "🏷️"))
            blocks.append(self.build_paragraph_block(""))
        
        # Build content based on conversation type
        if conversation_type == "project_problem_solving":
            blocks.extend(self._build_project_content(analysis))
        elif conversation_type == "idea_brainstorming":
            blocks.extend(self._build_brainstorming_content(analysis))
        elif conversation_type == "learning_educational":
            blocks.extend(self._build_learning_content(analysis))
        elif conversation_type == "general_discussion":
            blocks.extend(self._build_general_content(analysis))
        else:
            # Fallback to general structure
            blocks.extend(self._build_general_content(analysis))
        
        return blocks
    
    def _build_project_content(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Build content for project/problem-solving conversations."""
        blocks = []
        
        # Key Insights
        key_insights = analysis.get("key_insights", [])
        if key_insights:
            blocks.append(self.build_heading_block("💡 Key Insights", 2))
            for insight in key_insights:
                blocks.append(self.build_bulleted_list_block(insight))
            blocks.append(self.build_paragraph_block(""))
        
        # Decisions Made
        decisions_made = analysis.get("decisions_made", [])
        if decisions_made:
            blocks.append(self.build_heading_block("✅ Decisions Made", 2))
            for decision in decisions_made:
                blocks.append(self.build_bulleted_list_block(decision))
            blocks.append(self.build_paragraph_block(""))
        
        # Action Items
        action_items = analysis.get("action_items", [])
        if action_items:
            blocks.append(self.build_heading_block("📋 Action Items", 2))
            for item in action_items:
                blocks.append(self.build_todo_block(item, checked=False))
            blocks.append(self.build_paragraph_block(""))
        
        return blocks
    
    def _build_brainstorming_content(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Build content for idea/brainstorming conversations."""
        blocks = []
        
        # Core Ideas
        core_ideas = analysis.get("core_ideas", [])
        if core_ideas:
            blocks.append(self.build_heading_block("💭 Core Ideas", 2))
            for idea in core_ideas:
                blocks.append(self.build_bulleted_list_block(idea))
            blocks.append(self.build_paragraph_block(""))
        
        # Interesting Points
        interesting_points = analysis.get("interesting_points", [])
        if interesting_points:
            blocks.append(self.build_heading_block("✨ Interesting Points", 2))
            for point in interesting_points:
                blocks.append(self.build_bulleted_list_block(point))
            blocks.append(self.build_paragraph_block(""))
        
        # Follow-up Questions
        follow_up_questions = analysis.get("follow_up_questions", [])
        if follow_up_questions:
            blocks.append(self.build_heading_block("🤔 Follow-up Questions", 2))
            for question in follow_up_questions:
                blocks.append(self.build_bulleted_list_block(question))
            blocks.append(self.build_paragraph_block(""))
        
        return blocks
    
    def _build_learning_content(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Build content for learning/educational conversations."""
        blocks = []
        
        # Key Concepts
        key_concepts = analysis.get("key_concepts", [])
        if key_concepts:
            blocks.append(self.build_heading_block("📚 Key Concepts", 2))
            for concept in key_concepts:
                blocks.append(self.build_bulleted_list_block(concept))
            blocks.append(self.build_paragraph_block(""))
        
        # Examples
        examples = analysis.get("examples", [])
        if examples:
            blocks.append(self.build_heading_block("💡 Examples", 2))
            for example in examples:
                blocks.append(self.build_bulleted_list_block(example))
            blocks.append(self.build_paragraph_block(""))
        
        # Takeaways
        takeaways = analysis.get("takeaways", [])
        if takeaways:
            blocks.append(self.build_heading_block("🎯 Key Takeaways", 2))
            for takeaway in takeaways:
                blocks.append(self.build_bulleted_list_block(takeaway))
            blocks.append(self.build_paragraph_block(""))
        
        return blocks
    
    def _build_general_content(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Build content for general discussions."""
        blocks = []
        
        # Main Points
        main_points = analysis.get("main_points", [])
        if main_points:
            blocks.append(self.build_heading_block("📌 Main Points", 2))
            for point in main_points:
                blocks.append(self.build_bulleted_list_block(point))
            blocks.append(self.build_paragraph_block(""))
        
        return blocks
    
    @staticmethod
    def build_heading_block(text: str, level: int = 2) -> Dict[str, Any]:
        """Build a heading block."""
        heading_type = f"heading_{level}"
        return {
            "object": "block",
            "type": heading_type,
            heading_type: {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {"content": text}
                    }
                ]
            }
        }
    
    @staticmethod
    def build_paragraph_block(text: str) -> Dict[str, Any]:
        """Build a paragraph block."""
        return {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {"content": text}
                    }
                ]
            }
        }
    
    @staticmethod
    def build_bulleted_list_block(text: str) -> Dict[str, Any]:
        """Build a bulleted list item block."""
        return {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {"content": text}
                    }
                ]
            }
        }
    
    @staticmethod
    def build_todo_block(text: str, checked: bool = False) -> Dict[str, Any]:
        """Build a to-do/checkbox block."""
        return {
            "object": "block",
            "type": "to_do",
            "to_do": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {"content": text}
                    }
                ],
                "checked": checked
            }
        }
    
    @staticmethod
    def build_divider_block() -> Dict[str, Any]:
        """Build a divider block."""
        return {
            "object": "block",
            "type": "divider",
            "divider": {}
        }
    
    @staticmethod
    def build_callout_block(text: str, emoji: str = "💡") -> Dict[str, Any]:
        """Build a callout block with an emoji icon."""
        return {
            "object": "block",
            "type": "callout",
            "callout": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {"content": text}
                    }
                ],
                "icon": {
                    "type": "emoji",
                    "emoji": emoji
                }
            }
        }