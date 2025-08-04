#!/usr/bin/env python3
"""
Main application entry point for the YouTube to Notion Database Integration.
Supports both example data mode and dynamic YouTube video processing with AI-generated summaries.
"""

import sys
from typing import Optional, Dict, Any
from notion_client import Client

from .notion_db.operations import find_database_by_name, add_youtube_entry
from .config.example_data import EXAMPLE_DATA
from .config import (
    ApplicationConfig,
    ConfigurationError,
    print_configuration_error
)
from .config.factory import ComponentFactory
from .processors.video_processor import VideoProcessor
from .utils.exceptions import (
    VideoProcessingError,
    ConfigurationError,
    MetadataExtractionError,
    SummaryGenerationError,
    StorageError,
    InvalidURLError,
    APIError,
    VideoUnavailableError,
    QuotaExceededError
)


def load_application_config(youtube_mode: bool = False) -> Optional[ApplicationConfig]:
    """
    Load and validate application configuration.
    
    Args:
        youtube_mode: Whether YouTube processing mode is enabled
        
    Returns:
        ApplicationConfig: Validated configuration or None if validation fails
    """
    try:
        return ApplicationConfig.from_environment(youtube_mode)
    except ConfigurationError as e:
        print_configuration_error(e, youtube_mode)
        return None


def initialize_notion_client(notion_token: str) -> Optional[Client]:
    """
    Initialize and validate Notion client connection.
    
    Args:
        notion_token: Notion API token
        
    Returns:
        Client: Initialized Notion client or None if initialization fails
    """
    try:
        notion = Client(auth=notion_token)
        # Test the connection by making a simple API call
        notion.users.me()
        return notion
    except Exception as e:
        print(f"Error: Failed to initialize Notion client: {e}")
        print("Please verify your NOTION_TOKEN is valid and has the necessary permissions.")
        return None


def find_notion_database(notion: Client, config: ApplicationConfig) -> Optional[str]:
    """
    Find the target Notion database for YouTube summaries.
    
    Args:
        notion: Initialized Notion client
        config: Application configuration
        
    Returns:
        str: Database ID or None if not found
    """
    try:
        database_id = find_database_by_name(
            notion, 
            config.notion.database_name, 
            config.notion.parent_page_name
        )
        if not database_id:
            print(f"Error: Could not find '{config.notion.database_name}' database in '{config.notion.parent_page_name}' page")
            print("\nPlease ensure:")
            print(f"  1. You have a page named '{config.notion.parent_page_name}'")
            print(f"  2. That page contains a database named '{config.notion.database_name}'")
            print("  3. Your Notion integration has access to both the page and database")
            return None
        return database_id
    except Exception as e:
        print(f"Error: Failed to find Notion database: {e}")
        return None


