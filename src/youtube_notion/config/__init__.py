"""
Configuration module for YouTube to Notion integration.

This module provides centralized configuration management with validation,
default values, and environment variable handling.
"""

from .settings import (
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

__all__ = [
    'ApplicationConfig',
    'NotionConfig', 
    'YouTubeProcessorConfig',
    'ConfigurationError',
    'DEFAULT_SUMMARY_PROMPT',
    'validate_environment_variables',
    'get_configuration_help',
    'print_configuration_error',
    'load_custom_prompt'
]