# YouTube to Notion Database Integration

A Python application that automatically adds YouTube video summaries to a Notion database with proper markdown formatting and rich text conversion.

## Features

- 🎥 **YouTube Integration**: Processes video metadata (title, URL, channel, cover image)
- 📝 **Markdown to Notion**: Converts markdown summaries to Notion's rich text format
- 🎨 **Rich Formatting**: Supports headers, bullet points, numbered lists, bold, and italic text
- 🖼️ **Cover Images**: Automatically adds video thumbnails as page covers
- 🧪 **Comprehensive Testing**: 17+ unit tests ensuring reliable markdown conversion
- 📁 **Professional Structure**: Organized, maintainable codebase following Python best practices

## Project Structure

```
youtube-notion-integration/
├── src/                          # Source code
│   ├── notion_db/               # Notion database operations
│   └── utils/                   # Utility modules (markdown converter)
├── tests/                       # Comprehensive test suite
├── config/                      # Configuration and example data
├── main.py                      # Main application entry point
└── requirements.txt             # Dependencies
```

## Prerequisites

- Python 3.8+
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
- **Summary** (Rich Text)
- **Video URL** (URL)
- **Channel** (Rich Text)
- **Tags** (Multi-select) - optional

### 4. Run the Application

```bash
python main.py
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
| Summary | Rich Text | Brief summary (truncated to 2000 chars) |
| Video URL | URL | YouTube video link |
| Channel | Rich Text | Channel name |
| Tags | Multi-select | Optional tags |

The full markdown summary will be added as the page content with proper formatting.

## Example Data

The application includes example data from a YouTube video about AI chunking strategies. Run the app to see how it converts markdown content with:

- Multiple heading levels
- Bullet points and numbered lists
- Bold and italic text formatting
- Complex nested content

## Testing

Run the comprehensive test suite:

```bash
# Unit tests for markdown conversion
python tests/test_markdown_converter.py

# Integration tests with example data
python tests/test_integration.py

# All tests with pytest (if installed)
pytest tests/
```

## Development

### Project Structure

- `src/notion_db/operations.py` - Database operations (find, create entries)
- `src/utils/markdown_converter.py` - Markdown to Notion conversion
- `tests/` - Unit and integration tests
- `config/example_data.py` - Sample data for testing

### Adding New Features

1. Add functionality to appropriate module in `src/`
2. Write tests in `tests/`
3. Update documentation

### Markdown Conversion Features

The markdown converter supports:

- **Headers**: `#`, `##`, `###` → Notion heading blocks
- **Lists**: `- item` and `1. item` → Notion list blocks
- **Formatting**: `**bold**` and `*italic*` → Notion rich text
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
- Ensure you're running from the project root directory
- Check that all dependencies are installed

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