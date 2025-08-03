---
inclusion: always
---

# Product Guidelines

YouTube-to-Notion Integration processes YouTube videos and creates AI-generated summaries in Notion databases with rich formatting and embedded content.

## Core Product Rules

### Content Processing Standards
- **Video Embedding**: Always embed YouTube videos at the top of Notion pages using video blocks
- **Thumbnail Covers**: Set video thumbnails as page cover images for visual consistency
- **Timestamp Linking**: Convert `[8:05]` or `[8:05-8:24]` patterns to clickable YouTube timestamp URLs
- **Rich Text Conversion**: Transform markdown summaries to Notion's rich text format with proper formatting

### Operation Modes
- **Default Mode**: Example data mode (no API keys required) - use for testing and demos
- **YouTube Mode**: Live processing with GEMINI_API_KEY - requires valid API configuration
- **Mode Validation**: Validate required environment variables based on selected mode

### Content Quality Standards
- **AI Summaries**: Generate comprehensive, structured summaries using Google Gemini
- **Markdown Support**: Handle headers (H1-H3), bullet points, numbered lists, bold, italic formatting
- **Error Graceful**: Provide meaningful error messages with troubleshooting guidance
- **Fallback Strategy**: YouTube API failures should gracefully fall back to web scraping

### Database Integration Rules
- **Dynamic Discovery**: Automatically find target Notion databases by name
- **Page Creation**: Create new pages with consistent structure and formatting
- **Property Mapping**: Map video metadata to appropriate Notion page properties
- **Duplicate Prevention**: Check for existing entries before creating new pages

### Conversation Logging Standards
- **Automatic Logging**: All Gemini API conversations are automatically logged to `chat_logs/` directory
- **Structured Format**: Logs saved as markdown files with naming pattern `{video_id}_{timestamp}.md`
- **Complete Context**: Each log includes session info, video metadata, full prompt, and AI response
- **Privacy Protection**: Chat logs are git-ignored to protect sensitive content
- **Cleanup Management**: Automatic cleanup of logs older than 30 days
- **Error Resilience**: Logging failures don't interrupt main processing workflow

### Batch Processing Standards
- **Multiple URLs**: Support processing multiple YouTube URLs in a single operation
- **Progress Tracking**: Show progress indicators for batch operations (e.g., "Processing 3/10...")
- **Error Resilience**: Continue processing remaining URLs even if some fail
- **Batch Reporting**: Provide summary of successful/failed operations at completion
- **Intelligent Quota Management**: Parse `retryDelay` from API responses and wait appropriately
- **Smart Retry Logic**: Wait for API-specified delay + 15 second buffer before retrying
- **Progress Feedback**: Show clear messages during quota waits (e.g., "Waiting 33 seconds before retry...")
- **Test Mode Optimization**: Cap retry delays to 5 seconds during testing to prevent hangs
- **Reduced Verbosity**: Use concise output in batch mode to avoid overwhelming logs
- **Resume Capability**: Support resuming interrupted batch operations

### User Experience Principles
- **Clear Feedback**: Provide progress indicators and success/failure messages
- **Validation First**: Validate inputs (URLs, API keys) before processing
- **Helpful Errors**: Include specific troubleshooting steps in error messages
- **Mode Clarity**: Make operation mode clear to users in CLI help and output
- **Batch Efficiency**: Minimize redundant operations (database lookups, client initialization) in batch mode
- **Quota Transparency**: Show clear messages when waiting for API quota limits (e.g., "Waiting 33 seconds...")
- **Resilient Processing**: Continue batch operations even when individual URLs hit quota limits
- **Test-Friendly**: Automatically detect test environments and cap delays to prevent hangs