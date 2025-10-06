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