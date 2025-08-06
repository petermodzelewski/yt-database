"""
Essential end-to-end integration tests for the YouTube-to-Notion system.

This module contains only the essential integration tests:
- One end-to-end happy path test
- One happy path test per subsystem (metadata, summary, storage)

These tests use real APIs and the test database configured in .env-test.
"""

import pytest
from typing import Dict, Any

from src.youtube_notion.config.factory import ComponentFactory
from src.youtube_notion.processors.video_processor import VideoProcessor
from src.youtube_notion.utils.exceptions import (
    VideoProcessingError,
    ConfigurationError,
    MetadataExtractionError,
    SummaryGenerationError,
    StorageError
)


@pytest.mark.integration
class TestEndToEndIntegration:
    """Essential end-to-end integration test using real APIs and test database."""
    
    def test_complete_video_processing_pipeline(self, skip_if_no_api_keys, clean_test_database, integration_config):
        """Test the complete video processing pipeline from URL to Notion storage."""
        # Use a well-known, stable YouTube video for testing
        test_video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        
        # Create components using factory from environment (.env-test is already loaded)
        factory = ComponentFactory.from_environment(youtube_mode=True)
        
        metadata_extractor = factory.create_metadata_extractor()
        summary_writer = factory.create_summary_writer()
        storage = factory.create_storage()
        
        # Create video processor
        processor = VideoProcessor(
            metadata_extractor=metadata_extractor,
            summary_writer=summary_writer,
            storage=storage
        )
        
        # Validate configuration
        assert processor.validate_configuration(), "Configuration validation should pass"
        
        # Process the video
        result = processor.process_video(test_video_url)
        
        # Verify processing succeeded
        assert result is True, "Video processing should succeed"
        
        # Verify data was stored in Notion
        # Query the test database to confirm the entry was created
        database_id = clean_test_database['database_id']
        notion_client = storage.client
        
        response = notion_client.databases.query(database_id=database_id)
        pages = response.get("results", [])
        
        assert len(pages) > 0, "At least one page should be created in the test database"
        
        # Verify the created page has correct properties
        page = pages[0]
        properties = page.get("properties", {})
        
        # Check that all required properties exist
        assert "Title" in properties, "Page should have Title property"
        assert "Channel" in properties, "Page should have Channel property"
        assert "Video URL" in properties, "Page should have Video URL property"
        
        # Check that the page has content (summary is stored as page body, not property)
        page_id = page["id"]
        blocks_response = notion_client.blocks.children.list(block_id=page_id)
        blocks = blocks_response.get("results", [])
        
        assert len(blocks) > 0, "Page should have content blocks"
        
        # Verify the structure: YouTube embed, divider, and summary content
        block_types = [block.get("type") for block in blocks]
        assert "embed" in block_types, "Page should contain YouTube embed"
        assert "divider" in block_types, "Page should contain divider"
        
        # Verify URL matches
        video_url_prop = properties.get("Video URL", {})
        if video_url_prop.get("url"):
            assert video_url_prop["url"] == test_video_url, "Stored URL should match input URL"


@pytest.mark.integration
class TestSubsystemIntegration:
    """Test individual subsystem integrations with real APIs - happy path only."""
    
    def test_metadata_extractor_integration(self, integration_config):
        """Test metadata extractor subsystem happy path with real YouTube API."""
        factory = ComponentFactory.from_environment(youtube_mode=True)
        extractor = factory.create_metadata_extractor()
        
        test_video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        
        # Extract metadata
        metadata = extractor.extract_metadata(test_video_url)
        
        # Verify metadata structure and content
        assert isinstance(metadata, dict)
        assert "title" in metadata
        assert "channel" in metadata
        assert "thumbnail_url" in metadata
        assert "video_id" in metadata
        
        # Verify content quality
        assert len(metadata["title"]) > 0
        assert len(metadata["channel"]) > 0
        assert metadata["video_id"] == "dQw4w9WgXcQ"
    
    def test_summary_writer_integration(self, integration_config):
        """Test Gemini AI subsystem happy path with real Gemini API."""
        factory = ComponentFactory.from_environment(youtube_mode=True)
        writer = factory.create_summary_writer()
        
        test_video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        test_metadata = {
            "title": "Test Video Title",
            "description": "Test video description with some content to summarize",
            "channel": "Test Channel"
        }
        
        # Generate summary
        summary = writer.generate_summary(test_video_url, test_metadata)
        assert isinstance(summary, str)
        assert len(summary) > 0
        
        # Verify summary contains markdown formatting (basic quality check)
        assert "#" in summary or "**" in summary or "*" in summary, "Summary should contain markdown formatting"
    
    def test_notion_storage_integration(self, clean_test_database, integration_config):
        """Test Notion storage subsystem happy path with real Notion API."""
        factory = ComponentFactory.from_environment(youtube_mode=True)
        storage = factory.create_storage()
        
        # Test data
        test_data = {
            "Title": "Integration Test Video",
            "Channel": "Test Channel",
            "Video URL": "https://www.youtube.com/watch?v=test123",
            "Cover": "https://img.youtube.com/vi/test123/maxresdefault.jpg",
            "Summary": "# Test Summary\n\nThis is a test summary with [1:23] timestamp."
        }
        
        # Store data
        result = storage.store_video_summary(test_data)
        assert result is True, "Data should be stored successfully"
        
        # Verify data was stored
        database_id = clean_test_database['database_id']
        notion_client = storage.client
        
        response = notion_client.databases.query(database_id=database_id)
        pages = response.get("results", [])
        
        assert len(pages) > 0, "At least one page should be created"
        
        # Verify page properties
        page = pages[0]
        properties = page.get("properties", {})
        
        assert "Title" in properties
        assert "Channel" in properties
        assert "Video URL" in properties