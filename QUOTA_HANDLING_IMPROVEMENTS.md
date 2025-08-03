# Quota Handling Improvements

## Overview

I've implemented comprehensive improvements to handle Gemini API quota errors with proper retry delays, addressing the issue where the system would fail immediately instead of waiting for the API-specified retry delay.

## Key Improvements

### 1. Enhanced QuotaExceededError Exception

**File**: `src/youtube_notion/processors/exceptions.py`

- Added `retry_delay_seconds` parameter to store the delay from API response
- Added `raw_error` parameter to store the complete error for debugging
- Enhanced string representation to show retry delay information

```python
# Before: Basic quota error
QuotaExceededError("API quota exceeded")

# After: Enhanced with retry delay
QuotaExceededError(
    message="API quota exceeded", 
    retry_delay_seconds=18,  # From API response
    raw_error="Full API error response"
)
```

### 2. Retry Delay Parsing

**File**: `src/youtube_notion/processors/youtube_processor.py`

Added `_parse_retry_delay_from_error()` method that extracts retry delay from Gemini API error responses:

- Handles multiple formats: `'retryDelay': '18s'`, `"retryDelay": "18s"`, `retryDelay: 18s`
- Parses JSON structures within error messages
- Returns `None` if no retry delay is found (falls back to default retry logic)

**Example API Error Response**:
```json
{
  "error": {
    "details": [
      {
        "@type": "type.googleapis.com/google.rpc.RetryInfo",
        "retryDelay": "18s"
      }
    ]
  }
}
```

### 3. Intelligent Retry Logic

**File**: `src/youtube_notion/processors/youtube_processor.py`

Modified `_api_call_with_retry()` to:

- **Parse retry delays** from quota error responses
- **Wait for API-specified delay + 15 second buffer** before retrying
- **Continue processing** instead of failing immediately
- **Cap retry delays in test mode** to prevent long test hangs (5 seconds max)
- **Provide clear progress feedback** during waits

```python
# Production: Wait for full delay
"API quota exceeded. Waiting 33 seconds before retry (attempt 1/3)..."

# Test mode: Capped delay
"API quota exceeded. Test mode: waiting 5s (capped from 33s) before retry (attempt 1/3)..."
```

### 4. Test Mode Detection

Automatically detects test environments and caps retry delays:

- Checks for `PYTEST_CURRENT_TEST`, `TESTING`, or `_PYTEST_RAISE` environment variables
- Caps retry delays to 5 seconds maximum during testing
- Prevents test suite hangs while maintaining production behavior

### 5. Enhanced Error Messages

Improved error messages with actionable information:

```python
# Before
"Gemini API quota exceeded"

# After  
"Gemini API quota exceeded: [detailed error] | API: Gemini API | Quota Type: quota | Retry After: 18s"
```

### 6. Batch Processing Resilience

The improvements work seamlessly with existing batch processing:

- **Individual URL failures** don't stop the entire batch
- **Quota delays** are handled gracefully with progress feedback
- **Batch summary** shows successful vs failed URLs
- **Automatic retry** for quota errors with proper delays

## Usage Examples

### Single URL Processing
```bash
# Will automatically retry with proper delays if quota exceeded
python youtube_notion_cli.py --url "https://youtu.be/VIDEO_ID"
```

### Batch Processing
```bash
# Will continue processing other URLs even if some hit quota limits
python youtube_notion_cli.py --urls "url1,url2,url3"
python youtube_notion_cli.py --file urls.txt
```

### Expected Output During Quota Handling
```
Processing YouTube video: https://youtu.be/abc123
API quota exceeded. Waiting 33 seconds before retry (attempt 1/3)...
✓ Successfully processed video: Example Video Title
✓ Added to Notion: Example Video Title
```

## Technical Details

### Retry Delay Calculation
```python
# API returns: retryDelay: "18s"
# System waits: 18 + 15 = 33 seconds
# Reasoning: 15-second buffer ensures we don't retry too early
```

### Test Mode Behavior
```python
# Production: Wait full delay (18 + 15 = 33 seconds)
# Test mode: Cap to 5 seconds maximum
# Prevents test suite from hanging for minutes
```

### Error Flow
1. **API Call** → Quota exceeded with `retryDelay: "18s"`
2. **Parse Delay** → Extract 18 seconds from error response
3. **Calculate Wait** → 18 + 15 = 33 seconds total
4. **Wait & Retry** → Sleep for 33 seconds, then retry
5. **Continue** → Process next URL or complete successfully

## Backward Compatibility

- All existing functionality remains unchanged
- New retry behavior only activates when API provides retry delay
- Falls back to original exponential backoff if no retry delay specified
- Existing error handling and batch processing work as before

## Testing

The improvements include comprehensive test coverage:

- ✅ Retry delay parsing from various error formats
- ✅ Test mode detection and delay capping
- ✅ Enhanced error message generation
- ✅ Integration with existing retry logic
- ✅ Batch processing resilience

## Benefits

1. **Improved Success Rate**: Respects API retry delays instead of failing immediately
2. **Better User Experience**: Clear progress feedback during waits
3. **Batch Processing Resilience**: Continues processing other URLs during quota delays
4. **Test Suite Stability**: Prevents long hangs during testing
5. **Production Ready**: Handles real-world quota scenarios gracefully

## Files Modified

- `src/youtube_notion/processors/exceptions.py` - Enhanced QuotaExceededError
- `src/youtube_notion/processors/youtube_processor.py` - Retry logic and delay parsing
- `tests/test_cli.py` - Fixed CLI test assertions
- `tests/test_youtube_end_to_end.py` - Updated hanging tests to handle quota errors

The system now handles quota limits intelligently, making it much more robust for production use while maintaining fast test execution.