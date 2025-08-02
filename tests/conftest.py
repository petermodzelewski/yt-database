"""
Pytest configuration and fixtures.
"""

import sys
import os
import pytest
from unittest.mock import Mock

# Load environment variables from .env file for integration tests
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not available, skip loading
    pass

# Register custom pytest markers
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')")
    config.addinivalue_line("markers", "integration: marks tests as integration tests requiring API keys")
    config.addinivalue_line("markers", "unit: marks tests as unit tests")

# Add src to Python path for package imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(project_root, 'src'))


@pytest.fixture
def sample_video_data():
    """Sample YouTube video data for testing."""
    return {
        "title": "Test Video Title",
        "video_url": "https://www.youtube.com/watch?v=test123",
        "channel": "Test Channel",
        "cover_url": "https://img.youtube.com/vi/test123/maxresdefault.jpg",
        "summary": "# Test Summary\n\nThis is a **test** summary with [8:05] timestamp."
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


@pytest.fixture
def sample_markdown():
    """Sample markdown content for testing."""
    return """# Main Title

This is a paragraph with **bold** and *italic* text.

## Section Title

- First bullet point
- Second bullet point with [8:05] timestamp

1. First numbered item
2. Second numbered item

### Subsection

More content here."""