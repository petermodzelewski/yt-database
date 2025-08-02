# Requirements Document

## Introduction

This feature enhances the existing YouTube-Notion integration by replacing the static example data with dynamic processing of actual YouTube videos. The system will accept a YouTube URL, extract video metadata, generate AI-powered summaries using Google Gemini, and return structured data compatible with the existing Notion database integration.

## Requirements

### Requirement 1

**User Story:** As a user, I want to provide a YouTube URL and get an AI-generated summary with timestamps, so that I can automatically create rich Notion pages from any YouTube video.

#### Acceptance Criteria

1. WHEN a user provides a valid YouTube URL THEN the system SHALL extract the video ID from the URL
2. WHEN the system processes a YouTube video THEN it SHALL retrieve the video title from YouTube's metadata
3. WHEN the system processes a YouTube video THEN it SHALL retrieve the channel name from YouTube's metadata
4. WHEN the system processes a YouTube video THEN it SHALL construct the correct thumbnail URL using the video ID
5. WHEN the system generates content THEN it SHALL use Google Gemini API to create a markdown summary with timestamps
6. WHEN Gemini generates the summary THEN the system SHALL format timestamps in the expected format [MM:SS] or [MM:SS-MM:SS]

### Requirement 2

**User Story:** As a user, I want the AI-generated content to maintain the same structure as the existing example data, so that it works seamlessly with the current Notion integration.

#### Acceptance Criteria

1. WHEN the system processes a YouTube video THEN it SHALL return data with the same structure as example_data.py
2. WHEN the system constructs the response THEN it SHALL include title, video_url, channel, cover_image, and summary fields
3. WHEN the system generates the summary THEN it SHALL ensure the content is in markdown format compatible with the existing markdown converter
4. WHEN the system processes video metadata THEN it SHALL handle missing or unavailable data gracefully

### Requirement 3

**User Story:** As a developer, I want proper error handling and validation for YouTube URLs and API calls, so that the system is robust and provides clear feedback when issues occur.

#### Acceptance Criteria

1. WHEN an invalid YouTube URL is provided THEN the system SHALL return a clear error message
2. WHEN the YouTube video is private or unavailable THEN the system SHALL handle the error gracefully
3. WHEN the Gemini API is unavailable or returns an error THEN the system SHALL provide appropriate error handling
4. WHEN API rate limits are exceeded THEN the system SHALL provide informative error messages
5. WHEN required environment variables are missing THEN the system SHALL validate and report missing configuration

### Requirement 4

**User Story:** As a user, I want the system to be configurable for different types of content extraction, so that I can customize the AI prompts for different use cases.

#### Acceptance Criteria

1. WHEN the system calls Gemini API THEN it SHALL use a configurable prompt for content generation
2. WHEN generating summaries THEN the system SHALL support customization of the content focus (e.g., practical information, key concepts, etc.)
3. WHEN processing videos THEN the system SHALL allow configuration of summary length and detail level
4. WHEN the system is configured THEN it SHALL validate that required API keys are present

### Requirement 5

**User Story:** As a user, I want the YouTube video processing to integrate seamlessly with the existing CLI and main application flow, so that I can use it as a drop-in replacement for example data.

#### Acceptance Criteria

1. WHEN the main application runs THEN it SHALL support both example data mode and YouTube URL processing mode
2. WHEN a YouTube URL is provided via CLI THEN the system SHALL process it and create the Notion entry
3. WHEN the system processes a YouTube video THEN it SHALL maintain compatibility with existing notion_db operations
4. WHEN the processing is complete THEN the system SHALL provide the same success/failure feedback as the current implementation