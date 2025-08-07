---
inclusion: always
---

# Project Structure & Architecture Guide

## Package Organization

Component-based architecture with clear separation of concerns:

```
src/youtube_notion/              # Main package (use relative imports)
├── main.py                      # Application entry point
├── interfaces/                  # Abstract base classes (contracts)
│   ├── storage.py               # Storage interface
│   └── summary_writer.py        # Summary writer interface
├── extractors/                  # Video metadata extraction
│   └── video_metadata_extractor.py
├── writers/                     # AI summary generation
│   └── gemini_summary_writer.py
├── storage/                     # Data persistence
│   └── notion_storage.py
├── processors/                  # Orchestration layer
│   └── video_processor.py       # Main orchestrator
├── config/                      # Configuration & DI
│   ├── factory.py               # Component factory
│   ├── settings.py              # Environment config
│   └── example_data.py
└── utils/                       # Shared utilities
    ├── exceptions.py            # Exception hierarchy
    ├── chat_logger.py           # Conversation logging
    ├── video_utils.py           # Video processing utilities
    └── markdown_converter.py
```

## Architecture Patterns

### Component-Based Design
- **Interfaces First**: All components implement abstract interfaces from `interfaces/`
- **Dependency Injection**: Use `ComponentFactory` to create and wire components
- **Single Responsibility**: Each component has one clear purpose
- **Testability**: Mock implementations in `tests/fixtures/mock_implementations.py`

### Standard Component Creation Pattern
```python
from .config.factory import ComponentFactory

# Always use factory for component creation
factory = ComponentFactory()
processor = VideoProcessor(
    factory.create_metadata_extractor(),
    factory.create_summary_writer(),
    factory.create_storage()
)
success = processor.process_video(url)
```

### Component Responsibilities

| Component | Purpose | Key Functions |
|-----------|---------|---------------|
| `main.py` | Application entry point | Orchestrates ComponentFactory and VideoProcessor |
| `interfaces/` | Abstract contracts | `Storage`, `SummaryWriter` interfaces |
| `extractors/` | YouTube metadata | URL validation, video ID extraction, metadata retrieval |
| `writers/` | AI summary generation | Gemini AI integration with streaming and retry logic |
| `storage/` | Data persistence | Notion database operations with rich text conversion |
| `processors/` | Workflow orchestration | Coordinates all components through dependency injection |
| `config/factory.py` | Dependency injection | Creates and configures components based on environment |
| `utils/exceptions.py` | Error handling | Structured exception hierarchy |
| `utils/chat_logger.py` | Conversation logging | Automatic cleanup and structured logging |
| `utils/video_utils.py` | Video processing | Duration parsing, video splitting for long content |

### Import Conventions

**ALWAYS use relative imports within `src/youtube_notion/` package:**

```python
# Interfaces (for type hints and contracts)
from .interfaces.storage import Storage
from .interfaces.summary_writer import SummaryWriter

# Core components
from .extractors.video_metadata_extractor import VideoMetadataExtractor
from .writers.gemini_summary_writer import GeminiSummaryWriter
from .storage.notion_storage import NotionStorage
from .processors.video_processor import VideoProcessor

# Configuration and utilities
from .config.factory import ComponentFactory
from .config.example_data import EXAMPLE_DATA
from .utils.exceptions import VideoProcessingError, ConfigurationError
from .utils.video_utils import parse_iso8601_duration, calculate_video_splits
from .utils.markdown_converter import parse_rich_text

# External dependencies (absolute imports)
from notion_client import Client
import google.generativeai as genai
```

### Error Handling Rules

**Exception Hierarchy** (use specific types from `utils/exceptions.py`):
- `VideoProcessingError` - Base for video processing failures
- `ConfigurationError` - Configuration validation failures  
- `MetadataExtractionError` - Video metadata extraction failures
- `SummaryGenerationError` - AI summary generation failures
- `StorageError` - Data persistence failures

**Error Handling Patterns**:
- Return boolean success indicators from main functions
- Validate component configuration at initialization
- Implement graceful fallbacks (YouTube API → web scraping)
- Provide user-friendly error messages with troubleshooting context
- Parse `retryDelay` from API responses and wait appropriately
- Cap retry delays to 5 seconds during testing to prevent hangs

## Testing Architecture

