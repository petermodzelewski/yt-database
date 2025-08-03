---
inclusion: always
---

# Technical Guidelines

## Technology Stack & Dependencies

**Core Stack**: Python 3.12+, Notion SDK, Google Gemini AI, YouTube Data API
**Key Dependencies**: `notion-client`, `google-genai>=0.1.0`, `python-dotenv`, `pytest`

## Development Patterns

### Package Structure
- Use relative imports within `src/youtube_notion/` package
- Follow modern Python packaging with `pyproject.toml`
- Maintain clear module separation: `config/`, `notion_db/`, `processors/`, `utils/`

### Testing Requirements
- **Always use**: `python run_tests.py` (handles PYTHONPATH automatically)
- **Avoid**: Direct `pytest` calls without proper path setup
- Install in development mode: `pip install -e .` before testing

### Test-Driven Development Standards
- **MANDATORY**: Write proper unit tests for every functionality change
- **NEVER**: Use print statements or quick checks for validation
- **ALWAYS**: Run full test suite after any code changes
- **REQUIRED**: Review and update existing tests when functionality changes
- **PREFER**: Unit tests over integration tests (faster execution)
- **STRUCTURE**: Follow existing test patterns in `tests/` directory
- **COVERAGE**: Ensure new code paths are covered by tests
- **VALIDATION**: Tests must pass before considering changes complete

### Error Handling Standards
- Return boolean success indicators from main functions
- Use specific exception types with retry logic
- Provide user-friendly error messages with troubleshooting context
- Implement graceful fallbacks (YouTube API → web scraping)
- **Intelligent Quota Management**: Parse `retryDelay` from API responses and wait appropriately
- **Test Mode Detection**: Cap retry delays to 5 seconds during testing to prevent hangs
- **Batch Resilience**: Continue processing other URLs even when some hit quota limits

### Configuration Management
- Use `.env` files with `python-dotenv` for environment variables
- Validate configuration based on operation mode (YouTube vs example data)
- Support multiple API providers with graceful degradation

## Code Style Rules

### Import Conventions
```python
# Internal package imports (relative)
from .notion_db.operations import find_database_by_name
from .config.example_data import EXAMPLE_DATA

# External dependencies (absolute)
from notion_client import Client
```

### CLI Design Patterns
- Support dual entry points: `youtube_notion_cli.py` (dev) and console script (installed)
- Use mutually exclusive argument groups for different modes
- Provide comprehensive help documentation with examples
- Support batch processing with `--batch` flag and multiple URL inputs
- Implement file-based URL input for large batch operations
- Use `batch_mode` parameter to control output verbosity

### API Integration Standards
- Implement retry logic for external API calls
- Use structured error handling with specific exception types
- Support fallback mechanisms (API → web scraping)
- Validate API responses before processing
- Implement rate limiting for batch operations to respect API quotas
- Use connection pooling and session reuse for batch processing efficiency
- **Enhanced Quota Handling**: Parse `retryDelay` from API error responses (e.g., "18s")
- **Smart Retry Logic**: Wait for API-specified delay + 15 second buffer before retrying
- **Batch Processing Resilience**: Continue processing remaining URLs when individual ones hit quota limits
- **Test Environment Optimization**: Cap retry delays to 5 seconds maximum during testing

## Development Commands

```bash
# Setup (required)
pip install -e .
cp .env.example .env

# Testing (preferred method)
python run_tests.py

# Running application
python youtube_notion_cli.py --example-data  # Default mode
python youtube_notion_cli.py --url "https://youtu.be/VIDEO_ID"  # YouTube mode
python youtube_notion_cli.py --batch --urls url1 url2 url3  # Batch mode
python youtube_notion_cli.py --batch --file urls.txt  # Batch from file
```