# NeuroBot Test Suite

This directory contains comprehensive tests for the NeuroBot viewer and database functionality.

## Test Files

- `test_viewer_and_db.py` - Main comprehensive test script
- `run_tests.py` - Simple test runner with automatic server management
- `tests/` - Individual test modules

## Quick Start

### Option 1: Using the Test Runner (Recommended)

```bash
cd Backend
python run_tests.py
```

This will:
- Check dependencies
- Start the Flask server automatically (if not running)
- Run all tests
- Generate a comprehensive report
- Clean up test files

### Option 2: Manual Testing

1. Start the Flask server:
```bash
cd Backend
python app.py
```

2. In another terminal, run the tests:
```bash
cd Backend
python test_viewer_and_db.py
```

### Option 3: Individual Test Modules

```bash
# Test dialogue storage
python tests/test_dialogue_storage.py

# Test chatbot API
python tests/test_chatbot_api.py

# Test chatbot service
python tests/test_chatbot.py

# Test retrieval functionality
python tests/test_retrieval.py
```

## What the Tests Cover

### Viewer Functionality Tests
- ✅ Document retrieval and pagination
- ✅ Search functionality (exact and semantic)
- ✅ Document CRUD operations (Create, Read, Update, Delete)
- ✅ Statistics and analytics
- ✅ Frontend page accessibility

### Database Functionality Tests
- ✅ Dialogue session creation and management
- ✅ Message storage and retrieval
- ✅ Session statistics and metadata
- ✅ Session deletion and cleanup
- ✅ Storage statistics

### API Endpoint Tests
- ✅ Chatbot message handling
- ✅ Session management
- ✅ Settings management
- ✅ Dialogue storage API
- ✅ Error handling

### Frontend Tests
- ✅ Page accessibility
- ✅ Navigation functionality
- ✅ Modal interactions
- ✅ Form submissions

## Test Categories

### 1. Viewer Endpoints (`test_viewer_endpoints`)
- `GET /api/documents` - Basic document retrieval
- `GET /api/documents?page=1&search=` - Pagination
- `GET /api/documents?search=test` - Search functionality
- `GET /api/document/0` - Specific document retrieval
- `GET /api/stats` - Statistics
- `POST /api/add_qa` - Add new Q&A
- `PUT /api/document/0` - Update document
- `GET /api/semantic_search?query=test` - Semantic search

### 2. Database Functionality (`test_database_functionality`)
- Session creation and management
- Message storage and retrieval
- Session statistics
- Session cleanup and deletion
- Storage metadata

### 3. Chatbot API (`test_chatbot_api`)
- `POST /api/chatbot` - Send messages
- `POST /api/chatbot/clear` - Clear history
- `POST /api/chatbot/new-session` - Start new session
- `GET /api/dialogues` - Get all dialogues
- `GET /api/dialogues/stats` - Dialogue statistics

### 4. Settings API (`test_settings_api`)
- `GET /api/get_settings` - Retrieve settings
- `POST /api/save_settings` - Save settings

### 5. Frontend Pages (`test_frontend_pages`)
- Home/Viewer page
- Chatbot page
- Settings page
- Analytics page
- About page

## Test Output

The test suite provides detailed output including:

```
🚀 Starting NeuroBot Viewer and Database Tests
============================================================
TESTING VIEWER FUNCTIONALITY
============================================================
✅ PASS Get Documents (Basic)
   Status: 200, Documents: 15

✅ PASS Get Documents (Pagination)
   Page: 1, Total: 2, Items: 15

❌ FAIL Semantic Search
   Exception: Connection timeout

============================================================
TEST SUMMARY
============================================================
Total Tests: 25
Passed: 23
Failed: 2
Success Rate: 92.0%
```

## Configuration

### Environment Variables
Make sure you have the following environment variables set:
- `OPENAI_API_KEY` - Your OpenAI API key (for chatbot functionality)

### Test Configuration
You can modify the test configuration in `test_viewer_and_db.py`:

```python
# Change the base URL if your server runs on a different port
tester = NeuroBotTester("http://localhost:5001")  # Default port is 5001

# Add custom test data
test_qa = {
    "question": "Your custom test question?",
    "answer": "Your custom test answer."
}
```

## Troubleshooting

### Common Issues

1. **Server not running**
   ```
   ❌ ERROR: Flask server is not running!
   Please start the server with: python app.py
   ```
   Solution: Start the Flask server first

2. **Missing dependencies**
   ```
   ❌ Missing required packages: requests flask-cors
   ```
   Solution: Install missing packages with `pip install requests flask-cors`

3. **Connection timeout**
   ```
   ❌ FAIL Semantic Search
   Exception: Connection timeout
   ```
   Solution: Check if the vector store is properly initialized

4. **Permission errors**
   ```
   ❌ Error: Could not clean up test files
   ```
   Solution: Check file permissions in the Backend directory

### Debug Mode

To run tests with verbose output:
```bash
python test_viewer_and_db.py --verbose
```

### Manual Server Testing

If you want to test the server manually:
```bash
# Start server
cd Backend
python app.py

# In another terminal, test specific endpoints
curl http://localhost:5001/api/documents
curl http://localhost:5001/api/stats
```

## Test Data

The test suite creates temporary test data:
- Test dialogue sessions in `test_dialogues.json`
- Test Q&A pairs in the knowledge base
- Temporary session data

All test data is automatically cleaned up after tests complete.

## Extending the Tests

To add new tests:

1. Add test methods to the `NeuroBotTester` class
2. Call them from `run_all_tests()`
3. Use the `log_test()` method for consistent output

Example:
```python
def test_new_feature(self):
    """Test a new feature."""
    try:
        # Your test code here
        success = True
        message = "Feature working correctly"
    except Exception as e:
        success = False
        message = f"Exception: {str(e)}"
    
    self.log_test("New Feature Test", success, message)
```

## Performance Notes

- Tests typically complete in 30-60 seconds
- Server startup adds 3-5 seconds
- Large knowledge bases may slow down search tests
- Vector store operations may take longer on first run

## Continuous Integration

For CI/CD integration, the test suite returns:
- Exit code 0 for success
- Exit code 1 for failure
- Detailed JSON output available via `--json` flag (planned feature) 