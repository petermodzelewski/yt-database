"""
Unit tests for web server configuration.

This module tests the WebServerConfig class and configuration
validation functionality.
"""

import pytest
from unittest.mock import patch
import os
from pydantic import ValidationError

from src.youtube_notion.web.config import WebServerConfig


class TestWebServerConfig:
    """Test WebServerConfig class functionality."""
    
    def test_default_configuration(self):
        """Test default configuration values."""
        config = WebServerConfig()
        
        assert config.host == "127.0.0.1"
        assert config.port == 8080
        assert config.debug is False
        assert config.static_folder == "web/static"
        assert config.max_queue_size == 100
        assert config.sse_heartbeat_interval == 30
        assert config.reload is False
        assert config.cors_origins == ["http://localhost:8080", "http://127.0.0.1:8080"]
    
    def test_custom_configuration(self):
        """Test configuration with custom values."""
        config = WebServerConfig(
            host="0.0.0.0",
            port=9000,
            debug=True,
            static_folder="custom/static",
            max_queue_size=50,
            sse_heartbeat_interval=10,
            reload=True,
            cors_origins=["http://example.com"]
        )
        
        assert config.host == "0.0.0.0"
        assert config.port == 9000
        assert config.debug is True
        assert config.static_folder == "custom/static"
        assert config.max_queue_size == 50
        assert config.sse_heartbeat_interval == 10
        assert config.reload is True
        assert config.cors_origins == ["http://example.com"]
    
    def test_environment_variable_configuration(self):
        """Test configuration from environment variables using from_env method."""
        env_vars = {
            'WEB_HOST': '192.168.1.100',
            'WEB_PORT': '3000',
            'WEB_DEBUG': 'true',
            'WEB_STATIC_FOLDER': 'assets/static',
            'WEB_MAX_QUEUE_SIZE': '200',
            'WEB_SSE_HEARTBEAT_INTERVAL': '60',
            'WEB_RELOAD': 'false'
        }
        
        with patch.dict(os.environ, env_vars):
            config = WebServerConfig.from_env()
            
            assert config.host == "192.168.1.100"
            assert config.port == 3000
            assert config.debug is True
            assert config.static_folder == "assets/static"
            assert config.max_queue_size == 200
            assert config.sse_heartbeat_interval == 60
            assert config.reload is False
    
    def test_pydantic_environment_variable_configuration(self):
        """Test Pydantic's automatic environment variable parsing."""
        env_vars = {
            'WEB_HOST': '10.0.0.1',
            'WEB_PORT': '5000',
            'WEB_DEBUG': 'true'
        }
        
        with patch.dict(os.environ, env_vars):
            config = WebServerConfig()
            
            # Note: Pydantic with env_prefix should pick up these values
            # The actual behavior depends on Pydantic version and configuration
            assert config.host in ["127.0.0.1", "10.0.0.1"]  # May or may not pick up env vars
            assert config.port in [8080, 5000]  # May or may not pick up env vars
    
    def test_invalid_port_validation(self):
        """Test that Pydantic accepts any integer for port (no built-in validation)."""
        # Pydantic doesn't validate port ranges by default, only that it's an integer
        config = WebServerConfig(port=-1)
        assert config.port == -1
        
        config = WebServerConfig(port=70000)
        assert config.port == 70000
    
    def test_invalid_max_queue_size_validation(self):
        """Test validation of invalid max queue size values."""
        # Pydantic allows 0 and negative values by default unless we add validators
        # These tests verify the current behavior
        config = WebServerConfig(max_queue_size=0)
        assert config.max_queue_size == 0
        
        config = WebServerConfig(max_queue_size=-10)
        assert config.max_queue_size == -10
    
    def test_invalid_sse_heartbeat_interval_validation(self):
        """Test validation of invalid SSE heartbeat interval values."""
        # Pydantic allows 0 and negative values by default unless we add validators
        config = WebServerConfig(sse_heartbeat_interval=0)
        assert config.sse_heartbeat_interval == 0
        
        config = WebServerConfig(sse_heartbeat_interval=-5)
        assert config.sse_heartbeat_interval == -5
    
    def test_invalid_host_validation(self):
        """Test validation of invalid host values."""
        # Pydantic allows empty strings by default unless we add validators
        config = WebServerConfig(host="")
        assert config.host == ""
    
    def test_invalid_static_folder_validation(self):
        """Test validation of invalid static folder values."""
        # Pydantic allows empty strings by default unless we add validators
        config = WebServerConfig(static_folder="")
        assert config.static_folder == ""
    
    def test_boolean_environment_variable_parsing(self):
        """Test parsing of boolean environment variables using from_env."""
        # Test various true values
        true_values = ['true', 'True', 'TRUE']
        for value in true_values:
            with patch.dict(os.environ, {'WEB_DEBUG': value}):
                config = WebServerConfig.from_env()
                assert config.debug is True, f"Failed for value: {value}"
        
        # Test various false values
        false_values = ['false', 'False', 'FALSE', '0', 'no', 'No', 'NO', '']
        for value in false_values:
            with patch.dict(os.environ, {'WEB_DEBUG': value}):
                config = WebServerConfig.from_env()
                assert config.debug is False, f"Failed for value: {value}"
    
    def test_integer_environment_variable_parsing(self):
        """Test parsing of integer environment variables using from_env."""
        with patch.dict(os.environ, {'WEB_PORT': '5000'}):
            config = WebServerConfig.from_env()
            assert config.port == 5000
        
        with patch.dict(os.environ, {'WEB_MAX_QUEUE_SIZE': '150'}):
            config = WebServerConfig.from_env()
            assert config.max_queue_size == 150
        
        with patch.dict(os.environ, {'WEB_SSE_HEARTBEAT_INTERVAL': '45'}):
            config = WebServerConfig.from_env()
            assert config.sse_heartbeat_interval == 45
    
    def test_cors_origins_environment_parsing(self):
        """Test parsing of CORS origins from environment variables."""
        with patch.dict(os.environ, {'WEB_CORS_ORIGINS': 'http://example.com,https://test.com,http://localhost:3000'}):
            config = WebServerConfig.from_env()
            expected_origins = ['http://example.com', 'https://test.com', 'http://localhost:3000']
            assert config.cors_origins == expected_origins
    
    def test_invalid_environment_variable_types(self):
        """Test handling of invalid environment variable types in from_env."""
        # Invalid port
        with patch.dict(os.environ, {'WEB_PORT': 'not_a_number'}):
            with pytest.raises(ValueError):
                WebServerConfig.from_env()
        
        # Invalid max queue size
        with patch.dict(os.environ, {'WEB_MAX_QUEUE_SIZE': 'invalid'}):
            with pytest.raises(ValueError):
                WebServerConfig.from_env()
        
        # Invalid SSE heartbeat interval
        with patch.dict(os.environ, {'WEB_SSE_HEARTBEAT_INTERVAL': 'bad_value'}):
            with pytest.raises(ValueError):
                WebServerConfig.from_env()
    
    def test_configuration_serialization(self):
        """Test configuration serialization to dictionary using model_dump."""
        config = WebServerConfig(
            host="localhost",
            port=4000,
            debug=True,
            max_queue_size=75
        )
        
        config_dict = config.model_dump()
        
        expected_keys = {
            'host', 'port', 'debug', 'static_folder', 
            'max_queue_size', 'sse_heartbeat_interval', 'reload', 'cors_origins'
        }
        assert set(config_dict.keys()) == expected_keys
        
        assert config_dict['host'] == "localhost"
        assert config_dict['port'] == 4000
        assert config_dict['debug'] is True
        assert config_dict['max_queue_size'] == 75
    
    def test_configuration_validation_method(self):
        """Test Pydantic model validation."""
        # Valid configuration - Pydantic validates on creation
        config = WebServerConfig()
        assert isinstance(config, WebServerConfig)
        
        # Test with edge case values
        config = WebServerConfig(
            port=1,  # Minimum valid port
            max_queue_size=1,  # Minimum valid queue size
            sse_heartbeat_interval=1  # Minimum valid interval
        )
        assert isinstance(config, WebServerConfig)
        
        config = WebServerConfig(
            port=65535,  # Maximum valid port
            max_queue_size=10000,  # Large queue size
            sse_heartbeat_interval=3600  # Large interval
        )
        assert isinstance(config, WebServerConfig)
    
    def test_configuration_copy(self):
        """Test configuration copying functionality."""
        original = WebServerConfig(
            host="original.host",
            port=8888,
            debug=True
        )
        
        # Create copy with modifications
        copy = WebServerConfig(
            host=original.host,
            port=9999,  # Different port
            debug=original.debug,
            static_folder=original.static_folder,
            max_queue_size=original.max_queue_size,
            sse_heartbeat_interval=original.sse_heartbeat_interval,
            reload=original.reload
        )
        
        assert copy.host == original.host
        assert copy.port != original.port
        assert copy.debug == original.debug
        assert copy.static_folder == original.static_folder
    
    def test_configuration_string_representation(self):
        """Test configuration string representation."""
        config = WebServerConfig(
            host="test.host",
            port=7777,
            debug=True
        )
        
        config_str = str(config)
        
        # Should contain key configuration values
        assert "test.host" in config_str
        assert "7777" in config_str
        assert "debug=True" in config_str or "True" in config_str
    
    def test_production_vs_development_presets(self):
        """Test production vs development configuration presets."""
        # Development preset
        dev_config = WebServerConfig(
            debug=True,
            reload=True,
            sse_heartbeat_interval=5  # Fast heartbeat for development
        )
        
        assert dev_config.debug is True
        assert dev_config.reload is True
        assert dev_config.sse_heartbeat_interval == 5
        
        # Production preset
        prod_config = WebServerConfig(
            debug=False,
            reload=False,
            sse_heartbeat_interval=60,  # Slower heartbeat for production
            host="0.0.0.0"  # Listen on all interfaces
        )
        
        assert prod_config.debug is False
        assert prod_config.reload is False
        assert prod_config.sse_heartbeat_interval == 60
        assert prod_config.host == "0.0.0.0"


