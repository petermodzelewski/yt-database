#!/usr/bin/env python3
"""
Main application entry point for the Notion client project.
Adds YouTube video summaries to Notion database using EXAMPLE_DATA.
"""

import os
from dotenv import load_dotenv
from notion_client import Client
from data import EXAMPLE_DATA
from markdown_converter import markdown_to_notion_blocks

# Load environment variables from .env file
load_dotenv()

def find_database_by_name(notion, database_name, parent_page_name=None):
    """Find database by name, optionally within a specific parent page."""
    try:
        # Search for databases
        databases = notion.search(filter={"property": "object", "value": "database"})
        
        for db in databases['results']:
            db_title = db['title'][0]['plain_text'] if db['title'] else ''
            
            if db_title == database_name:
                if parent_page_name:
                    # Check if database is in the correct parent page
                    parent = notion.pages.retrieve(db['parent']['page_id'])
                    parent_title = parent['properties']['title']['title'][0]['plain_text'] if parent['properties'].get('title') else ''
                    
                    if parent_title == parent_page_name:
                        return db['id']
                else:
                    return db['id']
        
        return None
    except Exception as e:
        print(f"Error finding database: {e}")
        return None

def add_youtube_entry(notion, database_id, title, summary, video_url, channel, cover_url):
    """Add a new entry to the YT Summaries database."""
    try:

        # Convert markdown summary to Notion blocks
        summary_blocks = markdown_to_notion_blocks(summary)
        
        # Create the page properties
        properties = {
            "Title": {
                "title": [
                    {
                        "type": "text",
                        "text": {"content": title}
                    }
                ]
            },
            "Video URL": {
                "url": video_url
            },
            "Channel": {
                "rich_text": [
                    {
                        "type": "text", 
                        "text": {"content": channel}
                    }
                ]
            },
            "Summary": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {"content": summary[:2000]}  # Notion has a 2000 char limit for rich_text properties
                    }
                ]
            }
        }
        
        # Create the page with summary blocks as content
        page = notion.pages.create(
            parent={"database_id": database_id},
            properties=properties,
            children=summary_blocks,
            cover={"type": "external", "external": {"url": cover_url}} if cover_url else None
        )
        
        print(f"Successfully added entry: {title}")
        return page['id']
        
    except Exception as e:
        print(f"Error adding entry to database: {e}")
        return None

def main():
    """Main function to add YouTube summary to Notion database using EXAMPLE_DATA."""
    # Initialize Notion client
    notion_token = os.getenv("NOTION_TOKEN")
    
    if not notion_token:
        print("Error: NOTION_TOKEN environment variable not set")
        return
    
    notion = Client(auth=notion_token)
    
    # Find the YT Summaries database
    database_id = find_database_by_name(notion, "YT Summaries", "YouTube Knowledge Base")
    
    if not database_id:
        print("Error: Could not find 'YT Summaries' database in 'YouTube Knowledge Base' page")
        return
    
    # Use example data
    video_url = EXAMPLE_DATA["Video URL"]
    cover_url = EXAMPLE_DATA["Cover"]
    channel = EXAMPLE_DATA["Channel"] 
    title = EXAMPLE_DATA["Title"]
    summary = EXAMPLE_DATA["Summary"]
    
    # Add the entry
    page_id = add_youtube_entry(notion, database_id, title, summary, video_url, channel, cover_url)
    
    if page_id:
        print(f"Entry added successfully with ID: {page_id}")
    else:
        print("Failed to add entry")

if __name__ == "__main__":
    main()