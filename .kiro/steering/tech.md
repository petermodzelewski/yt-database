---
inclusion: always
---

# Technical Guidelines

## Core Stack & Dependencies

**Python 3.12+** with `notion-client`, `google-genai>=0.1.0`, `python-dotenv`, `pytest`, `hypothesis`

### Key Dependencies
- `notion-client` - Official Notion API client
- `google-genai>=0.1.0` - Google Gemini AI integration with FileData support
- `google-api-python-client>=2.0.0` - YouTube Data API access
- `requests>=2.25.0` - HTTP requests and web scraping fallback
- `pytest` - Primary testing framework (unified across all tests)
- `hypothesis` - Property-based testing for robust validation

## Architecture Rules

### Component-Based Design
- **ALWAYS** use `ComponentFactory` for dependency injection - never instantiate components directly
- **ALWAYS** use relative imports within `src/youtube_notion/` package
- All components implement abstract interfaces from `interfaces/` for testability
- Package structure: `interfaces/`, `extractors/`, `writers/`, `storage/`, `processors/`, `config/`, `utils/`

### Import Pattern (Required)
```python
# Relative imports within package
from .interfaces.storage import Storage
from .config.factory import ComponentFactory
from .utils.exceptions import VideoProcessingError

# Absolute imports for external dependencies
from notion_client import Client
```

## Testing Standards

### Primary Development Workflow
- **MANDATORY**: Run `python run_tests.py` for all development (478 tests, ~6s)
- **NEVER**: Use direct `pytest` calls or print statements for validation
- **REQUIRED**: Write unit tests for every functionality change
- **REQUIRED**: Use mock implementations from `tests/fixtures/mock_implementations.py`

### Test Types
- **Unit Tests** (`tests/unit/`): Fast, isolated, no external APIs
- **Integration Tests** (`tests/integration/`): End-to-end with `.env-test` config
- Run integration tests only before releases (13 tests, ~90s)

## Error Handling

### Exception Hierarchy (from `utils/exceptions.py`)
- `VideoProcessingError` - Base for video processing failures
- `ConfigurationError` - Configuration validation failures
- `MetadataExtractionError` - Video metadata extraction failures
- `SummaryGenerationError` - AI summary generation failures
- `StorageError` - Data persistence failures

### Error Patterns
- Return boolean success indicators from main functions
- Parse `retryDelay` from API responses and wait appropriately
- Cap retry delays to 5 seconds during testing
- Continue batch processing when individual URLs fail

## API Integration

### Gemini API Best Practices
- **CRITICAL**: Use `types.Part(file_data=...)` for YouTube URLs, not text prompts
- Pass video URLs as FileData objects to align with Gemini documentation
- This ensures reliable video processing and proper API usage

### Notion API Optimization
- **CRITICAL**: Implement block batching for summaries >100 blocks
- Create pages with first 100 blocks, append remaining in batches of 100
- Handle Notion's hard limit gracefully to prevent validation errors
- Test with long summaries to verify batching logic

### Retry Logic
- Implement graceful fallbacks (YouTube API → web scraping)
- Parse API `retryDelay` responses (e.g., "18s") + 15 second buffer
- Use connection pooling for batch operations
- Validate all API responses before processing

### Configuration
- Use `.env` for development, `.env-test` for integration tests
- Validate configuration at component initialization
- Support multiple API providers with graceful degradation

## Recent Improvements (Post-PR #3)

### Critical API Fixes
- **Gemini FileData**: YouTube URLs now passed as FileData objects (not text)
- **Notion Batching**: Automatic handling of 100+ block summaries with batching
- **Nested Table Formatting**: Rich markdown support within table cells

### Testing Enhancements
- **Property-Based Testing**: Added Hypothesis for robust markdown validation
- **Unified pytest**: All tests now use pytest framework consistently
- **Enhanced Coverage**: 478 unit tests with comprehensive edge case testing

### Code Quality Improvements
- **Consolidated Processing**: Streamlined main.py logic (reduced by 184 lines)
- **Better Error Handling**: Enhanced API integration with proper fallbacks
- **Rich Content Support**: Tables with nested bold, italic, links formatting

## Development Commands

```bash
# Setup
pip install -e .
cp .env.example .env

# Primary workflow
python run_tests.py                    # Unit tests (daily use)
python -m pytest tests/integration/   # Integration tests (releases only)

# Application modes
python youtube_notion_cli.py --example-data           # Default mode
python youtube_notion_cli.py --url "VIDEO_URL"        # YouTube mode
python youtube_notion_cli.py --urls "url1,url2,url3"  # Batch mode
python youtube_notion_cli.py --file urls.txt          # Batch from file
```

## CLI Design

- Dual entry points: `youtube_notion_cli.py` (dev) and console script (installed)
- Mutually exclusive argument groups for different modes
- **Batch Processing**: 
  - `--urls "url1,url2,url3"` for comma-separated URLs
  - `--file urls.txt` for file-based URL input
- Use `batch_mode` parameter to control output verbosity
- Custom prompts only supported with single `--url` (not batch modes)