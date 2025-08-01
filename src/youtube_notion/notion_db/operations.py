"""
Notion database operations.
"""

from ..utils.markdown_converter import markdown_to_notion_blocks, enrich_timestamps_with_links


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
    """Add a new entry to the YT Summaries database.
    
    Creates a page with:
    1. YouTube video embedded at the top
    2. A divider for visual separation
    3. The summary with timestamps converted to clickable YouTube links
    4. All content converted from markdown to formatted Notion blocks
    
    Timestamps like [8:05] or [8:05-8:24] become clickable links that jump to that time in the video.
    """
    try:
        # Enrich timestamps in summary with YouTube links
        enriched_summary = enrich_timestamps_with_links(summary, video_url)
        
        # Convert enriched markdown summary to Notion blocks
        summary_blocks = markdown_to_notion_blocks(enriched_summary)
        
        # Create YouTube embed block
        youtube_embed = {
            "object": "block",
            "type": "embed",
            "embed": {
                "url": video_url
            }
        }
        
        # Add a divider after the video for better visual separation
        divider = {
            "object": "block",
            "type": "divider",
            "divider": {}
        }
        
        # Combine embed, divider, and summary blocks
        all_blocks = [youtube_embed, divider] + summary_blocks
        
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
            }
        }
        
        # Create the page with YouTube embed and summary blocks as content
        page = notion.pages.create(
            parent={"database_id": database_id},
            properties=properties,
            children=all_blocks,
            cover={"type": "external", "external": {"url": cover_url}} if cover_url else None
        )
        
        print(f"Successfully added entry: {title}")
        return page['id']
        
    except Exception as e:
        print(f"Error adding entry to database: {e}")
        return None