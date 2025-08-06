"""
Tests for configuration management system.

This module tests the configuration validation, environment variable handling,
and error reporting functionality.
"""

import os
import pytest
from unittest.mock import patch, mock_open, Mock
from src.youtube_notion.config import (
    ApplicationConfig,
    NotionConfig,
    YouTubeProcessorConfig,
    DEFAULT_SUMMARY_PROMPT,
    validate_environment_variables,
    get_configuration_help,
    print_configuration_error,
    load_custom_prompt,
    ComponentFactory
)
from src.youtube_notion.config.settings import ConfigurationError as SettingsConfigurationError
from src.youtube_notion.utils.exceptions import ConfigurationError


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
            with patch('src.youtube_notion.config.settings.load_dotenv'):  # Prevent .env loading
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


class TestComponentFactory:
    """Test ComponentFactory for dependency injection."""
    
    def test_factory_initialization_valid_config(self):
        """Test factory initialization with valid configuration."""
        notion_config = NotionConfig(notion_token="test_token")
        youtube_config = YouTubeProcessorConfig(gemini_api_key="test_gemini_key")
        app_config = ApplicationConfig(notion=notion_config, youtube_processor=youtube_config)
        
        factory = ComponentFactory(app_config)
        
        assert factory.config == app_config
    
    def test_factory_initialization_no_config(self):
        """Test that factory initialization fails with no configuration."""
        with pytest.raises(ConfigurationError, match="Application configuration is required"):
            ComponentFactory(None)
    
    def test_factory_initialization_invalid_config_type(self):
        """Test that factory initialization fails with invalid configuration type."""
        with pytest.raises(ConfigurationError, match="Invalid application configuration type"):
            ComponentFactory("invalid_config")
    
    def test_factory_initialization_no_notion_config(self):
        """Test that factory initialization fails without Notion configuration."""
        app_config = ApplicationConfig(notion=None)
        
        with pytest.raises(ConfigurationError, match="Notion configuration is required"):
            ComponentFactory(app_config)
    
    def test_create_summary_writer_success(self):
        """Test successful summary writer creation."""
        notion_config = NotionConfig(notion_token="test_token")
        youtube_config = YouTubeProcessorConfig(
            gemini_api_key="test_gemini_key",
            gemini_model="gemini-2.0-flash-exp",
            gemini_temperature=0.5,
            gemini_max_output_tokens=2000,
            max_retries=2,
            timeout_seconds=60
        )
        app_config = ApplicationConfig(notion=notion_config, youtube_processor=youtube_config)
        factory = ComponentFactory(app_config)
        
        # Mock the validation to avoid actual API calls
        with patch('src.youtube_notion.writers.gemini_summary_writer.GeminiSummaryWriter.validate_configuration', return_value=True):
            summary_writer = factory.create_summary_writer()
            
            assert summary_writer is not None
            assert summary_writer.api_key == "test_gemini_key"
            assert summary_writer.model == "gemini-2.0-flash-exp"
            assert summary_writer.temperature == 0.5
            assert summary_writer.max_output_tokens == 2000
            assert summary_writer.max_retries == 2
            assert summary_writer.timeout_seconds == 60
    
    def test_create_summary_writer_no_youtube_config(self):
        """Test summary writer creation fails without YouTube configuration."""
        notion_config = NotionConfig(notion_token="test_token")
        app_config = ApplicationConfig(notion=notion_config, youtube_processor=None)
        factory = ComponentFactory(app_config)
        
        with pytest.raises(ConfigurationError, match="YouTube processor configuration is required"):
            factory.create_summary_writer()
    
    def test_create_summary_writer_with_custom_chat_logger(self):
        """Test summary writer creation with custom chat logger."""
        from src.youtube_notion.utils.chat_logger import ChatLogger
        
        notion_config = NotionConfig(notion_token="test_token")
        youtube_config = YouTubeProcessorConfig(gemini_api_key="test_gemini_key")
        app_config = ApplicationConfig(notion=notion_config, youtube_processor=youtube_config)
        factory = ComponentFactory(app_config)
        
        custom_logger = ChatLogger()
        
        with patch('src.youtube_notion.writers.gemini_summary_writer.GeminiSummaryWriter.validate_configuration', return_value=True):
            summary_writer = factory.create_summary_writer(chat_logger=custom_logger)
            
            assert summary_writer.chat_logger == custom_logger
    
    def test_create_summary_writer_validation_failure(self):
        """Test summary writer creation with validation failure."""
        notion_config = NotionConfig(notion_token="test_token")
        youtube_config = YouTubeProcessorConfig(gemini_api_key="test_gemini_key")
        app_config = ApplicationConfig(notion=notion_config, youtube_processor=youtube_config)
        factory = ComponentFactory(app_config)
        
        with patch('src.youtube_notion.writers.gemini_summary_writer.GeminiSummaryWriter.validate_configuration', 
                   side_effect=ConfigurationError("Invalid API key")):
            with pytest.raises(ConfigurationError, match="Invalid API key"):
                factory.create_summary_writer()
    
    def test_create_storage_success(self):
        """Test successful storage creation."""
        notion_config = NotionConfig(
            notion_token="test_token",
            database_name="Test DB",
            parent_page_name="Test Page"
        )
        app_config = ApplicationConfig(notion=notion_config)
        factory = ComponentFactory(app_config)
        
        # Mock the Notion API client to avoid actual API calls
        with patch('src.youtube_notion.storage.notion_storage.Client') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            
            # Mock the search API call that validate_configuration makes
            mock_client.search.return_value = {
                'results': [{'id': 'test-db-id', 'title': [{'plain_text': 'Test DB'}]}]
            }
            
            storage = factory.create_storage()
            
            assert storage is not None
            assert storage.notion_token == "test_token"
            assert storage.database_name == "Test DB"
            assert storage.parent_page_name == "Test Page"
    
    def test_create_storage_validation_failure(self):
        """Test storage creation with validation failure."""
        notion_config = NotionConfig(notion_token="test_token")
        app_config = ApplicationConfig(notion=notion_config)
        factory = ComponentFactory(app_config)
        
        with patch('src.youtube_notion.storage.notion_storage.NotionStorage.validate_configuration', 
                   side_effect=ConfigurationError("Invalid token")):
            with pytest.raises(ConfigurationError, match="Invalid token"):
                factory.create_storage()
    
    def test_create_metadata_extractor_success(self):
        """Test successful metadata extractor creation."""
        notion_config = NotionConfig(notion_token="test_token")
        youtube_config = YouTubeProcessorConfig(
            gemini_api_key="test_gemini_key",
            youtube_api_key="test_youtube_key",
            timeout_seconds=30
        )
        app_config = ApplicationConfig(notion=notion_config, youtube_processor=youtube_config)
        factory = ComponentFactory(app_config)
        
        extractor = factory.create_metadata_extractor()
        
        assert extractor is not None
        assert extractor.youtube_api_key == "test_youtube_key"
        assert extractor.timeout_seconds == 30
    
    def test_create_metadata_extractor_no_youtube_config(self):
        """Test metadata extractor creation without YouTube configuration."""
        notion_config = NotionConfig(notion_token="test_token")
        app_config = ApplicationConfig(notion=notion_config, youtube_processor=None)
        factory = ComponentFactory(app_config)
        
        extractor = factory.create_metadata_extractor()
        
        assert extractor is not None
        assert extractor.youtube_api_key is None
        assert extractor.timeout_seconds == 10  # Default timeout
    
    def test_create_all_components_success(self):
        """Test successful creation of all components."""
        notion_config = NotionConfig(notion_token="test_token")
        youtube_config = YouTubeProcessorConfig(gemini_api_key="test_gemini_key")
        app_config = ApplicationConfig(notion=notion_config, youtube_processor=youtube_config)
        factory = ComponentFactory(app_config)
        
        # Mock the Notion API client to avoid actual API calls
        with patch('src.youtube_notion.storage.notion_storage.Client') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            
            # Mock the search API call that validate_configuration makes
            mock_client.search.return_value = {
                'results': [{'id': 'test-db-id', 'title': [{'plain_text': 'Test DB'}]}]
            }
            
            extractor, writer, storage = factory.create_all_components()
            
            assert extractor is not None
            assert writer is not None
            assert storage is not None
    
    def test_create_all_components_with_custom_logger(self):
        """Test creation of all components with custom chat logger."""
        from src.youtube_notion.utils.chat_logger import ChatLogger
        
        notion_config = NotionConfig(notion_token="test_token")
        youtube_config = YouTubeProcessorConfig(gemini_api_key="test_gemini_key")
        app_config = ApplicationConfig(notion=notion_config, youtube_processor=youtube_config)
        factory = ComponentFactory(app_config)
        
        custom_logger = ChatLogger()
        
        # Mock the Notion API client to avoid actual API calls
        with patch('src.youtube_notion.storage.notion_storage.Client') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            
            # Mock the search API call that validate_configuration makes
            mock_client.search.return_value = {
                'results': [{'id': 'test-db-id', 'title': [{'plain_text': 'Test DB'}]}]
            }
            
            extractor, writer, storage = factory.create_all_components(chat_logger=custom_logger)
            
            assert writer.chat_logger == custom_logger
    
    def test_validate_all_configurations_success(self):
        """Test successful validation of all configurations."""
        notion_config = NotionConfig(notion_token="test_token")
        youtube_config = YouTubeProcessorConfig(gemini_api_key="test_gemini_key")
        app_config = ApplicationConfig(notion=notion_config, youtube_processor=youtube_config)
        factory = ComponentFactory(app_config)
        
        result = factory.validate_all_configurations()
        
        assert result is True
    
    def test_validate_all_configurations_invalid_summary_writer(self):
        """Test validation failure for summary writer configuration."""
        notion_config = NotionConfig(notion_token="test_token")
        
        # The YouTubeProcessorConfig constructor validates the API key
        with pytest.raises(ValueError, match="Gemini API key is required"):
            youtube_config = YouTubeProcessorConfig(
                gemini_api_key="",  # Invalid empty key
            )
    
    def test_validate_all_configurations_invalid_storage(self):
        """Test validation failure for storage configuration."""
        # The NotionConfig constructor validates the token
        with pytest.raises(ValueError, match="Notion token is required"):
            NotionConfig(notion_token="")
    
    def test_validate_all_configurations_invalid_temperature(self):
        """Test validation failure for invalid temperature."""
        # The YouTubeProcessorConfig constructor validates the temperature
        with pytest.raises(ValueError, match="gemini_temperature must be between 0 and 2"):
            YouTubeProcessorConfig(
                gemini_api_key="test_key",
                gemini_temperature=3.0  # Invalid temperature > 2
            )
    
    def test_from_environment_success(self):
        """Test factory creation from environment variables."""
        env_vars = {
            "NOTION_TOKEN": "test_token",
            "GEMINI_API_KEY": "test_gemini_key",
            "DATABASE_NAME": "Custom DB"
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            with patch('src.youtube_notion.config.settings.load_dotenv'):
                factory = ComponentFactory.from_environment(youtube_mode=True)
                
                assert factory.config.notion.notion_token == "test_token"
                assert factory.config.youtube_processor.gemini_api_key == "test_gemini_key"
                assert factory.config.notion.database_name == "Custom DB"
    
    def test_from_environment_missing_vars(self):
        """Test factory creation from environment with missing variables."""
        with patch.dict(os.environ, {}, clear=True):
            with patch('src.youtube_notion.config.settings.load_dotenv'):
                with pytest.raises(ConfigurationError):
                    ComponentFactory.from_environment(youtube_mode=True)
    
    def test_get_configuration_summary_with_youtube(self):
        """Test configuration summary with YouTube configuration."""
        notion_config = NotionConfig(
            notion_token="test_token",
            database_name="Test DB",
            parent_page_name="Test Page"
        )
        youtube_config = YouTubeProcessorConfig(
            gemini_api_key="test_gemini_key",
            youtube_api_key="test_youtube_key",
            gemini_model="gemini-2.0-flash-exp",
            gemini_temperature=0.5,
            max_retries=5
        )
        app_config = ApplicationConfig(
            notion=notion_config,
            youtube_processor=youtube_config,
            debug=True,
            verbose=False
        )
        factory = ComponentFactory(app_config)
        
        summary = factory.get_configuration_summary()
        
        assert summary["factory_type"] == "ComponentFactory"
        assert summary["debug"] is True
        assert summary["verbose"] is False
        assert summary["notion"]["database_name"] == "Test DB"
        assert summary["notion"]["parent_page_name"] == "Test Page"
        assert summary["notion"]["token_configured"] is True
        assert summary["youtube_processor"]["gemini_api_key_configured"] is True
        assert summary["youtube_processor"]["youtube_api_key_configured"] is True
        assert summary["youtube_processor"]["gemini_model"] == "gemini-2.0-flash-exp"
        assert summary["youtube_processor"]["gemini_temperature"] == 0.5
        assert summary["youtube_processor"]["max_retries"] == 5
    
    def test_get_configuration_summary_without_youtube(self):
        """Test configuration summary without YouTube configuration."""
        notion_config = NotionConfig(notion_token="test_token")
        app_config = ApplicationConfig(notion=notion_config, youtube_processor=None)
        factory = ComponentFactory(app_config)
        
        summary = factory.get_configuration_summary()
        
        assert summary["factory_type"] == "ComponentFactory"
        assert summary["notion"]["token_configured"] is True
        assert summary["youtube_processor"] is None
    
    def test_get_configuration_summary_masks_sensitive_data(self):
        """Test that configuration summary masks sensitive data."""
        notion_config = NotionConfig(notion_token="secret_token_12345")
        youtube_config = YouTubeProcessorConfig(
            gemini_api_key="secret_gemini_key_67890",
            youtube_api_key="secret_youtube_key_abcde"
        )
        app_config = ApplicationConfig(notion=notion_config, youtube_processor=youtube_config)
        factory = ComponentFactory(app_config)
        
        summary = factory.get_configuration_summary()
        
        # Check that actual keys are not in the summary
        summary_str = str(summary)
        assert "secret_token_12345" not in summary_str
        assert "secret_gemini_key_67890" not in summary_str
        assert "secret_youtube_key_abcde" not in summary_str
        
        # Check that boolean flags indicate presence
        assert summary["notion"]["token_configured"] is True
        assert summary["youtube_processor"]["gemini_api_key_configured"] is True
        assert summary["youtube_processor"]["youtube_api_key_configured"] is True
    
    def test_factory_validation_methods(self):
        """Test individual validation methods."""
        notion_config = NotionConfig(notion_token="test_token")
        youtube_config = YouTubeProcessorConfig(gemini_api_key="test_gemini_key")
        app_config = ApplicationConfig(notion=notion_config, youtube_processor=youtube_config)
        factory = ComponentFactory(app_config)
        
        # Test individual validation methods don't raise exceptions
        factory._validate_factory_configuration()
        factory._validate_summary_writer_config()
        factory._validate_storage_config()
        factory._validate_metadata_extractor_config()
    
    def test_factory_validation_invalid_gemini_config(self):
        """Test factory validation with invalid Gemini configuration."""
        notion_config = NotionConfig(notion_token="test_token")
        
        # Test that invalid temperature raises ValueError during config creation
        with pytest.raises(ValueError, match="gemini_temperature must be between 0 and 2"):
            YouTubeProcessorConfig(
                gemini_api_key="test_key",
                gemini_temperature=-1.0  # Invalid temperature
            )
    
    def test_component_creation_error_handling(self):
        """Test error handling during component creation."""
        notion_config = NotionConfig(notion_token="test_token")
        youtube_config = YouTubeProcessorConfig(gemini_api_key="test_gemini_key")
        app_config = ApplicationConfig(notion=notion_config, youtube_processor=youtube_config)
        factory = ComponentFactory(app_config)
        
        # Test summary writer creation error
        with patch('src.youtube_notion.writers.gemini_summary_writer.GeminiSummaryWriter.__init__', 
                   side_effect=Exception("Unexpected error")):
            with pytest.raises(ConfigurationError, match="Failed to create summary writer"):
                factory.create_summary_writer()
        
        # Test storage creation error
        with patch('src.youtube_notion.storage.notion_storage.NotionStorage.__init__', 
                   side_effect=Exception("Unexpected error")):
            with pytest.raises(ConfigurationError, match="Failed to create storage backend"):
                factory.create_storage()
        
        # Test metadata extractor creation error
        with patch('src.youtube_notion.extractors.video_metadata_extractor.VideoMetadataExtractor.__init__', 
                   side_effect=Exception("Unexpected error")):
            with pytest.raises(ConfigurationError, match="Failed to create metadata extractor"):
                factory.create_metadata_extractor()