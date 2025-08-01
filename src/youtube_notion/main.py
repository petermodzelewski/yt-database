#!/usr/bin/env python3
"""
Main application entry point for the YouTube to Notion Database Integration.
Adds YouTube video summaries to Notion database using EXAMPLE_DATA.
"""

import os
from dotenv import load_dotenv
from notion_client import Client

from .notion_db.operations import find_database_by_name, add_youtube_entry
from .config.example_data import EXAMPLE_DATA

# Load environment variables from .env file
load_dotenv()


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