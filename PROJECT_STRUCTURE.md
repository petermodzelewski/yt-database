# Project Structure

This document outlines the organized folder structure of the YouTube to Notion Database Integration project.

## Directory Structure

```
youtube-notion-integration/
├── src/                          # Source code
│   ├── __init__.py
│   ├── notion_db/               # Notion database operations
│   │   ├── __init__.py
│   │   └── operations.py        # Database CRUD operations
│   └── utils/                   # Utility modules
│       ├── __init__.py
│       └── markdown_converter.py # Markdown to Notion conversion
├── tests/                       # Test files
│   ├── __init__.py
│   ├── test_markdown_converter.py # Unit tests for markdown converter
│   └── test_integration.py     # Integration tests
├── config/                      # Configuration files
│   ├── __init__.py
│   └── example_data.py         # Sample data for testing
├── main.py                     # Main application entry point
├── setup.py                    # Package setup configuration
├── pyproject.toml             # Modern Python project configuration
├── requirements.txt           # Python dependencies
├── .env                       # Environment variables (not in git)
├── .env.example              # Environment variables template
├── .gitignore                # Git ignore rules
└── README.md                 # Project documentation
```

## Module Descriptions

### `src/notion_db/operations.py`
Contains functions for interacting with Notion databases:
- `find_database_by_name()` - Locates a database by name and optional parent page
- `add_youtube_entry()` - Creates a new entry in the YT Summaries database

### `src/utils/markdown_converter.py`
Handles conversion of markdown text to Notion's rich text format:
- `parse_rich_text()` - Converts markdown formatting (bold/italic) to Notion rich text
- `markdown_to_notion_blocks()` - Converts full markdown to Notion block structure

### `tests/`
Comprehensive test suite:
- `test_markdown_converter.py` - 17 unit tests covering all markdown conversion scenarios
- `test_integration.py` - Integration test using real example data

### `config/example_data.py`
Contains sample YouTube video data for testing and demonstration purposes.

## Key Features of This Structure

1. **Separation of Concerns**: Each module has a specific responsibility
2. **Testability**: Clear separation makes unit testing straightforward
3. **Reusability**: Utility functions can be easily imported and reused
4. **Maintainability**: Organized structure makes the codebase easy to navigate
5. **Scalability**: Easy to add new features in appropriate modules

## Running the Application

### Main Application
```bash
python main.py
```

### Running Tests
```bash
# Unit tests
python tests/test_markdown_converter.py

# Integration tests
python tests/test_integration.py

# All tests with pytest (if installed)
pytest tests/
```

### Installation
```bash
# Install dependencies
pip install -r requirements.txt

# Install as package (optional)
pip install -e .
```

## Environment Setup

1. Copy `.env.example` to `.env`
2. Add your Notion API token to `.env`
3. Ensure your Notion database is set up with the required properties

This structure follows Python best practices and makes the project professional, maintainable, and easy to extend.