### Test Directory Structure
```
tests/
├── unit/                        # Fast, isolated tests (478 tests, ~6s)
│   ├── test_video_metadata_extractor.py
│   ├── test_gemini_summary_writer.py
│   ├── test_notion_storage.py
│   ├── test_video_processor.py
│   ├── test_component_factory.py
│   ├── test_main.py
│   ├── test_property_based_markdown_converter.py  # Property-based tests
│   ├── test_video_utils.py      # Video processing utilities tests
│   └── utils/
│       ├── test_exceptions.py
│       ├── test_chat_logger.py
│       └── test_markdown_converter.py
├── integration/                 # End-to-end tests (13 tests, ~90s)
│   ├── test_youtube_integration.py
│   ├── test_notion_integration.py
│   └── test_full_pipeline.py
├── fixtures/                    # Test data and mocks
│   ├── mock_implementations.py  # Mock components for unit tests
│   ├── sample_video_data.py     # Test video metadata
│   └── notion_test_data.py      # Sample Notion responses
└── conftest.py                  # Pytest configuration and shared fixtures
```

### Testing Strategy

**PRIMARY: Unit Tests** (`python run_tests.py`)
- **Purpose**: Fast feedback during development (478 tests in ~6 seconds)
- **Scope**: Individual component testing with dependency injection
- **Isolation**: Mock implementations from `tests/fixtures/mock_implementations.py`
- **No External Dependencies**: No I/O, APIs, or file system operations
- **Coverage**: Test all business logic, error handling, and edge cases

**SECONDARY: Integration Tests** (`python -m pytest tests/integration/`)
- **Purpose**: End-to-end validation before releases (13 tests in ~90 seconds)
- **Scope**: Real external APIs with `.env-test` configuration
- **Environment**: Test database "YT Summaries [TEST]" for safe testing
- **Coverage**: Full pipeline testing with actual YouTube and Notion APIs

### Test Development Rules

**Unit Test Requirements**:
- **MANDATORY**: Write unit tests for every functionality change
- **ISOLATION**: Use mock implementations, never call external APIs
- **FAST**: Tests must complete in seconds, not minutes
- **COMPREHENSIVE**: Cover success paths, error conditions, and edge cases
- **DEPENDENCY INJECTION**: Test components through their interfaces
- **PROPERTY-BASED**: Use Hypothesis for complex validation (e.g., markdown parsing)
- **PYTEST ONLY**: All tests must use pytest framework consistently

**Integration Test Guidelines**:
- **ENVIRONMENT**: Use `.env-test` configuration exclusively
- **SAFETY**: Only use designated test databases and resources
- **CLEANUP**: Tests must clean up any created resources
- **RESILIENCE**: Handle API rate limits and network issues gracefully

**Testing Workflow**:
- **DAILY DEVELOPMENT**: Run `python run_tests.py` frequently
- **NEVER**: Use print statements or quick checks for validation
- **REQUIRED**: Update existing tests when functionality changes
- **PREFER**: Unit tests over integration tests for faster feedback
- **BEFORE RELEASES**: Run full integration test suite

### Configuration Management

**Environment Files**:
- `.env` - Development and production
- `.env-test` - Integration tests only
- `.env.example` - Template for setup

**Configuration Rules**:
- Use `ComponentFactory` for all component creation
- Validate configuration based on operation mode (YouTube vs example data)
- Support multiple API providers with graceful degradation
- Components validate their configuration at initialization

## Development Commands

**Setup** (required):
```bash
pip install -e .
cp .env.example .env
```

**Testing** (primary development workflow):
```bash
python run_tests.py                    # Unit tests (fast, ~6 seconds)
python -m pytest tests/integration/   # Integration tests (slow, ~90 seconds)
```

**Running application**:
```bash
python youtube_notion_cli.py --example-data  # Default mode
python youtube_notion_cli.py --url "https://youtu.be/VIDEO_ID"  # YouTube mode
python youtube_notion_cli.py --urls "url1,url2,url3"  # Batch mode
python youtube_notion_cli.py --file urls.txt  # Batch from file
```

## Key Architecture Rules

1. **Component Creation**: Always use `ComponentFactory` - never instantiate components directly
2. **Import Style**: Use relative imports within `src/youtube_notion/` package
3. **Error Handling**: Use specific exception types from `utils/exceptions.py`
4. **Testing**: Write unit tests for all functionality changes - run `python run_tests.py`
5. **Configuration**: Validate component configuration at initialization
6. **Interfaces**: All components must implement abstract interfaces for testability