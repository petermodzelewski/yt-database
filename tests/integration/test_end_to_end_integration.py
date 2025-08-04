"""
End-to-end integration tests for the YouTube-to-Notion system.

This module contains comprehensive integration tests that verify the complete
processing pipeline works correctly with real APIs and test databases.

These tests:
- Use the .env-test configuration exclusively
- Create and clean up test database entries
- Verify complete end-to-end functionality
- Test error scenarios with real APIs
- Ensure components work together correctly
"""

import pytest
import os
import time
from typing import Dict, Any

from youtube_notion.config.factory import ComponentFactory
from youtube_notion.processors.video_processor import VideoProcessor
from youtube_notion.extractors.video_metadata_extractor import VideoMetadataExtractor
from youtube_notion.writers.gemini_summary_writer import GeminiSummaryWriter
from youtube_notion.storage.notion_storage import NotionStorage
from youtube_notion.utils.exceptions import (
    VideoProcessingError,
    ConfigurationError,
    MetadataExtractionError,
    SummaryGenerationError,
    StorageError
)


@pytest.mark.integration
class TestEndToEndIntegration:
    """End-to-end integration tests using real APIs and test database."""
    
    def test_complete_video_processing_pipeline(self, skip_if_no_api_keys, clean_test_database, integration_config):
        """Test the complete video processing pipeline from URL to Notion storage."""
        # Use a well-known, stable YouTube video for testing
        test_video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        
        # Create components using factory
        factory = ComponentFactory()
        
        metadata_extractor = factory.create_metadata_extractor(
            youtube_api_key=integration_config.get('youtube_api_key')
        )
        
        summary_writer = factory.create_summary_writer(
            api_key=integration_config['gemini_api_key']
        )
        
        storage = factory.create_storage(
            notion_token=integration_config['notion_token'],
            database_name=integration_config['database_name'],
            parent_page_name=integration_config['parent_page_name']
        )
        
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
        notion_client = storage.notion_client
        
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
        assert "Summary" in properties, "Page should have Summary property"
        
        # Verify URL matches
        video_url_prop = properties.get("Video URL", {})
        if video_url_prop.get("url"):
            assert video_url_prop["url"] == test_video_url, "Stored URL should match input URL"
    
    def test_video_processing_with_custom_prompt(self, skip_if_no_api_keys, clean_test_database, integration_config):
        """Test video processing with a custom prompt."""
        test_video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        custom_prompt = "Create a brief summary focusing only on the main theme. Include exactly 2 timestamps."
        
        # Create components
        factory = ComponentFactory()
        
        metadata_extractor = factory.create_metadata_extractor(
            youtube_api_key=integration_config.get('youtube_api_key')
        )
        
        summary_writer = factory.create_summary_writer(
            api_key=integration_config['gemini_api_key']
        )
        
        storage = factory.create_storage(
            notion_token=integration_config['notion_token'],
            database_name=integration_config['database_name'],
            parent_page_name=integration_config['parent_page_name']
        )
        
        processor = VideoProcessor(
            metadata_extractor=metadata_extractor,
            summary_writer=summary_writer,
            storage=storage
        )
        
        # Process with custom prompt
        result = processor.process_video(test_video_url, custom_prompt=custom_prompt)
        
        assert result is True, "Video processing with custom prompt should succeed"
        
        # Verify data was stored
        database_id = clean_test_database['database_id']
        notion_client = storage.notion_client
        
        response = notion_client.databases.query(database_id=database_id)
        pages = response.get("results", [])
        
        assert len(pages) > 0, "Page should be created with custom prompt"
    
    def test_component_validation(self, integration_config):
        """Test that all components validate their configuration correctly."""
        factory = ComponentFactory()
        
        # Test metadata extractor validation
        metadata_extractor = factory.create_metadata_extractor(
            youtube_api_key=integration_config.get('youtube_api_key')
        )
        assert metadata_extractor.validate_configuration() is True
        
        # Test summary writer validation
        if integration_config['gemini_api_key']:
            summary_writer = factory.create_summary_writer(
                api_key=integration_config['gemini_api_key']
            )
            assert summary_writer.validate_configuration() is True
        
        # Test storage validation
        if integration_config['notion_token']:
            storage = factory.create_storage(
                notion_token=integration_config['notion_token'],
                database_name=integration_config['database_name'],
                parent_page_name=integration_config['parent_page_name']
            )
            assert storage.validate_configuration() is True
    
    def test_invalid_configuration_handling(self):
        """Test handling of invalid configuration."""
        factory = ComponentFactory()
        
        # Test invalid Gemini API key
        with pytest.raises(ConfigurationError):
            summary_writer = factory.create_summary_writer(api_key="invalid_key")
            summary_writer.validate_configuration()
        
        # Test invalid Notion token
        with pytest.raises(ConfigurationError):
            storage = factory.create_storage(
                notion_token="invalid_token",
                database_name="Test DB",
                parent_page_name="Test Page"
            )
            storage.validate_configuration()
    
    def test_invalid_video_url_handling(self, skip_if_no_api_keys, integration_config):
        """Test handling of invalid video URLs."""
        factory = ComponentFactory()
        
        metadata_extractor = factory.create_metadata_extractor(
            youtube_api_key=integration_config.get('youtube_api_key')
        )
        
        summary_writer = factory.create_summary_writer(
            api_key=integration_config['gemini_api_key']
        )
        
        storage = factory.create_storage(
            notion_token=integration_config['notion_token'],
            database_name=integration_config['database_name'],
            parent_page_name=integration_config['parent_page_name']
        )
        
        processor = VideoProcessor(
            metadata_extractor=metadata_extractor,
            summary_writer=summary_writer,
            storage=storage
        )
        
        # Test with invalid URL
        invalid_url = "https://www.youtube.com/watch?v=invalidvideo123"
        
        with pytest.raises((MetadataExtractionError, VideoProcessingError)):
            processor.process_video(invalid_url)
    
    def test_metadata_extraction_fallback(self, skip_if_no_api_keys, integration_config):
        """Test metadata extraction fallback from API to web scraping."""
        factory = ComponentFactory()
        
        # Create extractor without YouTube API key to force web scraping
        metadata_extractor = factory.create_metadata_extractor(youtube_api_key=None)
        
        test_video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        
        # Extract metadata using web scraping
        metadata = metadata_extractor.extract_metadata(test_video_url)
        
        # Verify metadata structure
        assert isinstance(metadata, dict)
        assert "title" in metadata
        assert "channel" in metadata
        assert "thumbnail_url" in metadata
        assert len(metadata["title"]) > 0
        assert len(metadata["channel"]) > 0
    
    @pytest.mark.slow
    def test_processing_performance(self, skip_if_no_api_keys, clean_test_database, integration_config):
        """Test processing performance with real APIs."""
        test_video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        
        factory = ComponentFactory()
        
        metadata_extractor = factory.create_metadata_extractor(
            youtube_api_key=integration_config.get('youtube_api_key')
        )
        
        summary_writer = factory.create_summary_writer(
            api_key=integration_config['gemini_api_key']
        )
        
        storage = factory.create_storage(
            notion_token=integration_config['notion_token'],
            database_name=integration_config['database_name'],
            parent_page_name=integration_config['parent_page_name']
        )
        
        processor = VideoProcessor(
            metadata_extractor=metadata_extractor,
            summary_writer=summary_writer,
            storage=storage
        )
        
        # Measure processing time
        start_time = time.time()
        result = processor.process_video(test_video_url)
        processing_time = time.time() - start_time
        
        assert result is True, "Processing should succeed"
        assert processing_time < 180, f"Processing took {processing_time:.2f}s, expected < 180s"
    
    def test_database_cleanup_isolation(self, clean_test_database, integration_config):
        """Test that database cleanup works and tests are isolated."""
        database_id = clean_test_database['database_id']
        
        # Create a test storage instance
        factory = ComponentFactory()
        storage = factory.create_storage(
            notion_token=integration_config['notion_token'],
            database_name=integration_config['database_name'],
            parent_page_name=integration_config['parent_page_name']
        )
        
        # Verify database is empty at start
        notion_client = storage.notion_client
        response = notion_client.databases.query(database_id=database_id)
        initial_pages = response.get("results", [])
        
        # Should be empty due to cleanup
        assert len(initial_pages) == 0, "Database should be clean at test start"
        
        # Create a test entry
        test_data = {
            "Title": "Test Entry",
            "Channel": "Test Channel",
            "Video URL": "https://www.youtube.com/watch?v=test123",
            "Summary": "Test summary content"
        }
        
        result = storage.store_video_summary(test_data)
        assert result is True, "Test entry should be stored successfully"
        
        # Verify entry was created
        response = notion_client.databases.query(database_id=database_id)
        pages_after_create = response.get("results", [])
        assert len(pages_after_create) == 1, "One page should exist after creation"
        
        # The cleanup fixture will clean up after this test


