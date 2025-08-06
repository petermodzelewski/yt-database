"""
Configuration management for YouTube to Notion integration.

This module provides centralized configuration management with validation,
default values, and environment variable handling for the application.
"""

import os
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from dotenv import load_dotenv

from ..utils.exceptions import ConfigurationError


from .constants import DEFAULT_SUMMARY_PROMPT


@dataclass
class YouTubeProcessorConfig:
    """Configuration for YouTube video processing."""
    
    # API Keys
    gemini_api_key: str
    youtube_api_key: Optional[str] = None
    
    # Processing Configuration
    default_prompt: str = DEFAULT_SUMMARY_PROMPT
    max_retries: int = 3
    timeout_seconds: int = 120
    
    # Gemini API Configuration
    gemini_model: str = "gemini-2.0-flash-exp"
    gemini_temperature: float = 0.1
    gemini_max_output_tokens: int = 4000
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        if not self.gemini_api_key:
            raise ValueError("Gemini API key is required")
        
        if self.max_retries < 0:
            raise ValueError("max_retries must be non-negative")
        
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        
        if self.gemini_temperature < 0 or self.gemini_temperature > 2:
            raise ValueError("gemini_temperature must be between 0 and 2")
        
        if self.gemini_max_output_tokens <= 0:
            raise ValueError("gemini_max_output_tokens must be positive")


@dataclass
class NotionConfig:
    """Configuration for Notion database operations."""
    
    # API Configuration
    notion_token: str
    
    # Database Configuration
    database_name: str = "YT Summaries"
    parent_page_name: str = "YouTube Knowledge Base"
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        if not self.notion_token:
            raise ValueError("Notion token is required")
        
        if not self.database_name:
            raise ValueError("Database name cannot be empty")
        
        if not self.parent_page_name:
            raise ValueError("Parent page name cannot be empty")


@dataclass
class ApplicationConfig:
    """Main application configuration."""
    
    # Component configurations
    notion: NotionConfig
    youtube_processor: Optional[YouTubeProcessorConfig] = None
    
    # Application settings
    debug: bool = False
    verbose: bool = False
    
    @classmethod
    def from_environment(cls, youtube_mode: bool = False) -> 'ApplicationConfig':
        """
        Create configuration from environment variables.
        
        Args:
            youtube_mode: Whether YouTube processing is enabled
            
        Returns:
            ApplicationConfig: Configured application settings
            
        Raises:
            ConfigurationError: If required environment variables are missing or invalid
        """
        # Load environment variables
        load_dotenv()
        
        # Validate and collect environment variables
        env_vars = validate_environment_variables(youtube_mode)
        
        # Create Notion configuration
        notion_config = NotionConfig(
            notion_token=env_vars["NOTION_TOKEN"],
            database_name=env_vars.get("DATABASE_NAME", "YT Summaries"),
            parent_page_name=env_vars.get("PARENT_PAGE_NAME", "YouTube Knowledge Base")
        )
        
        # Create YouTube processor configuration if needed
        youtube_config = None
        if youtube_mode:
            youtube_config = YouTubeProcessorConfig(
                gemini_api_key=env_vars["GEMINI_API_KEY"],
                youtube_api_key=env_vars.get("YOUTUBE_API_KEY"),
                default_prompt=env_vars.get("DEFAULT_SUMMARY_PROMPT", DEFAULT_SUMMARY_PROMPT),
                max_retries=int(env_vars.get("YOUTUBE_PROCESSOR_MAX_RETRIES", "3")),
                timeout_seconds=int(env_vars.get("YOUTUBE_PROCESSOR_TIMEOUT", "120")),
                gemini_model=env_vars.get("GEMINI_MODEL", "gemini-2.0-flash-exp"),
                gemini_temperature=float(env_vars.get("GEMINI_TEMPERATURE", "0.1")),
                gemini_max_output_tokens=int(env_vars.get("GEMINI_MAX_OUTPUT_TOKENS", "4000"))
            )
        
        # Create application configuration
        return cls(
            notion=notion_config,
            youtube_processor=youtube_config,
            debug=env_vars.get("DEBUG", "false").lower() == "true",
            verbose=env_vars.get("VERBOSE", "false").lower() == "true"
        )





