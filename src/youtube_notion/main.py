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
    
    # Step 2: Process data
    if not batch_mode:
        print("\n2. Processing data...")
    
    success = False
    if youtube_mode:
        # YouTube URL processing mode
        success = process_video_with_orchestrator(youtube_url, custom_prompt, config, batch_mode)
    else:
        # Example data mode
        if not batch_mode:
            print("Using example data from config")

        try:
            # Initialize storage and add example data
            factory = ComponentFactory(config)
            storage = factory.create_storage()
            storage.validate_configuration()

            video_data = {
                "Title": EXAMPLE_DATA["Title"],
                "Video URL": EXAMPLE_DATA["Video URL"],
                "Channel": EXAMPLE_DATA["Channel"],
                "Cover": EXAMPLE_DATA["Cover"],
                "Summary": EXAMPLE_DATA["Summary"]
            }
            if not batch_mode:
                print(f"✓ Loaded example data: {video_data['Title']}")
                print("\n3. Adding entry to Notion database...")

            success = add_to_notion_database(storage, video_data)

        except (ConfigurationError, StorageError) as e:
            print(f"Error: {e}")
            if hasattr(e, 'details') and e.details:
                print(f"Details: {e.details}")
            success = False
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            success = False

    if success:
        if not batch_mode:
            print("\n" + "=" * 60)
            print("SUCCESS: Operation completed!")
            print("=" * 60)
        else:
            print(f"✓ Operation successful")
        return True
    else:
        if not batch_mode:
            print("\n" + "=" * 60)
            print("FAILED: Operation did not complete successfully")
            print("=" * 60)
        else:
            print(f"✗ Operation failed")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)