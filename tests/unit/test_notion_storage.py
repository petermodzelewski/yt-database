"""
Unit tests for NotionStorage backend implementation.

These tests use mocked Notion API responses to verify the storage backend
functionality without making actual API calls.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from notion_client import Client

from src.youtube_notion.storage.notion_storage import NotionStorage
from src.youtube_notion.utils.exceptions import StorageError, ConfigurationError


class TestNotionStorage:
    """Test suite for NotionStorage class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.notion_token = "test_token"
        self.database_name = "YT Summaries"
        self.parent_page_name = "YouTube Summaries"
        
        self.storage = NotionStorage(
            notion_token=self.notion_token,
            database_name=self.database_name,
            parent_page_name=self.parent_page_name
        )
        
        self.sample_video_data = {
            'Title': 'Test Video Title',
            'Channel': 'Test Channel',
            'Video URL': 'https://www.youtube.com/watch?v=test123',
            'Cover': 'https://img.youtube.com/vi/test123/maxresdefault.jpg',
            'Summary': '# Test Summary\n\nThis is a test summary with [8:05] timestamp.'
        }
    
    def test_init(self):
        """Test NotionStorage initialization."""
        storage = NotionStorage("token", "db_name", "parent_name")
        assert storage.notion_token == "token"
        assert storage.database_name == "db_name"
        assert storage.parent_page_name == "parent_name"
        assert storage._client is None
        assert storage._database_id is None
    
    @patch('src.youtube_notion.storage.notion_storage.Client')
    def test_client_property_creates_client(self, mock_client_class):
        """Test that client property creates Notion client when needed."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        client = self.storage.client
        
        mock_client_class.assert_called_once_with(auth=self.notion_token, timeout_ms=self.storage.timeout_seconds * 1000)
        assert client == mock_client
        assert self.storage._client == mock_client
    
    @patch('src.youtube_notion.storage.notion_storage.Client')
    def test_client_property_reuses_client(self, mock_client_class):
        """Test that client property reuses existing client."""
        mock_client = Mock()
        self.storage._client = mock_client
        
        client = self.storage.client
        
        mock_client_class.assert_not_called()
        assert client == mock_client
    
    def test_client_property_raises_on_missing_token(self):
        """Test that NotionStorage raises error when token is missing."""
        with pytest.raises(ConfigurationError, match="Notion token is required"):
            NotionStorage("", "db", "parent")
    
    @patch('src.youtube_notion.storage.notion_storage.Client')
    @patch('src.youtube_notion.storage.notion_storage.enrich_timestamps_with_links')
    @patch('src.youtube_notion.storage.notion_storage.markdown_to_notion_blocks')
    def test_store_video_summary_success(self, mock_markdown_blocks, mock_enrich_timestamps, mock_client_class):
        """Test successful video summary storage."""
        # Setup mocks
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_enrich_timestamps.return_value = "enriched summary"
        mock_markdown_blocks.return_value = [{"type": "paragraph", "paragraph": {"rich_text": []}}]
        
        mock_client.pages.create.return_value = {"id": "page_123"}
        
        # Mock find_target_location
        self.storage._database_id = "db_123"
        
        # Execute
        result = self.storage.store_video_summary(self.sample_video_data)
        
        # Verify
        assert result is True
        
        # Verify timestamp enrichment was called
        mock_enrich_timestamps.assert_called_once_with(
            self.sample_video_data['Summary'],
            self.sample_video_data['Video URL']
        )
        
        # Verify markdown conversion was called
        mock_markdown_blocks.assert_called_once_with("enriched summary")
        
        # Verify page creation
        mock_client.pages.create.assert_called_once()
        call_args = mock_client.pages.create.call_args
        
        # Check parent database
        assert call_args[1]['parent']['database_id'] == "db_123"
        
        # Check properties
        properties = call_args[1]['properties']
        assert properties['Title']['title'][0]['text']['content'] == self.sample_video_data['Title']
        assert properties['Video URL']['url'] == self.sample_video_data['Video URL']
        assert properties['Channel']['rich_text'][0]['text']['content'] == self.sample_video_data['Channel']
        
        # Check cover
        assert call_args[1]['cover']['type'] == 'external'
        assert call_args[1]['cover']['external']['url'] == self.sample_video_data['Cover']
        
        # Check children blocks (embed + divider + summary)
        children = call_args[1]['children']
        assert len(children) == 3  # embed + divider + summary block
        assert children[0]['type'] == 'embed'
        assert children[0]['embed']['url'] == self.sample_video_data['Video URL']
        assert children[1]['type'] == 'divider'
    
    def test_store_video_summary_missing_required_field(self):
        """Test storage fails when required field is missing."""
        incomplete_data = {
            'Title': 'Test Video',
            'Channel': 'Test Channel'
            # Missing Video URL and Summary
        }
        
        with pytest.raises(StorageError, match="Missing required field"):
            self.storage.store_video_summary(incomplete_data)
    
    @patch('src.youtube_notion.storage.notion_storage.Client')
    def test_store_video_summary_no_database_found(self, mock_client_class):
        """Test storage fails when target database is not found."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        # Mock find_target_location to return None
        with patch.object(self.storage, 'find_target_location', return_value=None):
            with pytest.raises(StorageError, match="Could not find database"):
                self.storage.store_video_summary(self.sample_video_data)
    
    @patch('src.youtube_notion.storage.notion_storage.Client')
    def test_store_video_summary_without_cover(self, mock_client_class):
        """Test storage works without cover image."""
        # Setup mocks
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.pages.create.return_value = {"id": "page_123"}
        
        # Mock dependencies
        with patch('src.youtube_notion.storage.notion_storage.enrich_timestamps_with_links') as mock_enrich, \
             patch('src.youtube_notion.storage.notion_storage.markdown_to_notion_blocks') as mock_blocks:
            
            mock_enrich.return_value = "enriched"
            mock_blocks.return_value = []
            
            # Remove cover from data
            data_without_cover = self.sample_video_data.copy()
            del data_without_cover['Cover']
            
            self.storage._database_id = "db_123"
            
            result = self.storage.store_video_summary(data_without_cover)
            
            assert result is True
            
            # Verify cover was not set
            call_args = mock_client.pages.create.call_args
            assert call_args[1]['cover'] is None
    
    @patch('src.youtube_notion.storage.notion_storage.Client')
    def test_store_video_summary_api_error(self, mock_client_class):
        """Test storage handles Notion API errors."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.pages.create.side_effect = Exception("API Error")
        
        self.storage._database_id = "db_123"
        
        with patch('src.youtube_notion.storage.notion_storage.enrich_timestamps_with_links'), \
             patch('src.youtube_notion.storage.notion_storage.markdown_to_notion_blocks'):
            
            with pytest.raises(StorageError, match="Unexpected error during Notion API call"):
                self.storage.store_video_summary(self.sample_video_data)
    
    def test_validate_configuration_missing_token(self):
        """Test configuration validation fails with missing token."""
        with pytest.raises(ConfigurationError, match="Notion token is required"):
            NotionStorage("", "db", "parent")
    
    def test_validate_configuration_missing_database_name(self):
        """Test configuration validation fails with missing database name."""
        with pytest.raises(ConfigurationError, match="Database name is required"):
            NotionStorage("token", "", "parent")
    
    def test_validate_configuration_missing_parent_page(self):
        """Test configuration validation succeeds with empty parent page name (optional)."""
        # Parent page name is optional, so this should not raise an error
        storage = NotionStorage("token", "db", "")
        assert storage.parent_page_name == ""
    
    @patch('src.youtube_notion.storage.notion_storage.Client')
    def test_validate_configuration_success(self, mock_client_class):
        """Test successful configuration validation."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.search.return_value = {"results": []}
        
        result = self.storage.validate_configuration()
        
        assert result is True
        mock_client_class.assert_called_once_with(auth=self.notion_token, timeout_ms=self.storage.timeout_seconds * 1000)
        mock_client.search.assert_called_once_with(filter={"property": "object", "value": "database"})
    
    @patch('src.youtube_notion.storage.notion_storage.Client')
    def test_validate_configuration_invalid_token(self, mock_client_class):
        """Test configuration validation fails with invalid token."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.search.side_effect = Exception("Invalid token")
        
        with pytest.raises(ConfigurationError, match="Invalid Notion configuration"):
            self.storage.validate_configuration()
    
    @patch('src.youtube_notion.storage.notion_storage.Client')
    def test_find_target_location_success(self, mock_client_class):
        """Test successful database location finding."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        # Mock search results
        mock_client.search.return_value = {
            "results": [
                {
                    "id": "db_123",
                    "title": [{"plain_text": "YT Summaries"}],
                    "parent": {"page_id": "parent_123"}
                }
            ]
        }
        
        # Mock parent page retrieval
        mock_client.pages.retrieve.return_value = {
            "properties": {
                "title": {
                    "title": [{"plain_text": "YouTube Summaries"}]
                }
            }
        }
        
        result = self.storage.find_target_location()
        
        assert result == "db_123"
        assert self.storage._database_id == "db_123"
        
        mock_client.search.assert_called_once_with(filter={"property": "object", "value": "database"})
        mock_client.pages.retrieve.assert_called_once_with("parent_123")
    
    @patch('src.youtube_notion.storage.notion_storage.Client')
    def test_find_target_location_cached(self, mock_client_class):
        """Test that cached database ID is returned without API call."""
        self.storage._database_id = "cached_db_123"
        
        result = self.storage.find_target_location()
        
        assert result == "cached_db_123"
        mock_client_class.assert_not_called()
    
    @patch('src.youtube_notion.storage.notion_storage.Client')
    def test_find_target_location_no_match(self, mock_client_class):
        """Test database location finding when no matching database exists."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        # Mock search results with no matching database
        mock_client.search.return_value = {
            "results": [
                {
                    "id": "db_456",
                    "title": [{"plain_text": "Other Database"}],
                    "parent": {"page_id": "parent_456"}
                }
            ]
        }
        
        result = self.storage.find_target_location()
        
        assert result is None
        assert self.storage._database_id is None
    
    @patch('src.youtube_notion.storage.notion_storage.Client')
    def test_find_target_location_wrong_parent(self, mock_client_class):
        """Test database location finding when database is in wrong parent page."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        # Mock search results
        mock_client.search.return_value = {
            "results": [
                {
                    "id": "db_123",
                    "title": [{"plain_text": "YT Summaries"}],
                    "parent": {"page_id": "parent_123"}
                }
            ]
        }
        
        # Mock parent page retrieval with wrong parent name
        mock_client.pages.retrieve.return_value = {
            "properties": {
                "title": {
                    "title": [{"plain_text": "Wrong Parent"}]
                }
            }
        }
        
        result = self.storage.find_target_location()
        
        assert result is None
        assert self.storage._database_id is None
    
    @patch('src.youtube_notion.storage.notion_storage.Client')
    def test_find_target_location_no_parent_requirement(self, mock_client_class):
        """Test database location finding without parent page requirement."""
        storage = NotionStorage("token", "YT Summaries", "")
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        # Mock search results
        mock_client.search.return_value = {
            "results": [
                {
                    "id": "db_123",
                    "title": [{"plain_text": "YT Summaries"}],
                    "parent": {"page_id": "parent_123"}
                }
            ]
        }
        
        result = storage.find_target_location()
        
        assert result == "db_123"
        # Should not retrieve parent page when no parent requirement
        mock_client.pages.retrieve.assert_not_called()
    
    @patch('src.youtube_notion.storage.notion_storage.Client')
    def test_find_target_location_api_error(self, mock_client_class):
        """Test database location finding handles API errors."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.search.side_effect = Exception("API Error")
        
        with pytest.raises(StorageError, match="Unexpected error during Notion API call"):
            self.storage.find_target_location()
    
    @patch('src.youtube_notion.storage.notion_storage.Client')
    def test_find_target_location_parent_retrieval_error(self, mock_client_class):
        """Test database location finding handles parent page retrieval errors."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        # Mock search results
        mock_client.search.return_value = {
            "results": [
                {
                    "id": "db_123",
                    "title": [{"plain_text": "YT Summaries"}],
                    "parent": {"page_id": "parent_123"}
                },
                {
                    "id": "db_456",
                    "title": [{"plain_text": "YT Summaries"}],
                    "parent": {"page_id": "parent_456"}
                }
            ]
        }
        
        # Mock parent page retrieval to fail for first, succeed for second
        def mock_retrieve(page_id):
            if page_id == "parent_123":
                raise Exception("Cannot retrieve parent")
            return {
                "properties": {
                    "title": {
                        "title": [{"plain_text": "YouTube Summaries"}]
                    }
                }
            }
        
        mock_client.pages.retrieve.side_effect = mock_retrieve
        
        result = self.storage.find_target_location()
        
        # Should find the second database after first fails
        assert result == "db_456"
    
    @patch('src.youtube_notion.storage.notion_storage.Client')
    def test_find_target_location_empty_title(self, mock_client_class):
        """Test database location finding handles databases with empty titles."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        # Mock search results with empty title
        mock_client.search.return_value = {
            "results": [
                {
                    "id": "db_123",
                    "title": [],  # Empty title
                    "parent": {"page_id": "parent_123"}
                },
                {
                    "id": "db_456",
                    "title": [{"plain_text": "YT Summaries"}],
                    "parent": {"page_id": "parent_456"}
                }
            ]
        }
        
        # Mock parent page retrieval
        mock_client.pages.retrieve.return_value = {
            "properties": {
                "title": {
                    "title": [{"plain_text": "YouTube Summaries"}]
                }
            }
        }
        
        result = self.storage.find_target_location()
        
        # Should find the second database with proper title
        assert result == "db_456"