# Technology Stack

## Core Technologies

- **Python 3.12+**: Primary language with modern packaging structure
- **Notion SDK**: Official Python client for Notion API integration
- **Google Gemini AI**: AI-powered video summary generation
- **YouTube Data API**: Optional metadata extraction (falls back to web scraping)

## Key Dependencies

```
notion-client          # Notion API integration
python-dotenv          # Environment variable management
pytest                 # Testing framework
google-genai>=0.1.0    # Google Gemini AI integration
google-api-python-client>=2.0.0  # YouTube Data API
requests>=2.25.0       # HTTP requests for web scraping fallback
```

## Build System

- **Modern Python Packaging**: Uses `pyproject.toml` with setuptools backend
- **Development Installation**: `pip install -e .` for editable installs
- **Entry Points**: Console script `youtube-notion` available after installation

## Common Commands

### Development Setup
```bash
# Clone and install dependencies
pip install -r requirements.txt

# Install in development mode (recommended)
pip install -e .

# Copy environment template
cp .env.example .env
```

### Testing
```bash
# Preferred method - uses test runner with proper path setup
python run_tests.py

# Direct pytest (requires proper PYTHONPATH)
python -m pytest tests/ -v

# Install package first, then test
pip install -e .
pytest tests/ -v
```

### Running the Application
```bash
# CLI script (recommended for development)
python youtube_notion_cli.py --url "https://youtu.be/VIDEO_ID"

# Installed console command
youtube-notion --url "https://youtu.be/VIDEO_ID"

# Module execution
python -m youtube_notion.main

# Example data mode (default)
python youtube_notion_cli.py --example-data
```

## Configuration Management

- **Environment Variables**: Uses `.env` files with python-dotenv
- **Configuration Classes**: Structured config validation in `config/` module
- **API Key Management**: Supports multiple API providers with graceful fallbacks
- **Mode Detection**: Automatic configuration validation based on operation mode