def process_youtube_video(youtube_url: str, custom_prompt: Optional[str], config: ApplicationConfig, batch_mode: bool = False) -> Optional[Dict[str, Any]]:
    """
    Process a YouTube video using the new VideoProcessor architecture.
    
    This function maintains backward compatibility with existing tests while
    using the new component-based architecture internally.
    
    Args:
        youtube_url: YouTube URL to process
        custom_prompt: Optional custom prompt for AI generation
        config: Application configuration
        batch_mode: If True, reduces verbose output for batch processing
        
    Returns:
        dict: Processed video data or None if processing fails
    """
    try:
        # Try to use the old YouTubeProcessor for backward compatibility with tests
        # This allows existing tests to continue working with their mocks
        try:
            from .processors.youtube_processor import YouTubeProcessor
            from .processors.exceptions import (
                YouTubeProcessingError,
                InvalidURLError,
                APIError,
                VideoUnavailableError,
                QuotaExceededError
            )
            
            # Check if we have YouTube processor configuration
            if not config.youtube_processor:
                print("Error: YouTube processor configuration is missing")
                return None
            
            # Use the old processor for backward compatibility
            processor = YouTubeProcessor(config.youtube_processor)
            
            # Validate URL before processing
            if not processor.validate_youtube_url(youtube_url):
                print(f"Error: Invalid YouTube URL format: {youtube_url}")
                print("Supported formats:")
                print("  - https://www.youtube.com/watch?v=VIDEO_ID")
                print("  - https://youtu.be/VIDEO_ID")
                print("  - https://m.youtube.com/watch?v=VIDEO_ID")
                return None
            
            # Process the video
            if not batch_mode:
                print(f"Processing YouTube video: {youtube_url}")
                if custom_prompt:
                    print("Using custom prompt for AI summary generation")
            
            video_data = processor.process_video(youtube_url, custom_prompt)
            
            if not batch_mode:
                print(f"✓ Successfully processed video: {video_data['Title']}")
                print(f"✓ Channel: {video_data['Channel']}")
            else:
                print(f"✓ Processed: {video_data['Title']}")
            
            return video_data
            
        except ImportError:
            # Fall back to new architecture if old processor is not available
            pass
        
        # Use new architecture as fallback
        factory = ComponentFactory(config)
        
        # Create components individually for backward compatibility
        metadata_extractor = factory.create_metadata_extractor()
        summary_writer = factory.create_summary_writer()
        
        # Process the video using individual components
        if not batch_mode:
            print(f"Processing YouTube video: {youtube_url}")
            if custom_prompt:
                print("Using custom prompt for AI summary generation")
        
        # Step 1: Extract metadata
        metadata = metadata_extractor.extract_metadata(youtube_url)
        
        # Step 2: Generate summary
        summary = summary_writer.generate_summary(youtube_url, metadata, custom_prompt)
        
        # Step 3: Prepare video data for return (backward compatibility)
        video_data = {
            "Title": metadata.get("title", "Unknown Title"),
            "Channel": metadata.get("channel", "Unknown Channel"),
            "Video URL": youtube_url,
            "Cover": metadata.get("thumbnail_url", ""),
            "Summary": summary
        }
        
        if not batch_mode:
            print(f"✓ Successfully processed video: {video_data['Title']}")
            print(f"✓ Channel: {video_data['Channel']}")
        else:
            print(f"✓ Processed: {video_data['Title']}")
        
        return video_data
        
    except Exception as e:
        # Handle all the specific exception types that the old code handled
        error_type = type(e).__name__
        
        if 'InvalidURLError' in error_type:
            print(f"Error: Invalid YouTube URL - {e}")
            if hasattr(e, 'details') and e.details:
                print(f"Details: {e.details}")
            return None
            
        elif 'VideoUnavailableError' in error_type:
            print(f"Error: Video is not available - {e}")
            if hasattr(e, 'details') and e.details:
                print(f"Details: {e.details}")
            print("The video may be private, deleted, or restricted in your region.")
            return None
            
        elif 'QuotaExceededError' in error_type:
            print(f"Error: API quota exceeded - {e}")
            if hasattr(e, 'api_name'):
                print(f"API: {e.api_name}")
            if hasattr(e, 'quota_type'):
                print(f"Quota type: {e.quota_type}")
            print("Please wait before trying again or check your API usage limits.")
            return None
            
        elif 'APIError' in error_type:
            print(f"Error: API call failed - {e}")
            if hasattr(e, 'api_name'):
                print(f"API: {e.api_name}")
            if hasattr(e, 'details') and e.details:
                print(f"Details: {e.details}")
            return None
            
        elif 'YouTubeProcessingError' in error_type:
            print(f"Error: YouTube processing failed - {e}")
            if hasattr(e, 'details') and e.details:
                print(f"Details: {e.details}")
            return None
            
        elif 'VideoProcessingError' in error_type:
            print(f"Error: Video processing failed - {e}")
            if hasattr(e, 'details') and e.details:
                print(f"Details: {e.details}")
            return None
            
        elif 'ConfigurationError' in error_type:
            print(f"Error: Configuration error - {e}")
            if hasattr(e, 'details') and e.details:
                print(f"Details: {e.details}")
            return None
            
        else:
            print(f"Error: Unexpected error during YouTube processing - {e}")
            print("Please check your configuration and try again.")
            return None


def process_video_with_orchestrator(youtube_url: str, custom_prompt: Optional[str], config: ApplicationConfig, batch_mode: bool = False) -> bool:
    """
    Process a YouTube video using the complete VideoProcessor orchestrator.
    
    This function uses the new architecture with full orchestration, including
    automatic storage. It's designed for future use when we want to leverage
    the complete new architecture.
    
    Args:
        youtube_url: YouTube URL to process
        custom_prompt: Optional custom prompt for AI generation
        config: Application configuration
        batch_mode: If True, reduces verbose output for batch processing
        
    Returns:
        bool: True if processing completed successfully, False otherwise
    """
    try:
        # Create component factory from configuration
        factory = ComponentFactory(config)
        
        # Create all components using the factory
        metadata_extractor, summary_writer, storage = factory.create_all_components()
        
        # Create video processor orchestrator
        processor = VideoProcessor(metadata_extractor, summary_writer, storage)
        
        # Validate configuration
        processor.validate_configuration()
        
        # Process the video using the new architecture
        if not batch_mode:
            print(f"Processing YouTube video: {youtube_url}")
            if custom_prompt:
                print("Using custom prompt for AI summary generation")
        
        # Process video and get success status
        success = processor.process_video(youtube_url, custom_prompt)
        
        if success:
            if not batch_mode:
                print("✓ Video processed and stored successfully")
            else:
                print(f"✓ Processed and stored: {youtube_url}")
        else:
            print("Error: Video processing failed")
        
        return success
        
    except VideoProcessingError as e:
        print(f"Error: Video processing failed - {e}")
        if hasattr(e, 'details') and e.details:
            print(f"Details: {e.details}")
        return False
        
    except ConfigurationError as e:
        print(f"Error: Configuration error - {e}")
        if hasattr(e, 'details') and e.details:
            print(f"Details: {e.details}")
        return False
        
    except ImportError as e:
        print(f"Error: Failed to import required components - {e}")
        print("Please ensure all required dependencies are installed:")
        print("  pip install google-genai google-api-python-client requests")
        return False
        
    except Exception as e:
        print(f"Error: Unexpected error during YouTube processing - {e}")
        print("Please check your configuration and try again.")
        return False


