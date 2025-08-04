"""
Integration test configuration and fixtures.

This module provides fixtures and configuration for integration tests that
may connect to external services and use real APIs.
"""

import pytest
import os
import time
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
from notion_client import Client

# CRITICAL: Load test environment variables from .env-test ONLY
# Integration tests must NEVER use production .env file
test_env_path = '.env-test'
if os.path.exists(test_env_path):
    load_dotenv(test_env_path, override=True)
    # Set environment variable to indicate test mode
    os.environ['TEST_MODE'] = 'true'
else:
    pytest.exit("ERROR: .env-test file not found. Integration tests require separate test configuration.")


@pytest.fixture(scope="session")
def integration_config():
    """Configuration for integration tests."""
    config = {
        'notion_token': os.getenv('NOTION_TOKEN'),
        'gemini_api_key': os.getenv('GEMINI_API_KEY'),
        'youtube_api_key': os.getenv('YOUTUBE_API_KEY'),
        'database_name': os.getenv('DATABASE_NAME', 'YT Summaries [TEST]'),
        'parent_page_name': os.getenv('PARENT_PAGE_NAME', 'YouTube Summaries [TEST]'),
        'test_mode': os.getenv('TEST_MODE', 'false').lower() == 'true'
    }
    
    # Validate test configuration
    if not config['test_mode']:
        pytest.exit("ERROR: TEST_MODE not set. Integration tests must use .env-test configuration.")
    
    return config


@pytest.fixture(scope="session")
def notion_client(integration_config):
    """Notion client for integration tests."""
    if not integration_config['notion_token']:
        pytest.skip("NOTION_TOKEN not available for integration test")
    
    return Client(auth=integration_config['notion_token'])


@pytest.fixture(scope="session")
def test_database_setup(notion_client, integration_config):
    """Set up test database and return database info."""
    database_name = integration_config['database_name']
    parent_page_name = integration_config['parent_page_name']
    
    # Find or create parent page
    parent_page_id = _find_or_create_parent_page(notion_client, parent_page_name)
    
    # Find or create test database
    database_id = _find_or_create_test_database(notion_client, database_name, parent_page_id)
    
    return {
        'database_id': database_id,
        'parent_page_id': parent_page_id,
        'database_name': database_name,
        'parent_page_name': parent_page_name
    }


@pytest.fixture
def clean_test_database(notion_client, test_database_setup):
    """Clean test database before and after each test."""
    database_id = test_database_setup['database_id']
    
    # Clean before test
    _clean_database_entries(notion_client, database_id)
    
    yield test_database_setup
    
    # Clean after test
    _clean_database_entries(notion_client, database_id)


@pytest.fixture
def skip_if_no_api_keys(integration_config):
    """Skip test if required API keys are not available."""
    if not integration_config['notion_token']:
        pytest.skip("NOTION_TOKEN not available for integration test")
    if not integration_config['gemini_api_key']:
        pytest.skip("GEMINI_API_KEY not available for integration test")


@pytest.fixture
def test_video_data():
    """Sample test video data for integration tests."""
    return {
        "title": "Test Integration Video",
        "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "channel": "Test Channel",
        "cover_url": "https://img.youtube.com/vi/dQw4w9WgXcQ/maxresdefault.jpg",
        "summary": "# Test Summary\n\nThis is a **test** summary with [8:05] timestamp for integration testing."
    }


def _find_or_create_parent_page(notion_client: Client, parent_page_name: str) -> str:
    """Find or create the parent page for test database."""
    try:
        # Search for existing parent page
        search_results = notion_client.search(
            query=parent_page_name,
            filter={"property": "object", "value": "page"}
        )
        
        for result in search_results.get("results", []):
            if result.get("object") == "page":
                title_property = result.get("properties", {}).get("title", {})
                if title_property.get("title"):
                    title_text = title_property["title"][0].get("text", {}).get("content", "")
                    if title_text == parent_page_name:
                        return result["id"]
        
        # Create parent page if not found
        parent_page = notion_client.pages.create(
            parent={"type": "page_id", "page_id": _get_root_page_id(notion_client)},
            properties={
                "title": {
                    "title": [{"text": {"content": parent_page_name}}]
                }
            }
        )
        return parent_page["id"]
        
    except Exception as e:
        pytest.exit(f"ERROR: Failed to set up parent page '{parent_page_name}': {e}")


def _find_or_create_test_database(notion_client: Client, database_name: str, parent_page_id: str) -> str:
    """Find or create the test database."""
    try:
        # Search for existing database
        search_results = notion_client.search(
            query=database_name,
            filter={"property": "object", "value": "database"}
        )
        
        for result in search_results.get("results", []):
            if result.get("object") == "database":
                title_property = result.get("title", [])
                if title_property and title_property[0].get("text", {}).get("content") == database_name:
                    return result["id"]
        
        # Create test database if not found
        database = notion_client.databases.create(
            parent={"type": "page_id", "page_id": parent_page_id},
            title=[{"text": {"content": database_name}}],
            properties={
                "Title": {"title": {}},
                "Channel": {"rich_text": {}},
                "Video URL": {"url": {}},
                "Cover": {"files": {}},
                "Summary": {"rich_text": {}}
            }
        )
        return database["id"]
        
    except Exception as e:
        pytest.exit(f"ERROR: Failed to set up test database '{database_name}': {e}")


def _get_root_page_id(notion_client: Client) -> str:
    """Get a root page ID for creating the parent page."""
    try:
        # Search for any page to use as root
        search_results = notion_client.search(
            filter={"property": "object", "value": "page"}
        )
        
        if search_results.get("results"):
            return search_results["results"][0]["id"]
        
        # If no pages found, create a root page
        root_page = notion_client.pages.create(
            parent={"type": "workspace", "workspace": True},
            properties={
                "title": {
                    "title": [{"text": {"content": "Test Root Page"}}]
                }
            }
        )
        return root_page["id"]
        
    except Exception as e:
        pytest.exit(f"ERROR: Failed to get root page ID: {e}")


def _clean_database_entries(notion_client: Client, database_id: str) -> None:
    """Clean all entries from test database."""
    try:
        # Query all pages in the database
        response = notion_client.databases.query(database_id=database_id)
        
        # Archive all pages
        for page in response.get("results", []):
            try:
                notion_client.pages.update(
                    page_id=page["id"],
                    archived=True
                )
                # Small delay to avoid rate limiting
                time.sleep(0.1)
            except Exception as e:
                # Log but don't fail the test for cleanup issues
                print(f"Warning: Failed to clean page {page['id']}: {e}")
                
    except Exception as e:
        # Log but don't fail the test for cleanup issues
        print(f"Warning: Failed to clean database {database_id}: {e}")


# Register custom pytest markers for integration tests
def pytest_configure(config):
    """Configure pytest with custom markers for integration tests."""
    config.addinivalue_line("markers", "integration: marks tests as integration tests requiring API keys")
    config.addinivalue_line("markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')")
    config.addinivalue_line("markers", "external_api: marks tests that call external APIs")
    config.addinivalue_line("markers", "database_cleanup: marks tests that require database cleanup")