# Technology Stack

## Core Dependencies

- **Python 3.12+**: Minimum supported version
- **notion-client**: Official Notion Python SDK for database operations
- **python-dotenv**: Environment variable management
- **pytest**: Testing framework

## Build System

- **Modern Python packaging**: Uses `pyproject.toml` with setuptools backend
- **Development installation**: `pip install -e .` for editable installs
- **Entry points**: Console script `youtube-notion` defined in pyproject.toml

## Common Commands

### Development Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Install in development mode (recommended)
pip install -e .

# Set up environment
cp .env.example .env
# Edit .env to add NOTION_TOKEN
```

### Running the Application
```bash
# Option 1: Use CLI script
python youtube_notion_cli.py

# Option 2: Use installed entry point
youtube-notion

# Option 3: Run as module
python -m youtube_notion.main
```

### Testing
```bash
# Recommended: Use test runner (handles path setup)
python run_tests.py

# Alternative: Direct pytest
python -m pytest tests/ -v

# After development install
pytest tests/ -v
```

## Architecture Patterns

- **Package structure**: Modern src-layout with `src/youtube_notion/`
- **Modular design**: Separate modules for database operations, markdown conversion, and utilities
- **Configuration**: Environment-based config with .env files
- **Error handling**: Graceful error handling with user-friendly messages