from typing import Optional
from .settings import ApplicationConfig, print_configuration_error
from ..utils.exceptions import ConfigurationError

def load_application_config(youtube_mode: bool = False) -> Optional[ApplicationConfig]:
    """
    Load and validate application configuration.

    Args:
        youtube_mode: Whether YouTube processing mode is enabled

    Returns:
        ApplicationConfig: Validated configuration or None if validation fails
    """
    try:
        return ApplicationConfig.from_environment(youtube_mode)
    except ConfigurationError as e:
        print_configuration_error(e, youtube_mode)
        return None
