#!/usr/bin/env python3
"""
Main application entry point for the YouTube to Notion Database Integration.
Supports both example data mode and dynamic YouTube video processing with AI-generated summaries.
"""

import sys
from typing import Optional, Dict, Any
# Removed unused import: from notion_client import Client

# Legacy imports removed - using new architecture components
from .config.example_data import EXAMPLE_DATA
from .config import (
    ApplicationConfig,
    print_configuration_error
)
from .config.factory import ComponentFactory
from .processors.video_processor import VideoProcessor
from .utils.exceptions import (
    VideoProcessingError,
    MetadataExtractionError,
    SummaryGenerationError,
    StorageError,
    InvalidURLError,
    APIError,
    ConfigurationError,
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



def find_notion_database(storage, config: ApplicationConfig) -> Optional[str]:
    """
    Find the target Notion database for YouTube summaries using new architecture.
    
    Args:
        storage: NotionStorage instance
        config: Application configuration
        
    Returns:
        str: Database ID or None if not found
    """
    try:
        database_id = storage.find_target_location()
        if not database_id:
            print(f"Error: Could not find '{config.notion.database_name}' database")
            if config.notion.parent_page_name:
                print(f"in '{config.notion.parent_page_name}' page")
            print("\nPlease ensure:")
            if config.notion.parent_page_name:
                print(f"  1. You have a page named '{config.notion.parent_page_name}'")
                print(f"  2. That page contains a database named '{config.notion.database_name}'")
            else:
                print(f"  1. You have a database named '{config.notion.database_name}'")
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
        # Use new architecture components
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
        
    except InvalidURLError as e:
        print(f"Error: Invalid YouTube URL - {e}")
        if hasattr(e, 'details') and e.details:
            print(f"Details: {e.details}")
        print("\nTroubleshooting:")
        print("• Ensure the URL is from YouTube (youtube.com or youtu.be)")
        print("• Check that the video ID is 11 characters long")
        print("• Try copying the URL directly from your browser")
        return None
        
    except VideoUnavailableError as e:
        print(f"Error: Video is not available - {e}")
        if hasattr(e, 'details') and e.details:
            print(f"Details: {e.details}")
        print("\nTroubleshooting:")
        print("• The video may be private, deleted, or restricted")
        print("• Check if the video is available in your region")
        print("• Verify the video URL is correct")
        return None
        
    except QuotaExceededError as e:
        print(f"Error: API quota exceeded - {e}")
        if hasattr(e, 'api_name'):
            print(f"API: {e.api_name}")
        if hasattr(e, 'quota_type'):
            print(f"Quota type: {e.quota_type}")
        if hasattr(e, 'retry_delay_seconds') and e.retry_delay_seconds:
            print(f"Retry after: {e.retry_delay_seconds + 15} seconds")
        print("\nTroubleshooting:")
        print("• Wait before trying again (see retry delay above)")
        print("• Check your API usage limits in the respective console")
        print("• Consider upgrading your API plan if needed")
        return None
        
    except APIError as e:
        print(f"Error: API call failed - {e}")
        if hasattr(e, 'api_name'):
            print(f"API: {e.api_name}")
        if hasattr(e, 'status_code'):
            print(f"Status code: {e.status_code}")
        if hasattr(e, 'details') and e.details:
            print(f"Details: {e.details}")
        
        # Provide specific troubleshooting based on API and error type
        error_message = str(e).lower()
        print("\nTroubleshooting:")
        if 'authentication' in error_message or 'api key' in error_message:
            print("• Check that your API key is valid and properly configured")
            print("• Ensure the API key has the necessary permissions")
            print("• Verify the API key is not expired")
        elif 'network' in error_message or 'timeout' in error_message:
            print("• Check your internet connection")
            print("• Try again in a few moments")
            print("• Consider increasing timeout settings if available")
        else:
            print("• Verify your API configuration")
            print("• Check the API service status")
            print("• Try again in a few moments")
        return None
        
    except (SummaryGenerationError, MetadataExtractionError, StorageError) as e:
        error_type = type(e).__name__.replace('Error', '').lower()
        print(f"Error: {error_type.replace('_', ' ').title()} failed - {e}")
        if hasattr(e, 'details') and e.details:
            print(f"Details: {e.details}")
        print("\nTroubleshooting:")
        print("• Check your configuration settings")
        print("• Verify all required API keys are set")
        print("• Try again in a few moments")
        return None
        
    except ConfigurationError as e:
        print(f"Error: Configuration error - {e}")
        if hasattr(e, 'details') and e.details:
            print(f"Details: {e.details}")
        print("\nTroubleshooting:")
        print("• Check your environment variables (.env file)")
        print("• Ensure all required configuration is provided")
        print("• Verify configuration values are valid")
        return None
        
    except Exception as e:
        print(f"Error: Unexpected error during YouTube processing - {e}")
        print(f"Error type: {type(e).__name__}")
        print("\nTroubleshooting:")
        print("• Check your configuration and try again")
        print("• Ensure all dependencies are properly installed")
        print("• If the problem persists, please report this issue")
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


def add_to_notion_database(storage, video_data: Dict[str, Any]) -> bool:
    """
    Add processed video data to the Notion database using new architecture.
    
    Args:
        storage: NotionStorage instance
        video_data: Processed video data
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        success = storage.store_video_summary(video_data)
        
        if success:
            print(f"✓ Entry added successfully to Notion database")
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
    
    # Step 2: Initialize storage backend
    if not batch_mode:
        print("\n2. Initializing storage backend...")
    try:
        factory = ComponentFactory(config)
        storage = factory.create_storage()
        storage.validate_configuration()
    except Exception as e:
        print(f"Error: Failed to initialize storage backend: {e}")
        return False
    if not batch_mode:
        print("✓ Storage backend initialized")
    
    # Step 3: Find target database
    if not batch_mode:
        print("\n3. Finding target database...")
    database_id = find_notion_database(storage, config)
    if not database_id:
        return False
    if not batch_mode:
        print("✓ Found target database")
    
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
    success = add_to_notion_database(storage, video_data)
    
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