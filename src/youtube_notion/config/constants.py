"""
Configuration constants for YouTube to Notion integration.

This module contains constants used throughout the application to avoid
circular import issues.
"""

# Default prompt for Gemini API summary generation
DEFAULT_SUMMARY_PROMPT = """
Condense all the practical information and examples regarding the video content in form of an article. 
Don't miss any details but keep the article as short and direct as possible. 
Put timestamp(s) to fragments of the video next to each fact you got from the video.
Format the output in markdown with proper headers, bullet points, and formatting.
Use timestamps in the format [MM:SS] or [MM:SS-MM:SS] for time ranges.
"""

# Maximum video duration in seconds that can be processed in a single chunk
MAX_VIDEO_DURATION_SECONDS = 2700  # 45 minutes