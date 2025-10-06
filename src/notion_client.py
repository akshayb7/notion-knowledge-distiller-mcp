"""
Notion API client for creating structured knowledge pages.
"""

import requests
from typing import Optional, Dict, Any, List


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