# Dialogue Storage System

This document describes the dialogue storage system that automatically saves all chatbot conversations in a single, organized JSON file.

## Overview

The dialogue storage system automatically saves all chatbot conversations in a single, well-organized JSON file. Each session contains:
- Unique session ID (UUID)
- Creation timestamp
- All messages with timestamps
- Metadata (total messages, last updated)

## File Structure

```
Backend/
├── dialogues.json               # Single file containing all dialogue sessions
├── dialogue_storage.py          # Core storage functionality
└── app.py                       # API endpoints
```

## Storage JSON Format

All sessions are stored in a single JSON file with the following structure:

```json
{
  "metadata": {
    "created_at": "2025-07-07T20:41:35.737563",
    "last_updated": "2025-07-07T20:41:35.791094",
    "total_sessions": 2
  },
  "sessions": {
    "session-id-1": {
      "session_id": "session-id-1",
      "created_at": "2025-07-07T20:41:35.737563",
      "messages": [
        {
          "id": "message-uuid",
          "role": "user|assistant",
          "content": "Message content",
          "timestamp": "2025-07-07T20:41:35.751861"
        }
      ],
      "metadata": {
        "total_messages": 4,
        "last_updated": "2025-07-07T20:41:35.791094"
      }
    },
    "session-id-2": {
      "session_id": "session-id-2",
      "created_at": "2025-07-07T20:42:00.000000",
      "messages": [],
      "metadata": {
        "total_messages": 0,
        "last_updated": "2025-07-07T20:42:00.000000"
      }
    }
  }
}
```

## API Endpoints

### Chatbot Endpoints

- `POST /api/chatbot` - Send message to chatbot
  - Request: `{"message": "Hello", "session_id": "optional-session-id"}`
  - Response: `{"success": true, "response": "Bot response", "session_id": "session-id"}`

- `POST /api/chatbot/clear` - Clear current conversation history
  - Response: `{"success": true, "message": "История разговора очищена"}`

- `POST /api/chatbot/new-session` - Start a new dialogue session
  - Response: `{"success": true, "message": "Новая сессия создана", "session_id": "new-session-id"}`

### Dialogue Management Endpoints

- `GET /api/dialogues` - Get all dialogue sessions (summaries)
  - Response: `{"success": true, "sessions": [...]}`

- `GET /api/dialogues/<session_id>` - Get specific dialogue session
  - Response: `{"success": true, "session": {...}}`

- `DELETE /api/dialogues/<session_id>` - Delete specific dialogue session
  - Response: `{"success": true, "message": "Сессия удалена"}`

- `DELETE /api/dialogues/clear-all` - Delete all dialogue sessions
  - Response: `{"success": true, "message": "Все сессии удалены"}`

- `GET /api/dialogues/stats` - Get storage statistics
  - Response: `{"success": true, "stats": {"total_sessions": 5, "total_messages": 25, "file_size_mb": 0.15}}`

## Usage Examples

### Starting a New Session

```python
from chatbot_service import chatbot_service

# Start a new session
session_id = chatbot_service.start_new_session()
print(f"New session: {session_id}")
```

### Sending Messages

```python
# Send a message (will create session if none exists)
response = chatbot_service.generate_response("Hello!")
print(f"Response: {response}")

# Get current session ID
current_session = chatbot_service.get_current_session_id()
print(f"Current session: {current_session}")
```

### Managing Sessions

```python
from dialogue_storage import dialogue_storage

# Get all sessions
sessions = dialogue_storage.get_all_sessions()
for session in sessions:
    print(f"Session {session['session_id']}: {session['total_messages']} messages")

# Get specific session
session_data = dialogue_storage.get_session("session-id")
if session_data:
    for msg in session_data['messages']:
        print(f"{msg['role']}: {msg['content']}")

# Delete session
success = dialogue_storage.delete_session("session-id")
```

## Automatic Features

1. **Automatic Session Creation**: When you send a message without a session ID, a new session is automatically created.

2. **Message Persistence**: Every user message and bot response is automatically saved to the current session.

3. **Session Management**: Each conversation maintains its own session, allowing for multiple concurrent conversations.

4. **Metadata Tracking**: Sessions include metadata like total message count and last update time.

5. **Single File Storage**: All sessions are stored in one organized JSON file for easy management.

## Testing

Run the test script to verify the system works:

```bash
cd Backend
python test_dialogue_storage.py
```

This will create test sessions and verify all functionality.

## File Locations

- **Storage File**: `Backend/dialogues.json`
- **Core Module**: `Backend/dialogue_storage.py`
- **Integration**: `Backend/chatbot_service.py`
- **API Endpoints**: `Backend/app.py`

## Notes

- All sessions are stored in a single JSON file for easy backup and management
- Each message has a unique UUID for tracking
- Timestamps are in ISO format for easy parsing
- The system automatically handles file creation and structure management
- No database required - everything is stored in one organized JSON file
- File size and statistics are tracked for monitoring 