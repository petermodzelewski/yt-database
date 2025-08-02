# Product Overview

YouTube to Notion Database Integration is a Python application that automatically processes YouTube videos and adds AI-generated summaries to a Notion database with proper markdown formatting and rich text conversion.

## Core Features

- **Dynamic YouTube Processing**: Process any YouTube video URL with AI-generated summaries using Google Gemini
- **Embedded Videos**: Automatically embeds YouTube videos at the top of each page
- **Smart Timestamps**: Converts timestamps like `[8:05]` or `[8:05-8:24]` to clickable YouTube links
- **Markdown to Notion**: Converts markdown summaries to Notion's rich text format
- **Rich Formatting**: Supports headers, bullet points, numbered lists, bold, and italic text
- **Cover Images**: Automatically adds video thumbnails as page covers
- **Dual Mode Operation**: Supports both example data mode and live YouTube processing
- **Robust Error Handling**: Comprehensive error handling with retry logic and graceful fallbacks

## Operation Modes

1. **YouTube URL Processing Mode**: Process real YouTube videos with AI-generated summaries (requires GEMINI_API_KEY)
2. **Example Data Mode**: Uses pre-built example data for testing and demonstration (default mode)

## Target Users

Developers and content creators who want to organize YouTube learning content in Notion databases with AI-generated summaries and proper formatting.