"""
Storage backend implementations for the YouTube-to-Notion integration system.

This module provides concrete implementations of the Storage interface
for different storage backends.
"""

from .notion_storage import NotionStorage

__all__ = ['NotionStorage']