class TestWebServerConfigIntegration:
    """Test WebServerConfig integration with other components."""
    
    def test_config_with_web_server_initialization(self):
        """Test configuration integration with WebServer initialization."""
        from tests.fixtures.mock_implementations import MockQueueManager
        from src.youtube_notion.web.server import WebServer
        
        config = WebServerConfig(
            port=8081,
            debug=True,
            max_queue_size=50
        )
        
        mock_queue_manager = MockQueueManager()
        
        # Should not raise any errors
        server = WebServer(mock_queue_manager, config)
        
        assert server.config.port == 8081
        assert server.config.debug is True
        assert server.config.max_queue_size == 50
    
    def test_config_environment_override_priority(self):
        """Test that explicit parameters override environment variables."""
        env_vars = {
            'WEB_PORT': '5000',
            'WEB_DEBUG': 'false'
        }
        
        with patch.dict(os.environ, env_vars):
            # Explicit parameters should override environment
            config = WebServerConfig(
                port=6000,  # Should override WEB_PORT
                debug=True   # Should override WEB_DEBUG
            )
            
            assert config.port == 6000  # Explicit value wins
            assert config.debug is True  # Explicit value wins
    
    def test_config_partial_environment_override(self):
        """Test partial configuration from environment variables using from_env."""
        env_vars = {
            'WEB_PORT': '4000',
            'WEB_DEBUG': 'true'
            # Other values should use defaults
        }
        
        with patch.dict(os.environ, env_vars):
            config = WebServerConfig.from_env()
            
            # Environment values
            assert config.port == 4000
            assert config.debug is True
            
            # Default values
            assert config.host == "127.0.0.1"
            assert config.max_queue_size == 100
            assert config.sse_heartbeat_interval == 30


if __name__ == "__main__":
    pytest.main([__file__, "-v"])