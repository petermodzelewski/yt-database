# Project Structure

## Directory Layout

```
youtube-notion-integration/
├── src/
│   └── youtube_notion/          # Main package
│       ├── __init__.py
│       ├── main.py              # Application entry point
│       ├── config/              # Configuration and example data
│       │   ├── __init__.py
│       │   └── example_data.py
│       ├── notion_db/           # Notion database operations
│       │   ├── __init__.py
│       │   └── operations.py
│       └── utils/               # Utility modules
│           ├── __init__.py
│           └── markdown_converter.py
├── tests/                       # Comprehensive test suite
├── youtube_notion_cli.py        # Command-line entry point
├── pyproject.toml              # Modern Python packaging
├── setup.py                    # Package setup
└── requirements.txt            # Dependencies
```

## Module Organization

### Core Application (`src/youtube_notion/`)
- **main.py**: Entry point, orchestrates the workflow using example data
- **config/example_data.py**: Sample YouTube video data for testing/demo

### Database Layer (`notion_db/`)
- **operations.py**: Notion API interactions
  - `find_database_by_name()`: Locate target database
  - `add_youtube_entry()`: Create formatted Notion pages

### Utilities (`utils/`)
- **markdown_converter.py**: Markdown to Notion conversion
  - `markdown_to_notion_blocks()`: Convert markdown to Notion blocks
  - `enrich_timestamps_with_links()`: Transform timestamps to clickable links
  - `parse_rich_text()`: Handle markdown formatting (bold, italic, links)

### Testing (`tests/`)
- **Unit tests**: Individual component testing
- **Integration tests**: End-to-end workflow testing
- **conftest.py**: Pytest configuration and path setup
- **run_tests.py**: Custom test runner with fallback support

## Import Conventions

- Use relative imports within the package: `from .utils.markdown_converter import ...`
- Package imports in tests: `from youtube_notion.module import ...`
- External dependencies imported at module level

## File Naming

- Snake_case for Python files and modules
- Test files prefixed with `test_`
- Configuration files use standard names (`.env`, `pyproject.toml`)
- CLI entry point uses descriptive name (`youtube_notion_cli.py`)