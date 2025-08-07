---
inclusion: always
---

# Product Guidelines

YouTube-to-Notion Integration processes YouTube videos and creates AI-generated summaries in Notion databases with rich formatting and embedded content.

## Architecture Patterns

### Component-Based Design
- Use `ComponentFactory` for dependency injection and component creation
- All components implement abstract interfaces (`Storage`, `SummaryWriter`)
- `VideoProcessor` orchestrates the complete processing pipeline
- Each component validates configuration at initialization
- Use structured exception hierarchy from `utils/exceptions.py`

### Operation Modes
- **Default**: Example data mode (no API keys required)
- **YouTube**: Live processing with `GEMINI_API_KEY` 
- **Test**: Integration tests use `.env-test` with "YT Summaries [TEST]" database

## Content Standards

### Notion Page Structure
- Embed YouTube video at top using video blocks
- Set video thumbnail as page cover image
- Convert `[8:05]` timestamps to clickable YouTube URLs
- Transform markdown to Notion rich text format

### AI Summary Requirements
- Use `GeminiSummaryWriter` for structured summaries
- **CRITICAL**: Pass YouTube URLs as FileData to Gemini API (not text prompts)
- Support streaming responses with progress indicators
- Handle markdown: headers (H1-H3), lists, bold, italic, **nested formatting in tables**
- Automatic conversation logging to `chat_logs/` directory

### Advanced Markdown Processing
- **Table Support**: Full table parsing with nested formatting (bold, italic, links)
- **Rich Text in Cells**: Each table cell supports complete markdown formatting
- **Code Block Preservation**: Markdown formatting ignored within code blocks
- **Property-Based Validation**: Robust parsing tested with generated edge cases

### Batch Processing
- Support multiple URLs with progress tracking ("Processing 3/10...")
- Continue processing on individual failures
- Parse API `retryDelay` responses and wait appropriately
- Cap retry delays to 5 seconds during testing
- Use concise output in batch mode

## Quality Standards

### Error Handling
- Return boolean success indicators from main functions
- Use specific exceptions: `VideoProcessingError`, `ConfigurationError`, etc.
- Implement graceful fallbacks (YouTube API → web scraping)
- Provide user-friendly error messages with troubleshooting context

### Testing Workflow
- **Primary**: Unit tests for daily development (`python run_tests.py` - 478 tests, ~6s)
- **Secondary**: Integration tests for releases (`python -m pytest tests/integration/` - 13 tests, ~90s)
- Use mock implementations from `tests/fixtures/mock_implementations.py`
- Unit tests must not perform I/O or call external APIs

### Database Integration
- Use `NotionStorage` implementation of `Storage` interface
- **CRITICAL**: Implement block batching for summaries >100 blocks
- Automatically discover target databases by name
- Check for duplicates before creating pages
- Map video metadata to Notion page properties
- Handle Notion's 100-block limit with automatic batching (first 100 blocks + append remaining)