@pytest.mark.integration
class TestComponentIntegration:
    """Test individual component integrations with real APIs."""
    
    def test_metadata_extractor_integration(self, integration_config):
        """Test metadata extractor with real YouTube API."""
        if not integration_config.get('youtube_api_key'):
            pytest.skip("YouTube API key not available")
        
        factory = ComponentFactory()
        extractor = factory.create_metadata_extractor(
            youtube_api_key=integration_config['youtube_api_key']
        )
        
        test_video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        
        metadata = extractor.extract_metadata(test_video_url)
        
        # Verify metadata structure and content
        assert isinstance(metadata, dict)
        assert "title" in metadata
        assert "channel" in metadata
        assert "description" in metadata
        assert "published_at" in metadata
        assert "thumbnail_url" in metadata
        
        # Verify content quality
        assert len(metadata["title"]) > 0
        assert len(metadata["channel"]) > 0
        assert "youtube.com" in metadata["thumbnail_url"] or "ytimg.com" in metadata["thumbnail_url"]
    
    def test_summary_writer_integration(self, integration_config):
        """Test summary writer with real Gemini API."""
        if not integration_config.get('gemini_api_key'):
            pytest.skip("Gemini API key not available")
        
        factory = ComponentFactory()
        writer = factory.create_summary_writer(
            api_key=integration_config['gemini_api_key']
        )
        
        test_video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        test_metadata = {
            "title": "Test Video",
            "channel": "Test Channel",
            "description": "Test description"
        }
        
        summary = writer.generate_summary(test_video_url, test_metadata)
        
        # Verify summary quality
        assert isinstance(summary, str)
        assert len(summary) > 50, "Summary should be substantial"
        assert summary.strip(), "Summary should not be empty or whitespace"
        
        # Check for markdown formatting
        assert "#" in summary or "**" in summary or "*" in summary, "Summary should contain markdown formatting"
    
    def test_notion_storage_integration(self, clean_test_database, integration_config):
        """Test Notion storage with real Notion API."""
        if not integration_config.get('notion_token'):
            pytest.skip("Notion token not available")
        
        factory = ComponentFactory()
        storage = factory.create_storage(
            notion_token=integration_config['notion_token'],
            database_name=integration_config['database_name'],
            parent_page_name=integration_config['parent_page_name']
        )
        
        test_data = {
            "Title": "Integration Test Video",
            "Channel": "Test Channel",
            "Video URL": "https://www.youtube.com/watch?v=test123",
            "Cover": "https://img.youtube.com/vi/test123/maxresdefault.jpg",
            "Summary": "# Test Summary\n\nThis is a **test** summary with [8:05] timestamp."
        }
        
        result = storage.store_video_summary(test_data)
        assert result is True, "Storage should succeed"
        
        # Verify data was stored correctly
        database_id = clean_test_database['database_id']
        notion_client = storage.notion_client
        
        response = notion_client.databases.query(database_id=database_id)
        pages = response.get("results", [])
        
        assert len(pages) > 0, "At least one page should be created"
        
        page = pages[0]
        properties = page.get("properties", {})
        
        # Verify stored data
        title_prop = properties.get("Title", {})
        if title_prop.get("title"):
            stored_title = title_prop["title"][0]["text"]["content"]
            assert stored_title == test_data["Title"]
        
        url_prop = properties.get("Video URL", {})
        if url_prop.get("url"):
            assert url_prop["url"] == test_data["Video URL"]


@pytest.mark.integration
class TestErrorScenarios:
    """Test error scenarios with real APIs."""
    
    def test_network_resilience(self, integration_config):
        """Test network resilience and retry logic."""
        if not integration_config.get('gemini_api_key'):
            pytest.skip("Gemini API key not available")
        
        factory = ComponentFactory()
        writer = factory.create_summary_writer(
            api_key=integration_config['gemini_api_key']
        )
        
        # Test with a potentially problematic video URL
        test_video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        test_metadata = {
            "title": "Test Video",
            "channel": "Test Channel"
        }
        
        # This should succeed with retry logic if there are temporary failures
        summary = writer.generate_summary(test_video_url, test_metadata)
        assert isinstance(summary, str)
        assert len(summary) > 0
    
    def test_configuration_error_handling(self):
        """Test configuration error handling."""
        factory = ComponentFactory()
        
        # Test with invalid API keys
        with pytest.raises(ConfigurationError):
            writer = factory.create_summary_writer(api_key="")
            writer.validate_configuration()
        
        with pytest.raises(ConfigurationError):
            storage = factory.create_storage(
                notion_token="",
                database_name="Test",
                parent_page_name="Test"
            )
            storage.validate_configuration()