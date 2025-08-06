---
inclusion: always
---

# Project Structure

## Package Organization

The project follows modern Python packaging standards with a clear separation of concerns:

```
youtube-notion-integration/
├── src/youtube_notion/          # Main package (importable)
│   ├── __init__.py
│   ├── main.py                  # Application entry point
│   ├── interfaces/              # Abstract base classes
│   │   ├── __init__.py
│   │   ├── storage.py           # Storage interface
│   │   └── summary_writer.py    # Summary writer interface
│   ├── extractors/              # Video metadata extraction
│   │   ├── __init__.py
│   │   └── video_metadata_extractor.py
│   ├── writers/                 # Summary generation implementations
│   │   ├── __init__.py
│   │   └── gemini_summary_writer.py
│   ├── storage/                 # Data persistence backends
│   │   ├── __init__.py
│   │   └── notion_storage.py
│   ├── processors/              # Orchestration and workflow
│   │   ├── __init__.py
│   │   ├── video_processor.py   # Main orchestrator
│   │   ├── youtube_processor.py # Legacy processor (deprecated)
│   │   └── exceptions.py        # Processor-specific exceptions
│   ├── config/                  # Configuration and factory
│   │   ├── __init__.py
│   │   ├── factory.py           # Component factory for DI
│   │   ├── settings.py          # Configuration management
│   │   └── example_data.py
│   ├── notion_db/               # Legacy Notion operations (deprecated)
│   │   ├── __init__.py
│   │   └── operations.py
│   └── utils/                   # Shared utilities
│       ├── __init__.py
│       ├── exceptions.py        # Exception hierarchy
│       ├── chat_logger.py       # Conversation logging
│       └── markdown_converter.py
├── tests/                       # Comprehensive test suite
│   ├── unit/                    # Fast, isolated unit tests
│   ├── integration/             # Integration tests with external APIs
│   ├── fixtures/                # Mock implementations and test data
│   │   └── mock_implementations.py
│   └── conftest.py              # Test configuration
├── youtube_notion_cli.py        # CLI entry point script
├── run_tests.py                 # Test runner with path setup
├── .env-test                    # Integration test configuration
├── pyproject.toml              # Modern Python packaging
├── setup.py                    # Package setup
└── requirements.txt            # Dependencies
```

## Key Architectural Patterns

### Component-Based Architecture

The project follows a component-based architecture with clear separation of concerns:

- **Interfaces**: Abstract base classes define contracts for components
- **Implementations**: Concrete implementations of interfaces (e.g., `GeminiSummaryWriter`, `NotionStorage`)
- **Orchestration**: `VideoProcessor` coordinates all components through dependency injection
- **Factory Pattern**: `ComponentFactory` creates and configures components based on environment
- **Testability**: Mock implementations allow fast unit testing without external dependencies

### Dependency Injection Pattern

```python
# Factory creates components based on configuration
factory = ComponentFactory()
extractor = factory.create_metadata_extractor()
writer = factory.create_summary_writer()
storage = factory.create_storage()

# VideoProcessor orchestrates components
processor = VideoProcessor(extractor, writer, storage)
success = processor.process_video(url)
```

### Module Responsibilities

- **`main.py`**: Application orchestration using ComponentFactory and VideoProcessor
- **`interfaces/`**: Abstract base classes defining component contracts
  - `Storage`: Interface for data persistence backends
  - `SummaryWriter`: Interface for AI summary generation
- **`extractors/video_metadata_extractor.py`**: YouTube URL validation, video ID extraction, and metadata retrieval
- **`writers/gemini_summary_writer.py`**: Google Gemini AI integration with streaming and retry logic
- **`storage/notion_storage.py`**: Notion database operations with rich text conversion
- **`processors/video_processor.py`**: Main orchestrator coordinating all components
- **`config/factory.py`**: Dependency injection and component creation
- **`config/settings.py`**: Environment configuration and validation
- **`utils/exceptions.py`**: Structured exception hierarchy for error handling
- **`utils/chat_logger.py`**: Conversation logging with automatic cleanup
- **`utils/markdown_converter.py`**: Markdown to Notion rich text conversion

### Import Patterns

```python
# Interface imports for type hints and contracts
from .interfaces.storage import Storage
from .interfaces.summary_writer import SummaryWriter

# Component implementations
from .extractors.video_metadata_extractor import VideoMetadataExtractor
from .writers.gemini_summary_writer import GeminiSummaryWriter
from .storage.notion_storage import NotionStorage
from .processors.video_processor import VideoProcessor

# Configuration and utilities
from .config.factory import ComponentFactory
from .config.example_data import EXAMPLE_DATA
from .utils.exceptions import VideoProcessingError, ConfigurationError
from .utils.markdown_converter import parse_rich_text

# All legacy components have been removed - use new architecture only
```

### Error Handling Strategy

- **Structured Exception Hierarchy**: Use specific exception types from `utils/exceptions.py`
  - `VideoProcessingError`: Base exception for video processing failures
  - `ConfigurationError`: Configuration validation failures
  - `MetadataExtractionError`: Video metadata extraction failures
  - `SummaryGenerationError`: AI summary generation failures
  - `StorageError`: Data persistence failures
- **Component Validation**: Each component validates its configuration at initialization
- **Graceful Fallbacks**: YouTube API → web scraping, detailed error messages
- **Return Values**: Boolean success indicators from main functions
- **Batch Errors**: Aggregate error reporting with individual URL failure tracking
- **Rate Limiting**: Exponential backoff and quota management for batch operations

### Testing Structure

- **Unit Tests** (`tests/unit/`): Fast, isolated tests using mock implementations
  - Individual component functionality with dependency injection
  - Mock implementations from `tests/fixtures/mock_implementations.py`
  - Complete in under 10 seconds total, no I/O operations
- **Integration Tests** (`tests/integration/`): Tests with external dependencies
  - Use `.env-test` configuration exclusively
  - Test database "YT Summaries [TEST]" for safe testing
  - API interactions with real services
- **Test Configuration**: Separate `conftest.py` files for unit and integration tests
- **Test Runner**: `run_tests.py` handles PYTHONPATH automatically
- **Mock Implementations**: Comprehensive mocks for all interfaces in `tests/fixtures/`

### Configuration Management

- **Environment Files**: 
  - `.env` for development and production
  - `.env-test` for integration tests
  - `.env.example` as template
- **Component Factory**: `config/factory.py` handles dependency injection
- **Mode-Based Validation**: Different requirements for YouTube vs example mode
- **Interface-Based Design**: Components implement abstract interfaces for testability
- **Configuration Classes**: Structured configuration with validation in `config/settings.py`
- **Graceful Fallbacks**: YouTube API → web scraping, detailed error messages

### CLI Design

- **Dual Entry Points**: `youtube_notion_cli.py` (development) and console script (installed)
- **Mutually Exclusive Modes**: `--url` vs `--example-data` vs `--batch`
- **Batch Input Methods**: Multiple URLs via `--urls` or file input via `--file`
- **Argument Validation**: Clear error messages for invalid combinations
- **Help Documentation**: Comprehensive usage examples including batch operations
- **Progress Indicators**: Real-time progress feedback for batch processing
- **Output Control**: Verbose vs concise output modes based on operation type