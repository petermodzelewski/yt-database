# Product Overview

YouTube to Notion Database Integration is a Python application that automatically processes YouTube video summaries and adds them to a Notion database with rich formatting and interactive features.

## Core Features

- **YouTube Integration**: Processes video metadata (title, URL, channel, cover image)
- **Smart Timestamps**: Converts timestamps like `[8:05]` or `[8:05-8:24]` to clickable YouTube links
- **Markdown to Notion**: Converts markdown summaries to Notion's rich text format
- **Rich Formatting**: Supports headers, bullet points, numbered lists, bold, and italic text
- **Embedded Videos**: Automatically embeds YouTube videos at the top of each page
- **Cover Images**: Automatically adds video thumbnails as page covers

## Target Use Case

The application is designed for users who want to organize YouTube learning content in Notion databases, creating structured knowledge bases with clickable timestamps that jump to specific video moments.

## Database Requirements

- Notion database named "YT Summaries" in a page called "YouTube Knowledge Base"
- Required properties: Title (Title), Video URL (URL), Channel (Rich Text), Tags (Multi-select, optional)
- Requires Notion integration token with database access