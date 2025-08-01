"""
Tests for configuration management system.

This module tests the configuration validation, environment variable handling,
and error reporting functionality.
"""

import os
import pytest
from unittest.mock import patch, mock_open
from youtube_notion.config import (
    ApplicationConfig,
    NotionConfig,
    YouTubeProcessorConfig,
    ConfigurationError,
    DEFAULT_SUMMARY_PROMPT,
    validate_environment_variables,
    get_configuration_help,
    print_configuration_error,
    load_custom_prompt
)


class TestYouTubeProcessorConfig:
    """Test YouTubeProcessorConfig validation and initialization."""
    
    def test_valid_config(self):
        """Test creating a valid configuration."""
        config = YouTubeProcessorConfig(
            gemini_api_key="test_key",
            youtube_api_key="youtube_key",
            default_prompt="Test prompt",
            max_retries=5,
            timeout_seconds=60
        )
        
        assert config.gemini_api_key == "test_key"
        assert config.youtube_api_key == "youtube_key"
        assert config.default_prompt == "Test prompt"
        assert config.max_retries == 5
        assert config.timeout_seconds == 60
    
    def test_missing_gemini_api_key(self):
        """Test that missing Gemini API key raises ValueError."""
        with pytest.raises(ValueError, match="Gemini API key is required"):
            YouTubeProcessorConfig(gemini_api_key="")
    
    def test_negative_max_retries(self):
        """Test that negative max_retries raises ValueError."""
        with pytest.raises(ValueError, match="max_retries must be non-negative"):
            YouTubeProcessorConfig(
                gemini_api_key="test_key",
                max_retries=-1
            )
    
    def test_zero_timeout(self):
        """Test that zero timeout raises ValueError."""
        with pytest.raises(ValueError, match="timeout_seconds must be positive"):
            YouTubeProcessorConfig(
                gemini_api_key="test_key",
                timeout_seconds=0
            )
    
    def test_invalid_temperature(self):
        """Test that invalid temperature raises ValueError."""
        with pytest.raises(ValueError, match="gemini_temperature must be between 0 and 2"):
            YouTubeProcessorConfig(
                gemini_api_key="test_key",
                gemini_temperature=3.0
            )
        
        with pytest.raises(ValueError, match="gemini_temperature must be between 0 and 2"):
            YouTubeProcessorConfig(
                gemini_api_key="test_key",
                gemini_temperature=-0.1
            )
    
    def test_invalid_max_output_tokens(self):
        """Test that invalid max_output_tokens raises ValueError."""
        with pytest.raises(ValueError, match="gemini_max_output_tokens must be positive"):
            YouTubeProcessorConfig(
                gemini_api_key="test_key",
                gemini_max_output_tokens=0
            )
    
    def test_default_values(self):
        """Test that default values are set correctly."""
        config = YouTubeProcessorConfig(gemini_api_key="test_key")
        
        assert config.youtube_api_key is None
        assert config.default_prompt == DEFAULT_SUMMARY_PROMPT
        assert config.max_retries == 3
        assert config.timeout_seconds == 120
        assert config.gemini_model == "gemini-2.0-flash-exp"
        assert config.gemini_temperature == 0.1
        assert config.gemini_max_output_tokens == 4000


class TestNotionConfig:
    """Test NotionConfig validation and initialization."""
    
    def test_valid_config(self):
        """Test creating a valid Notion configuration."""
        config = NotionConfig(
            notion_token="test_token",
            database_name="Test DB",
            parent_page_name="Test Page"
        )
        
        assert config.notion_token == "test_token"
        assert config.database_name == "Test DB"
        assert config.parent_page_name == "Test Page"
    
    def test_missing_notion_token(self):
        """Test that missing Notion token raises ValueError."""
        with pytest.raises(ValueError, match="Notion token is required"):
            NotionConfig(notion_token="")
    
    def test_empty_database_name(self):
        """Test that empty database name raises ValueError."""
        with pytest.raises(ValueError, match="Database name cannot be empty"):
            NotionConfig(
                notion_token="test_token",
                database_name=""
            )
    
    def test_empty_parent_page_name(self):
        """Test that empty parent page name raises ValueError."""
        with pytest.raises(ValueError, match="Parent page name cannot be empty"):
            NotionConfig(
                notion_token="test_token",
                parent_page_name=""
            )
    
    def test_default_values(self):
        """Test that default values are set correctly."""
        config = NotionConfig(notion_token="test_token")
        
        assert config.database_name == "YT Summaries"
        assert config.parent_page_name == "YouTube Knowledge Base"


