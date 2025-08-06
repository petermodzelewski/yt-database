"""
Unit test configuration and fixtures.

This module provides fixtures and configuration for unit tests that should
run quickly without external dependencies.
"""

import pytest
from unittest.mock import Mock

# Ensure unit tests don't accidentally load environment variables
import os
os.environ.pop('NOTION_TOKEN', None)
os.environ.pop('GEMINI_API_KEY', None)
os.environ.pop('YOUTUBE_API_KEY', None)


@pytest.fixture
def sample_video_metadata():
    """Sample video metadata for testing."""
    return {
        'video_id': 'test123',
        'title': 'Test Video Title',
        'channel': 'Test Channel',
        'description': 'Test video description',
        'published_at': '2024-01-01T00:00:00Z',
        'thumbnail_url': 'https://img.youtube.com/vi/test123/maxresdefault.jpg'
    }


@pytest.fixture
def sample_video_data():
    """Sample processed video data for testing."""
    return {
        'Title': 'Test Video Title',
        'Channel': 'Test Channel',
        'Video URL': 'https://youtu.be/test123',
        'Cover': 'https://img.youtube.com/vi/test123/maxresdefault.jpg',
        'Summary': '# Test Summary\n\nThis is a test summary with [8:05] timestamp.'
    }


@pytest.fixture
def mock_notion_client():
    """Mock Notion client for testing."""
    mock_client = Mock()
    mock_client.pages.create.return_value = {"id": "test-page-id"}
    mock_client.search.return_value = {
        "results": [{
            "id": "test-db-id",
            "object": "database",
            "title": [{"text": {"content": "YT Summaries"}}]
        }]
    }
    return mock_client