def validate_environment_variables(youtube_mode: bool = False) -> Dict[str, str]:
    """
    Validate required and optional environment variables.
    
    Args:
        youtube_mode: Whether YouTube processing mode is enabled
        
    Returns:
        dict: Dictionary of validated environment variables
        
    Raises:
        ConfigurationError: If required variables are missing or invalid
    """
    env_vars = {}
    missing_vars = []
    invalid_vars = {}
    
    # Always required variables
    required_vars = ["NOTION_TOKEN"]
    
    # Required for YouTube processing mode
    if youtube_mode:
        required_vars.extend(["GEMINI_API_KEY"])
    
    # Check required variables
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing_vars.append(var)
        else:
            env_vars[var] = value
    
    # Optional variables with validation
    optional_vars = {
        "DATABASE_NAME": str,
        "PARENT_PAGE_NAME": str,
        "YOUTUBE_API_KEY": str,
        "DEFAULT_SUMMARY_PROMPT": str,
        "YOUTUBE_PROCESSOR_MAX_RETRIES": int,
        "YOUTUBE_PROCESSOR_TIMEOUT": int,
        "GEMINI_MODEL": str,
        "GEMINI_TEMPERATURE": float,
        "GEMINI_MAX_OUTPUT_TOKENS": int,
        "DEBUG": str,
        "VERBOSE": str
    }
    
    # Validate optional variables
    for var, var_type in optional_vars.items():
        value = os.getenv(var)
        if value is not None:
            try:
                if var_type == int:
                    parsed_value = int(value)
                    if var == "YOUTUBE_PROCESSOR_MAX_RETRIES" and parsed_value < 0:
                        invalid_vars[var] = "must be non-negative"
                    elif var == "YOUTUBE_PROCESSOR_TIMEOUT" and parsed_value <= 0:
                        invalid_vars[var] = "must be positive"
                    elif var == "GEMINI_MAX_OUTPUT_TOKENS" and parsed_value <= 0:
                        invalid_vars[var] = "must be positive"
                    else:
                        env_vars[var] = value
                elif var_type == float:
                    parsed_value = float(value)
                    if var == "GEMINI_TEMPERATURE" and (parsed_value < 0 or parsed_value > 2):
                        invalid_vars[var] = "must be between 0 and 2"
                    else:
                        env_vars[var] = value
                elif var_type == str:
                    if var in ["DEBUG", "VERBOSE"] and value.lower() not in ["true", "false"]:
                        invalid_vars[var] = "must be 'true' or 'false'"
                    else:
                        env_vars[var] = value
            except ValueError:
                invalid_vars[var] = f"must be a valid {var_type.__name__}"
    
    # Raise error if there are issues
    if missing_vars or invalid_vars:
        error_message = "Configuration validation failed"
        raise ConfigurationError(error_message, missing_vars, invalid_vars)
    
    return env_vars


def get_configuration_help(youtube_mode: bool = False) -> str:
    """
    Get help text for configuration setup.
    
    Args:
        youtube_mode: Whether to include YouTube-specific configuration
        
    Returns:
        str: Configuration help text
    """
    help_text = """
Environment Variable Configuration:

REQUIRED VARIABLES:
  NOTION_TOKEN              Your Notion integration token
                            Get from: https://www.notion.so/my-integrations
"""
    
    if youtube_mode:
        help_text += """
  GEMINI_API_KEY            Your Google Gemini API key
                            Get from: https://aistudio.google.com/app/apikey
"""
    
    help_text += """
OPTIONAL VARIABLES:
  DATABASE_NAME             Name of the Notion database (default: "YT Summaries")
  PARENT_PAGE_NAME          Name of the parent page (default: "Knowledge Base")
"""
    
    if youtube_mode:
        help_text += """
  YOUTUBE_API_KEY           YouTube Data API key (optional, enables better metadata)
                            Get from: https://console.developers.google.com/
  
  DEFAULT_SUMMARY_PROMPT    Custom prompt for AI summary generation
  YOUTUBE_PROCESSOR_MAX_RETRIES    Maximum API retry attempts (default: 3)
  YOUTUBE_PROCESSOR_TIMEOUT        API timeout in seconds (default: 120)
  
  GEMINI_MODEL              Gemini model to use (default: "gemini-2.0-flash-exp")
  GEMINI_TEMPERATURE        AI temperature 0-2 (default: 0.1)
  GEMINI_MAX_OUTPUT_TOKENS  Maximum output tokens (default: 4000)
"""
    
    help_text += """
  DEBUG                     Enable debug mode (true/false, default: false)
  VERBOSE                   Enable verbose output (true/false, default: false)

SETUP:
  1. Copy .env.example to .env
  2. Edit .env and add your API keys
  3. Optionally customize other settings
"""
    
    return help_text


def print_configuration_error(error: ConfigurationError, youtube_mode: bool = False):
    """
    Print a user-friendly configuration error message.
    
    Args:
        error: Configuration error to display
        youtube_mode: Whether YouTube mode was requested
    """
    print("Error: Configuration validation failed")
    print()
    
    if error.missing_vars:
        print("Missing required environment variables:")
        for var in error.missing_vars:
            print(f"  - {var}")
        print()
    
    if error.invalid_vars:
        print("Invalid environment variable values:")
        for var, reason in error.invalid_vars.items():
            print(f"  - {var}: {reason}")
        print()
    
    print(get_configuration_help(youtube_mode))


def load_custom_prompt(prompt_file: Optional[str] = None) -> str:
    """
    Load custom prompt from file or environment variable.
    
    Args:
        prompt_file: Path to prompt file (optional)
        
    Returns:
        str: Custom prompt or default prompt if not found
    """
    # Try to load from file first
    if prompt_file and os.path.exists(prompt_file):
        try:
            with open(prompt_file, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except Exception:
            pass  # Fall back to environment variable or default
    
    # Try environment variable
    env_prompt = os.getenv("DEFAULT_SUMMARY_PROMPT")
    if env_prompt:
        return env_prompt
    
    # Return default prompt
    return DEFAULT_SUMMARY_PROMPT