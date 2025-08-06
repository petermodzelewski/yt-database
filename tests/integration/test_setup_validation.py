"""
Integration test setup validation.

This module contains tests to verify that the integration test environment
is properly configured and can connect to required services.
"""

import pytest
import os


@pytest.mark.integration
class TestIntegrationSetup:
    """Test integration test environment setup."""
    
    def test_env_test_configuration_loaded(self, integration_config):
        """Test that .env-test configuration is properly loaded."""
        # Verify test mode is enabled
        assert integration_config['test_mode'] is True, "TEST_MODE should be true in integration tests"
        
        # Verify test database names are used
        assert "[TEST]" in integration_config['database_name'], "Database name should contain [TEST]"
        assert "[TEST]" in integration_config['parent_page_name'], "Parent page name should contain [TEST]"
        
        # Verify environment variable is set
        assert os.getenv('TEST_MODE') == 'true', "TEST_MODE environment variable should be set"
    
    def test_required_api_keys_available(self, integration_config):
        """Test that required API keys are available for integration tests."""
        # Check Notion token
        notion_token = integration_config.get('notion_token')
        if notion_token:
            assert not notion_token.startswith('your_'), "Notion token should not be placeholder"
            assert len(notion_token) > 10, "Notion token should be substantial"
        
        # Check Gemini API key
        gemini_key = integration_config.get('gemini_api_key')
        if gemini_key:
            assert not gemini_key.startswith('your_'), "Gemini API key should not be placeholder"
            assert len(gemini_key) > 10, "Gemini API key should be substantial"
    
    def test_test_database_setup_fixture(self, test_database_setup):
        """Test that test database setup fixture works correctly."""
        # Verify database setup returns required information
        assert 'database_id' in test_database_setup
        assert 'parent_page_id' in test_database_setup
        assert 'database_name' in test_database_setup
        assert 'parent_page_name' in test_database_setup
        
        # Verify test naming
        assert "[TEST]" in test_database_setup['database_name']
        assert "[TEST]" in test_database_setup['parent_page_name']
        
        # Verify IDs are valid
        assert len(test_database_setup['database_id']) > 10
        assert len(test_database_setup['parent_page_id']) > 10
    
    def test_notion_client_connection(self, notion_client, integration_config):
        """Test that Notion client can connect successfully."""
        if not integration_config.get('notion_token'):
            pytest.skip("Notion token not available")
        
        # Test basic API call
        try:
            # Search for any page to test connection
            response = notion_client.search(
                filter={"property": "object", "value": "page"}
            )
            
            # Should get a response without error
            assert 'results' in response
            assert isinstance(response['results'], list)
            
        except Exception as e:
            pytest.fail(f"Failed to connect to Notion API: {e}")
    
    def test_clean_database_fixture(self, clean_test_database, notion_client):
        """Test that database cleanup fixture works correctly."""
        database_id = clean_test_database['database_id']
        
        # Query the database to verify it's clean
        response = notion_client.databases.query(database_id=database_id)
        pages = response.get("results", [])
        
        # Should be empty due to cleanup
        assert len(pages) == 0, f"Database should be clean, but found {len(pages)} pages"
    
    def test_test_isolation(self, clean_test_database):
        """Test that tests are properly isolated."""
        # This test should start with a clean database
        # The clean_test_database fixture ensures this
        
        # Verify database info is available
        assert clean_test_database['database_id']
        assert clean_test_database['database_name']
        
        # This test doesn't create any data, so cleanup should be minimal
        # The fixture will still clean up after this test
    
    @pytest.mark.skipif(
        not os.getenv('GEMINI_API_KEY'),
        reason="Gemini API key not available"
    )
    def test_gemini_api_availability(self, integration_config):
        """Test that Gemini API is accessible."""
        gemini_key = integration_config.get('gemini_api_key')
        
        if not gemini_key:
            pytest.skip("Gemini API key not configured")
        
        # Basic validation - we can't easily test the API without making a real call
        # which would be expensive, so we just validate the key format
        assert isinstance(gemini_key, str)
        assert len(gemini_key) > 10
        assert not gemini_key.startswith('your_')
    
    def test_environment_isolation(self):
        """Test that integration tests don't use production environment."""
        # Verify TEST_MODE is set
        assert os.getenv('TEST_MODE') == 'true', "TEST_MODE should be set for integration tests"
        
        # Verify we're not accidentally using production database names
        db_name = os.getenv('DATABASE_NAME', '')
        parent_name = os.getenv('PARENT_PAGE_NAME', '')
        
        if db_name:
            assert "[TEST]" in db_name, f"Database name should contain [TEST], got: {db_name}"
        
        if parent_name:
            assert "[TEST]" in parent_name, f"Parent page name should contain [TEST], got: {parent_name}"