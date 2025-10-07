"""
File system storage backend implementation.

This module provides a concrete implementation of the Storage interface
for saving video summaries as markdown files on the local file system.
"""

import os
from typing import Dict, Any, Optional

from ..interfaces.storage import Storage
from ..utils.exceptions import StorageError, ConfigurationError


class FileStorage(Storage):
    """
    Storage backend for saving video summaries to the local file system.

    This class handles saving the original markdown summary to a specified
    directory, with options for organizing files in subdirectories based on
    the video's channel.
    """

    def __init__(self, output_dir: str, use_channel_subdirectory: bool = True):
        """
        Initialize the file system storage backend.

        Args:
            output_dir: The root directory to save markdown files
            use_channel_subdirectory: Whether to create subdirectories for each channel

        Raises:
            ConfigurationError: If configuration parameters are invalid
        """
        if not output_dir or not output_dir.strip():
            raise ConfigurationError("Output directory is required and cannot be empty")

        self.output_dir = os.path.expanduser(output_dir.strip())
        self.use_channel_subdirectory = use_channel_subdirectory

    def store_video_summary(self, video_data: Dict[str, Any]) -> bool:
        """
        Save the generated markdown summary to a local file.

        The filename is sanitized to be file-system friendly.

        Args:
            video_data: Processed video data containing:
                - Title: Video title
                - Channel: Channel name
                - Summary: Generated markdown summary

        Returns:
            bool: True if successful, False otherwise

        Raises:
            StorageError: If the storage operation fails
        """
        try:
            # Validate required fields
            required_fields = ['Title', 'Channel', 'Summary']
            for field in required_fields:
                if field not in video_data:
                    raise StorageError(f"Missing required field: {field}")

            title = video_data['Title']
            channel = video_data['Channel']
            summary = video_data['Summary']

            # Determine target directory
            target_dir = self.output_dir
            if self.use_channel_subdirectory:
                sanitized_channel = self._sanitize_filename(channel)
                target_dir = os.path.join(self.output_dir, sanitized_channel)

            # Create directory if it doesn't exist
            if not os.path.exists(target_dir):
                os.makedirs(target_dir, exist_ok=True)

            # Sanitize filename and create file path
            sanitized_title = self._sanitize_filename(title)
            file_path = os.path.join(target_dir, f"{sanitized_title}.md")

            # Write summary to file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(summary)

            return True

        except Exception as e:
            raise StorageError(f"Failed to save summary to file: {str(e)}", details=str(e))

    def validate_configuration(self) -> bool:
        """
        Validate that the storage backend is properly configured.

        Checks if the output directory is writable.

        Returns:
            bool: True if configuration is valid

        Raises:
            ConfigurationError: If configuration validation fails
        """
        try:
            # Check if output directory is provided
            if not self.output_dir:
                raise ConfigurationError("Output directory is required")

            # Check if output directory exists and is writable
            if os.path.exists(self.output_dir):
                if not os.path.isdir(self.output_dir):
                    raise ConfigurationError(f"Output path '{self.output_dir}' exists but is not a directory")
                if not os.access(self.output_dir, os.W_OK):
                    raise ConfigurationError(f"Output directory '{self.output_dir}' is not writable")
            else:
                # Try to create the directory to check for write permissions
                try:
                    os.makedirs(self.output_dir, exist_ok=True)
                except OSError as e:
                    raise ConfigurationError(f"Could not create output directory '{self.output_dir}': {e}")

            return True

        except ConfigurationError:
            raise
        except Exception as e:
            raise ConfigurationError(f"File storage configuration validation failed: {str(e)}")

    def find_target_location(self) -> Optional[str]:
        """
        Return the root output directory as the target location.

        Returns:
            str: The root output directory path
        """
        return self.output_dir

    def _sanitize_filename(self, name: str) -> str:
        """
        Sanitize a string to be a valid filename.

        Removes or replaces characters that are invalid in file systems.

        Args:
            name: The string to sanitize

        Returns:
            str: A sanitized, file-system-friendly string
        """
        # Replace invalid characters with an underscore
        invalid_chars = r'<>:"/\|?*"'
        translation_table = str.maketrans(invalid_chars, '_' * len(invalid_chars))
        name = name.translate(translation_table)

        # Replace multiple spaces with a single space
        name = ' '.join(name.split())

        # Limit length to avoid issues with file systems
        max_length = 200
        if len(name) > max_length:
            name = name[:max_length]

        return name.strip()