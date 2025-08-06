---
inclusion: always
---

# Technical Guidelines

## Core Stack & Dependencies

**Python 3.12+** with `notion-client`, `google-genai>=0.1.0`, `python-dotenv`, `pytest`

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

### Retry Logic
- Implement graceful fallbacks (YouTube API → web scraping)
- Parse API `retryDelay` responses (e.g., "18s") + 15 second buffer
- Use connection pooling for batch operations
- Validate all API responses before processing

### Configuration
- Use `.env` for development, `.env-test` for integration tests
- Validate configuration at component initialization
- Support multiple API providers with graceful degradation

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
python youtube_notion_cli.py --batch --urls url1 url2 # Batch mode
```

## CLI Design

- Dual entry points: `youtube_notion_cli.py` (dev) and console script (installed)
- Mutually exclusive argument groups for different modes
- File-based URL input for large batch operations (`--file urls.txt`)
- Use `batch_mode` parameter to control output verbosity