# Integration Tests

This directory contains integration tests that verify the complete YouTube-to-Notion processing pipeline using real APIs and test databases.

## Setup Requirements

### 1. Test Environment Configuration

Integration tests require a separate `.env-test` file in the project root with test-specific API keys and configuration:

```bash
# Test environment configuration
NOTION_TOKEN=your_test_notion_token_here
DATABASE_NAME=YT Summaries [TEST]
PARENT_PAGE_NAME=YouTube Summaries [TEST]

GEMINI_API_KEY=your_test_gemini_api_key_here
GEMINI_MODEL=gemini-2.0-flash-exp
GEMINI_TEMPERATURE=0.7
GEMINI_MAX_OUTPUT_TOKENS=8192

YOUTUBE_API_KEY=your_test_youtube_api_key_here

# Test-specific settings
DEBUG=true
VERBOSE=false
YOUTUBE_PROCESSOR_MAX_RETRIES=2
YOUTUBE_PROCESSOR_TIMEOUT=60
TEST_MODE=true
```

### 2. Test Database Setup

Integration tests automatically create and manage test databases in Notion:

- **Database Name**: `YT Summaries [TEST]`
- **Parent Page**: `YouTube Summaries [TEST]`
- **Cleanup**: Automatic cleanup before and after each test

### 3. API Keys

You'll need test API keys for:

- **Notion**: Create a test integration at https://www.notion.so/my-integrations
- **Gemini**: Use your Google AI Studio API key (same as production, but with test data)
- **YouTube** (optional): YouTube Data API key for metadata extraction

## Running Integration Tests

### Using the Integration Test Runner (Recommended)

```bash
# Run all integration tests
python run_integration_tests.py

# Skip slow tests
python run_integration_tests.py --fast

# Verbose output
python run_integration_tests.py --verbose

# Stop on first failure
python run_integration_tests.py -x
```

### Using pytest directly

```bash
# Run all integration tests
python -m pytest tests/integration/ -m integration

# Run specific test file
python -m pytest tests/integration/test_end_to_end_integration.py -v

# Skip slow tests
python -m pytest tests/integration/ -m "integration and not slow"
```

## Test Categories

### Setup Validation Tests (`test_setup_validation.py`)
- Verify test environment configuration
- Check API key availability
- Test database setup and cleanup
- Validate test isolation

### End-to-End Integration Tests (`test_end_to_end_integration.py`)
- Complete video processing pipeline
- Component integration testing
- Error scenario testing
- Performance testing

### Component Integration Tests
- Individual component testing with real APIs
- Metadata extraction with YouTube API
- Summary generation with Gemini API
- Storage operations with Notion API

## Test Features

### Automatic Database Management
- Creates test databases automatically
- Cleans up test data before and after each test
- Ensures test isolation
- Uses `[TEST]` naming convention

### Configuration Safety
- **Never uses production `.env` file**
- Requires `TEST_MODE=true` in `.env-test`
- Validates API keys are not placeholders
- Prevents accidental production data modification

### Error Handling
- Tests network resilience and retry logic
- Validates error scenarios with real APIs
- Tests configuration error handling
- Verifies graceful degradation

## Test Fixtures

### Session-scoped Fixtures
- `integration_config`: Test configuration from `.env-test`
- `notion_client`: Authenticated Notion client
- `test_database_setup`: Test database creation and info

### Function-scoped Fixtures
- `clean_test_database`: Database cleanup before/after each test
- `skip_if_no_api_keys`: Skip tests when API keys unavailable
- `test_video_data`: Sample test data for video processing

## Best Practices

### Writing Integration Tests
1. Always use the `@pytest.mark.integration` marker
2. Use appropriate fixtures for setup and cleanup
3. Test with real APIs but use stable test data
4. Include error scenario testing
5. Verify complete workflows, not just happy paths

### Test Data
- Use well-known, stable YouTube videos for testing
- Avoid copyrighted or potentially problematic content
- Use short videos to minimize API costs
- Include various URL formats in tests

### Performance Considerations
- Mark slow tests with `@pytest.mark.slow`
- Use timeouts for API calls
- Minimize API calls where possible
- Test performance with realistic data sizes

## Troubleshooting

### Common Issues

**"ERROR: .env-test file not found"**
- Create `.env-test` file in project root
- Copy from `.env.example` and update with test values

**"Missing or placeholder values in .env-test"**
- Replace placeholder values with real API keys
- Ensure `TEST_MODE=true` is set

**"Database setup failed"**
- Check Notion token permissions
- Verify Notion integration has database access
- Ensure parent page exists and is accessible

**"API quota exceeded"**
- Use test API keys with sufficient quotas
- Run tests less frequently
- Use `--fast` flag to skip slow tests

**"Tests are not isolated"**
- Check that `clean_test_database` fixture is used
- Verify test database names contain `[TEST]`
- Ensure `TEST_MODE=true` in configuration

### Debug Mode

Enable debug output by setting `DEBUG=true` in `.env-test`:

```bash
DEBUG=true
VERBOSE=true
```

This provides additional logging and error details during test execution.

## Security Notes

- **Never commit `.env-test` with real API keys**
- Use separate test API keys from production
- Test databases should be clearly marked with `[TEST]`
- Integration tests should never modify production data
- API keys in `.env-test` should have minimal necessary permissions