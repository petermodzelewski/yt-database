"""
Summary writer implementations for the YouTube-to-Notion integration system.

This module provides concrete implementations of the SummaryWriter interface
for different AI providers and summary generation strategies.
"""

from .gemini_summary_writer import GeminiSummaryWriter

__all__ = ['GeminiSummaryWriter']