class TestValidateEnvironmentVariables:
    """Test environment variable validation."""
    
    def test_valid_example_mode(self):
        """Test validation in example mode with valid variables."""
        env_vars = {
            "NOTION_TOKEN": "test_token"
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            result = validate_environment_variables(youtube_mode=False)
            assert result["NOTION_TOKEN"] == "test_token"
    
    def test_valid_youtube_mode(self):
        """Test validation in YouTube mode with valid variables."""
        env_vars = {
            "NOTION_TOKEN": "test_token",
            "GEMINI_API_KEY": "test_gemini_key",
            "YOUTUBE_API_KEY": "test_youtube_key"
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            result = validate_environment_variables(youtube_mode=True)
            assert result["NOTION_TOKEN"] == "test_token"
            assert result["GEMINI_API_KEY"] == "test_gemini_key"
            assert result["YOUTUBE_API_KEY"] == "test_youtube_key"
    
    def test_missing_notion_token(self):
        """Test that missing NOTION_TOKEN raises ConfigurationError."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ConfigurationError) as exc_info:
                validate_environment_variables(youtube_mode=False)
            
            assert "NOTION_TOKEN" in exc_info.value.missing_vars
    
    def test_missing_gemini_key_youtube_mode(self):
        """Test that missing GEMINI_API_KEY in YouTube mode raises ConfigurationError."""
        env_vars = {"NOTION_TOKEN": "test_token"}
        
        with patch.dict(os.environ, env_vars, clear=True):
            with pytest.raises(ConfigurationError) as exc_info:
                validate_environment_variables(youtube_mode=True)
            
            assert "GEMINI_API_KEY" in exc_info.value.missing_vars
    
    def test_invalid_integer_values(self):
        """Test validation of integer environment variables."""
        env_vars = {
            "NOTION_TOKEN": "test_token",
            "GEMINI_API_KEY": "test_key",
            "YOUTUBE_PROCESSOR_MAX_RETRIES": "invalid"
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            with pytest.raises(ConfigurationError) as exc_info:
                validate_environment_variables(youtube_mode=True)
            
            assert "YOUTUBE_PROCESSOR_MAX_RETRIES" in exc_info.value.invalid_vars
            assert "must be a valid int" in exc_info.value.invalid_vars["YOUTUBE_PROCESSOR_MAX_RETRIES"]
    
    def test_invalid_float_values(self):
        """Test validation of float environment variables."""
        env_vars = {
            "NOTION_TOKEN": "test_token",
            "GEMINI_API_KEY": "test_key",
            "GEMINI_TEMPERATURE": "invalid"
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            with pytest.raises(ConfigurationError) as exc_info:
                validate_environment_variables(youtube_mode=True)
            
            assert "GEMINI_TEMPERATURE" in exc_info.value.invalid_vars
            assert "must be a valid float" in exc_info.value.invalid_vars["GEMINI_TEMPERATURE"]
    
    def test_invalid_range_values(self):
        """Test validation of values with specific ranges."""
        env_vars = {
            "NOTION_TOKEN": "test_token",
            "GEMINI_API_KEY": "test_key",
            "YOUTUBE_PROCESSOR_MAX_RETRIES": "-1",
            "GEMINI_TEMPERATURE": "3.0"
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            with pytest.raises(ConfigurationError) as exc_info:
                validate_environment_variables(youtube_mode=True)
            
            assert "YOUTUBE_PROCESSOR_MAX_RETRIES" in exc_info.value.invalid_vars
            assert "must be non-negative" in exc_info.value.invalid_vars["YOUTUBE_PROCESSOR_MAX_RETRIES"]
            assert "GEMINI_TEMPERATURE" in exc_info.value.invalid_vars
            assert "must be between 0 and 2" in exc_info.value.invalid_vars["GEMINI_TEMPERATURE"]
    
    def test_invalid_boolean_values(self):
        """Test validation of boolean environment variables."""
        env_vars = {
            "NOTION_TOKEN": "test_token",
            "DEBUG": "maybe"
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            with pytest.raises(ConfigurationError) as exc_info:
                validate_environment_variables(youtube_mode=False)
            
            assert "DEBUG" in exc_info.value.invalid_vars
            assert "must be 'true' or 'false'" in exc_info.value.invalid_vars["DEBUG"]
    
    def test_valid_optional_values(self):
        """Test that valid optional values are included."""
        env_vars = {
            "NOTION_TOKEN": "test_token",
            "GEMINI_API_KEY": "test_key",
            "DATABASE_NAME": "Custom DB",
            "YOUTUBE_PROCESSOR_MAX_RETRIES": "5",
            "GEMINI_TEMPERATURE": "0.5",
            "DEBUG": "true"
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            result = validate_environment_variables(youtube_mode=True)
            assert result["DATABASE_NAME"] == "Custom DB"
            assert result["YOUTUBE_PROCESSOR_MAX_RETRIES"] == "5"
            assert result["GEMINI_TEMPERATURE"] == "0.5"
            assert result["DEBUG"] == "true"


class TestApplicationConfig:
    """Test ApplicationConfig creation and validation."""
    
    def test_from_environment_example_mode(self):
        """Test creating config from environment in example mode."""
        env_vars = {
            "NOTION_TOKEN": "test_token",
            "DATABASE_NAME": "Custom DB"
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            config = ApplicationConfig.from_environment(youtube_mode=False)
            
            assert config.notion.notion_token == "test_token"
            assert config.notion.database_name == "Custom DB"
            assert config.youtube_processor is None
    
    def test_from_environment_youtube_mode(self):
        """Test creating config from environment in YouTube mode."""
        env_vars = {
            "NOTION_TOKEN": "test_token",
            "GEMINI_API_KEY": "test_gemini_key",
            "YOUTUBE_API_KEY": "test_youtube_key",
            "YOUTUBE_PROCESSOR_MAX_RETRIES": "5"
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            config = ApplicationConfig.from_environment(youtube_mode=True)
            
            assert config.notion.notion_token == "test_token"
            assert config.youtube_processor is not None
            assert config.youtube_processor.gemini_api_key == "test_gemini_key"
            assert config.youtube_processor.youtube_api_key == "test_youtube_key"
            assert config.youtube_processor.max_retries == 5
    
    def test_from_environment_missing_vars(self):
        """Test that missing environment variables raise ConfigurationError."""
        with patch.dict(os.environ, {}, clear=True):
            with patch('youtube_notion.config.settings.load_dotenv'):  # Prevent .env loading
                with pytest.raises(ConfigurationError):
                    ApplicationConfig.from_environment(youtube_mode=False)


class TestConfigurationHelpers:
    """Test configuration helper functions."""
    
    def test_get_configuration_help_example_mode(self):
        """Test configuration help for example mode."""
        help_text = get_configuration_help(youtube_mode=False)
        
        assert "NOTION_TOKEN" in help_text
        assert "GEMINI_API_KEY" not in help_text
        assert "YOUTUBE_API_KEY" not in help_text
    
    def test_get_configuration_help_youtube_mode(self):
        """Test configuration help for YouTube mode."""
        help_text = get_configuration_help(youtube_mode=True)
        
        assert "NOTION_TOKEN" in help_text
        assert "GEMINI_API_KEY" in help_text
        assert "YOUTUBE_API_KEY" in help_text
        assert "GEMINI_TEMPERATURE" in help_text
    
    def test_print_configuration_error(self, capsys):
        """Test printing configuration error messages."""
        error = ConfigurationError(
            "Test error",
            missing_vars=["NOTION_TOKEN", "GEMINI_API_KEY"],
            invalid_vars={"DEBUG": "must be true or false"}
        )
        
        print_configuration_error(error, youtube_mode=True)
        captured = capsys.readouterr()
        
        assert "Missing required environment variables:" in captured.out
        assert "NOTION_TOKEN" in captured.out
        assert "GEMINI_API_KEY" in captured.out
        assert "Invalid environment variable values:" in captured.out
        assert "DEBUG: must be true or false" in captured.out
    
    def test_load_custom_prompt_from_file(self):
        """Test loading custom prompt from file."""
        test_prompt = "This is a test prompt"
        
        with patch("builtins.open", mock_open(read_data=test_prompt)):
            with patch("os.path.exists", return_value=True):
                result = load_custom_prompt("test_prompt.txt")
                assert result == test_prompt
    
    def test_load_custom_prompt_from_env(self):
        """Test loading custom prompt from environment variable."""
        test_prompt = "Environment prompt"
        
        with patch.dict(os.environ, {"DEFAULT_SUMMARY_PROMPT": test_prompt}):
            with patch("os.path.exists", return_value=False):
                result = load_custom_prompt("nonexistent.txt")
                assert result == test_prompt
    
    def test_load_custom_prompt_default(self):
        """Test loading default prompt when no custom prompt is found."""
        with patch.dict(os.environ, {}, clear=True):
            with patch("os.path.exists", return_value=False):
                result = load_custom_prompt("nonexistent.txt")
                assert result == DEFAULT_SUMMARY_PROMPT
    
    def test_load_custom_prompt_file_error(self):
        """Test handling file read errors gracefully."""
        with patch("builtins.open", side_effect=IOError("File error")):
            with patch("os.path.exists", return_value=True):
                with patch.dict(os.environ, {}, clear=True):
                    result = load_custom_prompt("error_file.txt")
                    assert result == DEFAULT_SUMMARY_PROMPT


class TestConfigurationError:
    """Test ConfigurationError exception."""
    
    def test_basic_error(self):
        """Test basic ConfigurationError creation."""
        error = ConfigurationError("Test message")
        
        assert str(error) == "Test message"
        assert error.missing_vars == []
        assert error.invalid_vars == {}
    
    def test_error_with_details(self):
        """Test ConfigurationError with missing and invalid variables."""
        missing = ["VAR1", "VAR2"]
        invalid = {"VAR3": "reason1", "VAR4": "reason2"}
        
        error = ConfigurationError("Test message", missing, invalid)
        
        assert error.missing_vars == missing
        assert error.invalid_vars == invalid