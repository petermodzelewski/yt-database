---
inclusion: always
---

# Product Guidelines

YouTube-to-Notion Integration processes YouTube videos and creates AI-generated summaries in Notion databases with rich formatting and embedded content.

## Core Product Rules

### Component Architecture Standards
- **Interface-Based Design**: All major components implement abstract interfaces for testability
- **Dependency Injection**: Use `ComponentFactory` to create and configure components
- **Orchestration**: `VideoProcessor` coordinates the complete processing pipeline
- **Component Validation**: Each component validates its configuration at initialization
- **Error Propagation**: Use structured exception hierarchy for clear error handling
- **Mock Support**: Comprehensive mock implementations enable fast unit testing

### Content Processing Standards
- **Video Embedding**: Always embed YouTube videos at the top of Notion pages using video blocks
- **Thumbnail Covers**: Set video thumbnails as page cover images for visual consistency
- **Timestamp Linking**: Convert `[8:05]` or `[8:05-8:24]` patterns to clickable YouTube timestamp URLs
- **Rich Text Conversion**: Transform markdown summaries to Notion's rich text format with proper formatting

### Operation Modes
- **Default Mode**: Example data mode (no API keys required) - use for testing and demos
- **YouTube Mode**: Live processing with GEMINI_API_KEY - requires valid API configuration
- **Test Mode**: Integration tests use `.env-test` configuration with test database "YT Summaries [TEST]"
- **Mode Validation**: Component factory validates required environment variables based on selected mode
- **Component Creation**: Factory pattern ensures proper component configuration for each mode

### Content Quality Standards
- **AI Summaries**: Use `GeminiSummaryWriter` implementation for comprehensive, structured summaries
- **Streaming Support**: Real-time streaming of AI responses with progress indicators
- **Markdown Support**: Handle headers (H1-H3), bullet points, numbered lists, bold, italic formatting
- **Error Graceful**: Structured exception hierarchy provides meaningful error messages
- **Fallback Strategy**: `VideoMetadataExtractor` gracefully falls back from YouTube API to web scraping
- **Component Validation**: Each component validates its configuration before processing

### Database Integration Rules
- **Storage Interface**: Use `NotionStorage` implementation of the `Storage` interface
- **Dynamic Discovery**: Automatically find target Notion databases by name
- **Page Creation**: Create new pages with consistent structure and formatting
- **Property Mapping**: Map video metadata to appropriate Notion page properties
- **Duplicate Prevention**: Check for existing entries before creating new pages
- **Rich Text Conversion**: Integrated markdown-to-Notion conversion within storage layer

### Conversation Logging Standards
- **Integrated Logging**: `ChatLogger` utility integrated within `GeminiSummaryWriter`
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
- **Validation First**: Component factory validates all configurations before processing
- **Helpful Errors**: Structured exception hierarchy provides specific troubleshooting steps
- **Mode Clarity**: Make operation mode clear to users in CLI help and output
- **Batch Efficiency**: Minimize redundant operations (database lookups, client initialization) in batch mode
- **Quota Transparency**: Show clear messages when waiting for API quota limits (e.g., "Waiting 33 seconds...")
- **Resilient Processing**: Continue batch operations even when individual URLs hit quota limits
- **Test-Friendly**: Automatically detect test environments and cap delays to prevent hangs

### Testing Standards
- **Development Focus**: Unit tests are primary tool for daily development (478 tests in ~6 seconds)
- **Unit Test Speed**: Complete in under 10 seconds using comprehensive mock implementations
- **Integration Validation**: Integration tests for end-of-cycle validation (13 tests in ~90 seconds)
- **Integration Safety**: Integration tests use dedicated test database and `.env-test` configuration
- **Mock Completeness**: All interfaces have corresponding mock implementations for testing
- **Test Isolation**: Unit tests don't perform I/O operations or call external APIs
- **Component Testing**: Each component can be tested independently through its interface
- **Workflow**: Run unit tests frequently, integration tests before releases

## Current Product Status

### ✅ Architecture Restructure Complete
The YouTube-to-Notion integration has successfully completed a comprehensive architecture restructure:

- **Component-Based Design**: Clean separation between metadata extraction, summary generation, and storage
- **Interface-Driven**: Abstract interfaces enable pluggable implementations for different AI providers and storage backends
- **Factory Pattern**: `ComponentFactory` handles dependency injection and component configuration
- **Comprehensive Testing**: 478 unit tests (6s) + 13 integration tests (90s) with full mock implementations
- **Backward Compatibility**: All existing functionality preserved with identical external behavior

### ✅ Quality Assurance
- **Error Handling**: Structured exception hierarchy with intelligent retry logic and graceful fallbacks
- **Performance**: Optimized for development workflow with fast unit tests
- **Reliability**: Comprehensive error handling with quota management and API fallbacks
- **Maintainability**: Clear component boundaries and extensive test coverage

### ✅ Development Workflow
- **Daily Development**: Focus on unit tests for rapid feedback and validation
- **Release Validation**: Integration tests ensure end-to-end functionality with real APIs
- **Component Isolation**: Each component can be developed and tested independently