"""
Component factory for dependency injection.

This module provides a factory class for creating configured components
with proper dependency injection and validation.
"""

from typing import Optional
from ..interfaces.summary_writer import SummaryWriter
from ..interfaces.storage import Storage
from ..extractors.video_metadata_extractor import VideoMetadataExtractor
from ..writers.gemini_summary_writer import GeminiSummaryWriter
from ..storage.notion_storage import NotionStorage
from ..utils.chat_logger import ChatLogger
from ..utils.exceptions import ConfigurationError
from .settings import ApplicationConfig, YouTubeProcessorConfig, NotionConfig


class ComponentFactory:
    """
    Factory for creating configured components with dependency injection.
    
    This factory provides a centralized way to create and configure all
    application components based on the application configuration. It
    supports different implementations and validates configurations.
    """
    
    def __init__(self, config: ApplicationConfig):
        """
        Initialize the component factory.
        
        Args:
            config: Application configuration containing all component settings
            
        Raises:
            ConfigurationError: If configuration is invalid
        """
        if not config:
            raise ConfigurationError("Application configuration is required")
        
        self.config = config
        self._validate_factory_configuration()
    
    def create_summary_writer(self, chat_logger: Optional[ChatLogger] = None) -> SummaryWriter:
        """
        Create a configured summary writer implementation.
        
        Currently supports:
        - GeminiSummaryWriter: Uses Google Gemini AI for summary generation
        
        Args:
            chat_logger: Optional chat logger instance (creates new if None)
            
        Returns:
            SummaryWriter: Configured summary writer instance
            
        Raises:
            ConfigurationError: If summary writer configuration is invalid
        """
        if not self.config.youtube_processor:
            raise ConfigurationError(
                "YouTube processor configuration is required for summary writer creation"
            )
        
        youtube_config = self.config.youtube_processor
        
        try:
            # Create GeminiSummaryWriter with configuration
            summary_writer = GeminiSummaryWriter(
                api_key=youtube_config.gemini_api_key,
                model=youtube_config.gemini_model,
                temperature=youtube_config.gemini_temperature,
                max_output_tokens=youtube_config.gemini_max_output_tokens,
                default_prompt=youtube_config.default_prompt,
                max_retries=youtube_config.max_retries,
                timeout_seconds=youtube_config.timeout_seconds,
                chat_logger=chat_logger
            )
            
            # Validate the created summary writer
            summary_writer.validate_configuration()
            
            return summary_writer
            
        except Exception as e:
            if isinstance(e, ConfigurationError):
                raise
            raise ConfigurationError(
                f"Failed to create summary writer: {str(e)}",
                details=f"Error type: {type(e).__name__}"
            )
    
    def create_storage(self) -> Storage:
        """
        Create a configured storage backend implementation.
        
        Currently supports:
        - NotionStorage: Stores video summaries in Notion databases
        
        Returns:
            Storage: Configured storage backend instance
            
        Raises:
            ConfigurationError: If storage configuration is invalid
        """
        if not self.config.notion:
            raise ConfigurationError(
                "Notion configuration is required for storage creation"
            )
        
        notion_config = self.config.notion
        
        try:
            # Get retry configuration from YouTube processor config if available
            max_retries = 3  # Default
            timeout_seconds = 30  # Default
            
            if self.config.youtube_processor:
                max_retries = self.config.youtube_processor.max_retries
                timeout_seconds = self.config.youtube_processor.timeout_seconds
            
            # Create NotionStorage with configuration
            storage = NotionStorage(
                notion_token=notion_config.notion_token,
                database_name=notion_config.database_name,
                parent_page_name=notion_config.parent_page_name,
                max_retries=max_retries,
                timeout_seconds=timeout_seconds
            )
            
            # Validate the created storage backend
            storage.validate_configuration()
            
            return storage
            
        except Exception as e:
            if isinstance(e, ConfigurationError):
                raise
            raise ConfigurationError(
                f"Failed to create storage backend: {str(e)}",
                details=f"Error type: {type(e).__name__}"
            )
    
    def create_metadata_extractor(self) -> VideoMetadataExtractor:
        """
        Create a configured metadata extractor implementation.
        
        Currently supports:
        - VideoMetadataExtractor: Extracts metadata from YouTube videos
        
        Returns:
            VideoMetadataExtractor: Configured metadata extractor instance
            
        Raises:
            ConfigurationError: If metadata extractor configuration is invalid
        """
        try:
            # Get YouTube API key if available
            youtube_api_key = None
            if self.config.youtube_processor:
                youtube_api_key = self.config.youtube_processor.youtube_api_key
            
            # Get timeout from configuration or use default
            timeout_seconds = 10  # Default timeout
            if self.config.youtube_processor:
                timeout_seconds = self.config.youtube_processor.timeout_seconds
            
            # Create VideoMetadataExtractor with configuration
            extractor = VideoMetadataExtractor(
                youtube_api_key=youtube_api_key,
                timeout_seconds=timeout_seconds
            )
            
            return extractor
            
        except Exception as e:
            if isinstance(e, ConfigurationError):
                raise
            raise ConfigurationError(
                f"Failed to create metadata extractor: {str(e)}",
                details=f"Error type: {type(e).__name__}"
            )
    
    def create_all_components(self, chat_logger: Optional[ChatLogger] = None) -> tuple[VideoMetadataExtractor, SummaryWriter, Storage]:
        """
        Create all configured components for video processing.
        
        This is a convenience method that creates all three main components
        needed for video processing in the correct order.
        
        Args:
            chat_logger: Optional chat logger instance (creates new if None)
            
        Returns:
            tuple: (metadata_extractor, summary_writer, storage) components
            
        Raises:
            ConfigurationError: If any component configuration is invalid
        """
        try:
            # Create components in dependency order
            metadata_extractor = self.create_metadata_extractor()
            summary_writer = self.create_summary_writer(chat_logger)
            storage = self.create_storage()
            
            return metadata_extractor, summary_writer, storage
            
        except ConfigurationError:
            raise
        except Exception as e:
            raise ConfigurationError(
                f"Failed to create all components: {str(e)}",
                details=f"Error type: {type(e).__name__}"
            )
    
    def validate_all_configurations(self) -> bool:
        """
        Validate all component configurations without creating instances.
        
        This method performs validation checks for all components that would
        be created by this factory, without actually instantiating them.
        
        Returns:
            bool: True if all configurations are valid
            
        Raises:
            ConfigurationError: If any configuration is invalid
        """
        try:
            # Validate factory configuration
            self._validate_factory_configuration()
            
            # Validate individual component configurations
            self._validate_summary_writer_config()
            self._validate_storage_config()
            self._validate_metadata_extractor_config()
            
            return True
            
        except ConfigurationError:
            raise
        except Exception as e:
            raise ConfigurationError(
                f"Configuration validation failed: {str(e)}",
                details=f"Error type: {type(e).__name__}"
            )
    
    def _validate_factory_configuration(self):
        """
        Validate the factory's base configuration.
        
        Raises:
            ConfigurationError: If factory configuration is invalid
        """
        if not isinstance(self.config, ApplicationConfig):
            raise ConfigurationError(
                "Invalid application configuration type",
                details=f"Expected ApplicationConfig, got {type(self.config).__name__}"
            )
        
        # Validate that we have at least Notion configuration
        if not self.config.notion:
            raise ConfigurationError(
                "Notion configuration is required"
            )
    
    def _validate_summary_writer_config(self):
        """
        Validate summary writer configuration.
        
        Raises:
            ConfigurationError: If summary writer configuration is invalid
        """
        if not self.config.youtube_processor:
            raise ConfigurationError(
                "YouTube processor configuration is required for summary writer"
            )
        
        youtube_config = self.config.youtube_processor
        
        # Validate required fields
        if not youtube_config.gemini_api_key:
            raise ConfigurationError("Gemini API key is required for summary writer")
        
        # Validate configuration values
        if youtube_config.gemini_temperature < 0 or youtube_config.gemini_temperature > 2:
            raise ConfigurationError("Gemini temperature must be between 0 and 2")
        
        if youtube_config.gemini_max_output_tokens <= 0:
            raise ConfigurationError("Gemini max output tokens must be positive")
        
        if youtube_config.max_retries < 0:
            raise ConfigurationError("Max retries must be non-negative")
        
        if youtube_config.timeout_seconds <= 0:
            raise ConfigurationError("Timeout seconds must be positive")
    
    def _validate_storage_config(self):
        """
        Validate storage configuration.
        
        Raises:
            ConfigurationError: If storage configuration is invalid
        """
        notion_config = self.config.notion
        
        # Validate required fields
        if not notion_config.notion_token:
            raise ConfigurationError("Notion token is required for storage")
        
        if not notion_config.database_name:
            raise ConfigurationError("Database name is required for storage")
        
        if not notion_config.parent_page_name:
            raise ConfigurationError("Parent page name is required for storage")
    
    def _validate_metadata_extractor_config(self):
        """
        Validate metadata extractor configuration.
        
        Raises:
            ConfigurationError: If metadata extractor configuration is invalid
        """
        # Metadata extractor has minimal configuration requirements
        # YouTube API key is optional, timeout has a default value
        
        if self.config.youtube_processor:
            if self.config.youtube_processor.timeout_seconds <= 0:
                raise ConfigurationError("Timeout seconds must be positive for metadata extractor")
    
    @classmethod
    def from_environment(cls, youtube_mode: bool = False) -> 'ComponentFactory':
        """
        Create a component factory from environment variables.
        
        This is a convenience method that loads configuration from environment
        variables and creates a factory instance.
        
        Args:
            youtube_mode: Whether YouTube processing mode is enabled
            
        Returns:
            ComponentFactory: Factory instance configured from environment
            
        Raises:
            ConfigurationError: If environment configuration is invalid
        """
        try:
            # Load configuration from environment
            config = ApplicationConfig.from_environment(youtube_mode)
            
            # Create and return factory
            return cls(config)
            
        except Exception as e:
            if isinstance(e, ConfigurationError):
                raise
            raise ConfigurationError(
                f"Failed to create factory from environment: {str(e)}",
                details=f"Error type: {type(e).__name__}"
            )
    
    def get_configuration_summary(self) -> dict:
        """
        Get a summary of the current configuration.
        
        This method returns a dictionary containing key configuration
        information for debugging and validation purposes.
        
        Returns:
            dict: Configuration summary with sensitive data masked
        """
        summary = {
            "factory_type": "ComponentFactory",
            "debug": self.config.debug,
            "verbose": self.config.verbose,
            "notion": {
                "database_name": self.config.notion.database_name,
                "parent_page_name": self.config.notion.parent_page_name,
                "token_configured": bool(self.config.notion.notion_token)
            }
        }
        
        if self.config.youtube_processor:
            summary["youtube_processor"] = {
                "gemini_api_key_configured": bool(self.config.youtube_processor.gemini_api_key),
                "youtube_api_key_configured": bool(self.config.youtube_processor.youtube_api_key),
                "gemini_model": self.config.youtube_processor.gemini_model,
                "gemini_temperature": self.config.youtube_processor.gemini_temperature,
                "gemini_max_output_tokens": self.config.youtube_processor.gemini_max_output_tokens,
                "max_retries": self.config.youtube_processor.max_retries,
                "timeout_seconds": self.config.youtube_processor.timeout_seconds
            }
        else:
            summary["youtube_processor"] = None
        
        return summary