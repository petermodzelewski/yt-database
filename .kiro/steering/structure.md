# Project Structure

## Package Organization

The project follows modern Python packaging standards with a clear separation of concerns:

```
youtube-notion-integration/
├── src/youtube_notion/          # Main package (importable)
│   ├── __init__.py
│   ├── main.py                  # Application entry point
│   ├── config/                  # Configuration and example data
│   │   ├── __init__.py
│   │   └── example_data.py
│   ├── notion_db/               # Notion database operations
│   │   ├── __init__.py
│   │   └── operations.py
│   ├── processors/              # Video processing logic
│   │   └── youtube_processor.py
│   └── utils/                   # Utility modules
│       ├── __init__.py
│       └── markdown_converter.py
├── tests/                       # Comprehensive test suite
├── youtube_notion_cli.py        # CLI entry point script
├── run_tests.py                 # Test runner with path setup
├── pyproject.toml              # Modern Python packaging
├── setup.py                    # Package setup
└── requirements.txt            # Dependencies
```

## Key Architectural Patterns

### Module Responsibilities

- **`main.py`**: Application orchestration, error handling, and user feedback
- **`config/`**: Environment configuration, validation, and example data
- **`notion_db/operations.py`**: Database discovery and entry creation
- **`processors/`**: YouTube video processing and AI integration
- **`utils/markdown_converter.py`**: Markdown to Notion rich text conversion

### Import Patterns

```python
# Internal imports use relative imports within package
from .notion_db.operations import find_database_by_name
from .config.example_data import EXAMPLE_DATA
from .utils.markdown_converter import parse_rich_text

# External imports for processors (optional dependencies)
from .processors.youtube_processor import YouTubeProcessor
```

### Error Handling Strategy

- **Configuration Errors**: Graceful validation with user-friendly messages
- **API Errors**: Specific exception types with retry logic and fallbacks
- **Processing Errors**: Detailed error context with troubleshooting guidance
- **Return Values**: Boolean success indicators for main functions

### Testing Structure

- **Unit Tests**: Individual module functionality (`test_*.py`)
- **Integration Tests**: API interactions with mocking
- **End-to-End Tests**: Full workflow testing
- **Test Configuration**: `conftest.py` with fixtures and path setup
- **Test Runner**: `run_tests.py` handles PYTHONPATH automatically

### Configuration Management

- **Environment Files**: `.env` with `.env.example` template
- **Mode-Based Validation**: Different requirements for YouTube vs example mode
- **Graceful Fallbacks**: YouTube API → web scraping, detailed error messages
- **Structured Config**: Configuration classes with validation

### CLI Design

- **Dual Entry Points**: `youtube_notion_cli.py` (development) and console script (installed)
- **Mutually Exclusive Modes**: `--url` vs `--example-data`
- **Argument Validation**: Clear error messages for invalid combinations
- **Help Documentation**: Comprehensive usage examples