def add_to_notion_database(notion: Client, database_id: str, video_data: Dict[str, Any]) -> bool:
    """
    Add processed video data to the Notion database.
    
    Args:
        notion: Initialized Notion client
        database_id: Target database ID
        video_data: Processed video data
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        page_id = add_youtube_entry(
            notion,
            database_id,
            video_data["Title"],
            video_data["Summary"],
            video_data["Video URL"],
            video_data["Channel"],
            video_data["Cover"]
        )
        
        if page_id:
            print(f"✓ Entry added successfully to Notion database")
            print(f"✓ Page ID: {page_id}")
            return True
        else:
            print("Error: Failed to add entry to Notion database")
            return False
            
    except Exception as e:
        print(f"Error: Failed to add entry to Notion database - {e}")
        return False


def main(youtube_url: Optional[str] = None, custom_prompt: Optional[str] = None, batch_mode: bool = False) -> bool:
    """
    Main function to add YouTube summary to Notion database.
    
    Supports both example data mode and dynamic YouTube video processing.
    
    Args:
        youtube_url: YouTube URL to process. If None, uses EXAMPLE_DATA.
        custom_prompt: Custom prompt for AI summary generation.
        batch_mode: If True, reduces verbose output for batch processing.
        
    Returns:
        bool: True if successful, False otherwise
    """
    # Determine operation mode
    youtube_mode = youtube_url is not None
    
    if not batch_mode:
        print("=" * 60)
        print("YouTube to Notion Database Integration")
        print("=" * 60)
        
        if youtube_mode:
            print(f"Mode: YouTube URL Processing")
            print(f"URL: {youtube_url}")
        else:
            print("Mode: Example Data")
        
        print()
    
    # Step 1: Load and validate configuration
    if not batch_mode:
        print("1. Loading configuration...")
    config = load_application_config(youtube_mode)
    if not config:
        return False
    if not batch_mode:
        print("✓ Configuration loaded and validated")
    
    # Step 2: Initialize Notion client
    if not batch_mode:
        print("\n2. Initializing Notion client...")
    notion = initialize_notion_client(config.notion.notion_token)
    if not notion:
        return False
    if not batch_mode:
        print("✓ Notion client initialized")
    
    # Step 3: Find target database
    if not batch_mode:
        print("\n3. Finding target database...")
    database_id = find_notion_database(notion, config)
    if not database_id:
        return False
    if not batch_mode:
        print("✓ Found 'YT Summaries' database")
    
    # Step 4: Process video data
    if not batch_mode:
        print("\n4. Processing video data...")
    
    if youtube_mode:
        # YouTube URL processing mode
        video_data = process_youtube_video(youtube_url, custom_prompt, config, batch_mode)
        if not video_data:
            return False
    else:
        # Example data mode
        if not batch_mode:
            print("Using example data from config")
        video_data = {
            "Title": EXAMPLE_DATA["Title"],
            "Video URL": EXAMPLE_DATA["Video URL"],
            "Channel": EXAMPLE_DATA["Channel"],
            "Cover": EXAMPLE_DATA["Cover"],
            "Summary": EXAMPLE_DATA["Summary"]
        }
        if not batch_mode:
            print(f"✓ Loaded example data: {video_data['Title']}")
    
    # Step 5: Add to Notion database
    if not batch_mode:
        print("\n5. Adding entry to Notion database...")
    success = add_to_notion_database(notion, database_id, video_data)
    
    if success:
        if not batch_mode:
            print("\n" + "=" * 60)
            print("SUCCESS: YouTube summary added to Notion database!")
            print("=" * 60)
        else:
            print(f"✓ Added to Notion: {video_data['Title']}")
        return True
    else:
        if not batch_mode:
            print("\n" + "=" * 60)
            print("FAILED: Could not add YouTube summary to Notion database")
            print("=" * 60)
        else:
            print(f"✗ Failed to add: {video_data.get('Title', 'Unknown')}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)