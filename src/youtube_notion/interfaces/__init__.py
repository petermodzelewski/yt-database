"""
Abstract interfaces for the YouTube-to-Notion integration system.

This module provides the core abstractions that enable pluggable implementations
for summary generation and storage backends.
"""

from .summary_writer import SummaryWriter
from .storage import Storage

__all__ = ['SummaryWriter', 'Storage']