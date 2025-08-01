# YouTube to Notion Database Integration

A Python application that automatically adds YouTube video summaries to a Notion database with proper markdown formatting and rich text conversion.

## Features

- 🎥 **YouTube Integration**: Processes video metadata (title, URL, channel, cover image)
- 📺 **Embedded Videos**: Automatically embeds YouTube videos at the top of each page
- ⏰ **Smart Timestamps**: Converts timestamps like `[8:05]` or `[8:05-8:24]` to clickable YouTube links
- 📝 **Markdown to Notion**: Converts markdown summaries to Notion's rich text format
- 🎨 **Rich Formatting**: Supports headers, bullet points, numbered lists, bold, and italic text
- 🖼️ **Cover Images**: Automatically adds video thumbnails as page covers
- 🧪 **Comprehensive Testing**: 50+ unit tests ensuring reliable functionality
- 📁 **Professional Structure**: Organized, maintainable codebase following Python best practices

## Project Structure

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

## Prerequisites

- Python 3.12+
- Notion account with API access
- A Notion database named "YT Summaries" in a page called "YouTube Knowledge Base"

## Quick Start

### 1. Clone and Setup

```bash
git clone <repository-url>
cd youtube-notion-integration
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your Notion token
NOTION_TOKEN=your_notion_integration_token_here
```

### 3. Set Up Notion Database

Create a Notion database with these properties:
- **Title** (Title)
- **Video URL** (URL)
- **Channel** (Rich Text)
- **Tags** (Multi-select) - optional

The full summary content will be added as the page content with proper markdown formatting.

### 4. Run the Application

```bash
# Option 1: Use the CLI script
python youtube_notion_cli.py

# Option 2: Install as package and use entry point
pip install -e .
youtube-notion

# Option 3: Run as module
python -m youtube_notion.main
```

## Getting a Notion Integration Token

1. Visit [Notion Integrations](https://www.notion.so/my-integrations)
2. Click "New integration"
3. Name your integration (e.g., "YouTube Summaries")
4. Copy the "Internal Integration Token"
5. Share your database with the integration:
   - Open your Notion database
   - Click "Share" → "Invite"
   - Select your integration

## Database Schema

Your Notion database should have these properties:

| Property Name | Type | Description |
|---------------|------|-------------|
| Title | Title | Video title |
| Video URL | URL | YouTube video link |
| Channel | Rich Text | Channel name |
| Tags | Multi-select | Optional tags |

Each page will contain:
1. **Embedded YouTube video** at the top for easy viewing
2. **Visual divider** for clean separation
3. **Full markdown summary** with smart features:
   - **Clickable timestamps** that jump to specific moments in the video
   - **Rich formatting** (headers, lists, bold/italic text, etc.)
   - **Proper Notion block structure** for optimal readability

## Example Data

The application includes example data from a YouTube video about AI chunking strategies. Run the app to see how it creates a complete Notion page with:

- **Embedded YouTube video** at the top for immediate viewing
- **Visual divider** separating video from content
- **Formatted summary** with:
  - **Clickable timestamps** that jump to video moments
  - Multiple heading levels (H1-H6 supported)
  - Bullet points and numbered lists
  - Bold and italic text formatting
  - Complex nested content

## Testing

First, ensure all dependencies are installed:

```bash
pip install -r requirements.txt
```

Run the comprehensive test suite:

```bash
# Easy way - use the test runner (handles path setup automatically)
python run_tests.py

# Manual way with pytest (recommended):
python -m pytest tests/ -v

# Or install the package in development mode first:
pip install -e .
pytest tests/ -v
```

The test runner will automatically:
- Set up the correct Python path for the package structure
- Try to use pytest if available
- Fall back to running tests individually if pytest isn't installed

**Note**: The project now uses a proper Python package structure, eliminating the need for manual path manipulation that was required in the previous version.

### Benefits of the New Structure

- **Clean imports**: No more `sys.path` manipulation needed
- **Standard packaging**: Follows modern Python best practices
- **IDE-friendly**: Better autocomplete and code navigation
- **Installable**: Can be installed as a proper Python package
- **Maintainable**: Clear separation of concerns and modules

## Smart Timestamp Features

The application automatically detects and enhances timestamps in your markdown content:

### Supported Formats
- **Single timestamp**: `[8:05]` → Links to 8 minutes 5 seconds
- **Time range**: `[8:05-8:24]` → Links to start time (8:05)
- **Multiple timestamps**: `[0:01-0:07, 0:56-1:21]` → Creates separate links for each

### How It Works
1. **Detection**: Finds timestamp patterns in square brackets
2. **Parsing**: Converts time to seconds (supports MM:SS and HH:MM:SS)
3. **Linking**: Creates YouTube URLs with `&t=XXXs` parameter
4. **Integration**: Works with both standard and short YouTube URLs
5. **Rich Text**: Timestamps become clickable links in all contexts (headers, paragraphs, lists)

### Example
```markdown
#### The High Cost of Bad Chunking [0:01-0:07, 0:56-1:21]
```

Becomes:
```markdown
#### The High Cost of Bad Chunking [0:01-0:07](https://youtube.com/watch?v=VIDEO_ID&t=1s), [0:56-1:21](https://youtube.com/watch?v=VIDEO_ID&t=56s)
```

## Development

### Package Structure

- `src/youtube_notion/main.py` - Application entry point
- `src/youtube_notion/notion_db/operations.py` - Database operations (find, create entries)
- `src/youtube_notion/utils/markdown_converter.py` - Markdown to Notion conversion
- `src/youtube_notion/config/example_data.py` - Sample data for testing
- `tests/` - Unit and integration tests
- `youtube_notion_cli.py` - Command-line interface script

### Adding New Features

1. Add functionality to appropriate module in `src/youtube_notion/`
2. Write tests in `tests/` (imports use `from youtube_notion.module import ...`)
3. Update documentation

### Installation for Development

```bash
# Install in development mode (recommended)
pip install -e .

# This allows you to:
# - Import the package from anywhere: `from youtube_notion import ...`
# - Use the CLI command: `youtube-notion`
# - Make changes without reinstalling
```

### Markdown Conversion Features

The markdown converter supports:

- **Headers**: `#`, `##`, `###`, `####`, `#####`, `######` → Notion heading blocks
  - H1 (`#`) → Notion Heading 1
  - H2 (`##`) → Notion Heading 2  
  - H3+ (`###`, `####`, etc.) → Notion Heading 3 (Notion only supports 3 levels)
- **Lists**: `- item` and `1. item` → Notion list blocks
- **Formatting**: `**bold**` and `*italic*` → Notion rich text
- **Links**: `[text](url)` → Clickable Notion links (supports formatting within links)
- **Timestamps**: `[8:05]`, `[8:05-8:24]`, `[0:01-0:07, 0:56-1:21]` → Clickable YouTube timestamp links
- **Paragraphs**: Regular text → Notion paragraph blocks

## Troubleshooting

### Common Issues

**"Database not found"**
- Ensure database is named exactly "YT Summaries"
- Check that it's in a page named "YouTube Knowledge Base"
- Verify the integration has access to the database

**"Property does not exist"**
- Check database properties match the required schema
- Property names are case-sensitive

**Import errors**
- Install the package in development mode: `pip install -e .`
- Or ensure you're running from the project root with proper Python path
- Check that all dependencies are installed: `pip install -r requirements.txt`

### Debug Mode

Add debug output by modifying the database operations to print more information about the database structure and properties.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Acknowledgments

- Built with the official [Notion Python SDK](https://github.com/ramnes/notion-sdk-py)
- Inspired by the need to organize YouTube learning content in Notion