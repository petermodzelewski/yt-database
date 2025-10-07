"""
Multi-storage backend implementation.

This module provides a storage backend that can delegate to multiple
other storage backends, enabling saving summaries to multiple destinations
at once (e.g., Notion and local file system).
"""

from typing import Dict, Any, Optional, List

from ..interfaces.storage import Storage
from ..utils.exceptions import StorageError, ConfigurationError


class MultiStorage(Storage):
    """
    A storage backend that delegates to multiple other storage backends.

    This class allows for storing video summaries in multiple locations
    simultaneously by composing a list of other storage implementations.
    """

    def __init__(self, storages: List[Storage]):
        """
        Initialize the multi-storage backend.

        Args:
            storages: A list of configured storage backend instances
        """
        self.storages = storages

    def store_video_summary(self, video_data: Dict[str, Any]) -> bool:
        """
        Store processed video data in all configured storage backends.

        This method iterates through all storage backends and calls their
        `store_video_summary` method. If any of them fail, it collects the
        errors and raises a single StorageError at the end.

        Args:
            video_data: Processed video data to be stored

        Returns:
            bool: True if all backends succeed, otherwise raises an exception

        Raises:
            StorageError: If one or more storage backends fail
        """
        success = True
        errors = []

        for storage in self.storages:
            try:
                storage.store_video_summary(video_data)
            except Exception as e:
                success = False
                storage_name = type(storage).__name__
                errors.append(f" - {storage_name}: {str(e)}")

        if not success:
            error_details = "\n".join(errors)
            raise StorageError(
                "One or more storage backends failed",
                details=f"The following errors occurred:\n{error_details}"
            )

        return True

    def validate_configuration(self) -> bool:
        """
        Validate the configuration of all contained storage backends.

        Returns:
            bool: True if all configurations are valid

        Raises:
            ConfigurationError: If any storage backend has an invalid configuration
        """
        for storage in self.storages:
            storage.validate_configuration()
        return True

    def find_target_location(self) -> Optional[str]:
        """
        Find and return target locations from all storage backends.

        Returns a comma-separated string of all discovered locations.

        Returns:
            Optional[str]: A string containing all target locations, or None if none found
        """
        locations = []
        for storage in self.storages:
            location = storage.find_target_location()
            if location:
                locations.append(location)

        return ", ".join(locations) if locations else None