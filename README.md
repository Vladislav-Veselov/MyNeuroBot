# NeuroBot - Intelligent RAG Chatbot

A sophisticated web application featuring an intelligent chatbot powered by OpenAI GPT-3.5 with Retrieval-Augmented Generation (RAG) capabilities. This application provides a modern, user-friendly interface to interact with your knowledge base using advanced AI.

## Features

- 🤖 **Intelligent Chatbot**: Powered by OpenAI GPT-3.5 with RAG capabilities
- 📚 **Knowledge Base Management**: View, edit, and manage Q&A pairs
- 🔍 **Semantic Search**: Advanced vector-based search using FAISS
- ⚙️ **Customizable Settings**: Adjust tone, humor, and brevity levels
- 📊 **Analytics Dashboard**: View knowledge base statistics
- 🎨 **Modern UI**: Clean, responsive design with dark theme
- 🔄 **Conversation Memory**: Maintains context across chat sessions
- 🧹 **Chat Management**: Clear conversation history functionality

## Setup

1. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
cd Backend
pip install -r requirements.txt
```

3. Set up your environment variables:
Create a `.env` file in the Backend directory with your OpenAI API key:
```
OPENAI_API_KEY=your-api-key-here
```

## Running the Application

1. Start the Flask server:
```bash
cd Backend
python app.py
```

2. Open your web browser and navigate to:
```
http://localhost:5000
```

## Project Structure

```
NeuroBot/
├── Backend/
│   ├── app.py                 # Main Flask application
│   ├── chatbot_service.py     # OpenAI GPT-3.5 chatbot service
│   ├── vectorize.py           # Vector store management
│   ├── requirements.txt       # Python dependencies
│   ├── knowledge.txt          # Knowledge base Q&A pairs
│   ├── system_prompt.txt      # Chatbot behavior settings
│   ├── vector_KB/            # FAISS vector store
│   └── tests/                # Test files
│       ├── test_chatbot.py
│       └── test_chatbot_api.py
├── Frontend/
│   ├── static/
│   │   ├── css/
│   │   │   ├── style.css     # Base styles
│   │   │   ├── viewer.css    # Viewer page styles
│   │   │   └── chatbot.css   # Chatbot styles
│   │   ├── js/
│   │   │   ├── main.js       # Main frontend logic
│   │   │   ├── viewer.js     # Viewer functionality
│   │   │   ├── chatbot.js    # Chatbot frontend
│   │   │   └── settings.js   # Settings management
│   │   └── logo.png          # Application logo
│   └── templates/
│       ├── viewer.html       # Knowledge base viewer
│       ├── chatbot.html      # Chatbot interface
│       ├── settings.html     # Settings page
│       ├── analytics.html    # Analytics dashboard
│       └── about.html        # About page
└── README.md
```

## Usage

### Chatbot Interface
1. Navigate to the Chatbot page
2. Type your question in the chat input
3. The AI will search the knowledge base and provide intelligent responses
4. Use the "Clear Chat" button to start a new conversation

### Knowledge Base Management
1. Use the Viewer page to browse and edit Q&A pairs
2. Add new questions and answers through the interface
3. Search and filter content as needed

### Settings
1. Adjust chatbot behavior in the Settings page:
   - **Tone**: Choose between friendly, formal, casual, or professional
   - **Humor**: Set humor level from 0 (none) to 5 (very active)
   - **Brevity**: Control response length from 0 (very detailed) to 5 (very brief)
   - **Additional Prompt**: Add custom instructions for the AI

## API Endpoints

- `POST /api/chatbot` - Send a message to the chatbot
- `POST /api/chatbot/clear` - Clear conversation history
- `GET /api/documents` - Get knowledge base documents
- `POST /api/add_qa` - Add new Q&A pair
- `GET /api/settings` - Get chatbot settings
- `POST /api/save_settings` - Save chatbot settings

## Technical Details

- **AI Model**: OpenAI GPT-3.5-turbo for natural language generation
- **Embeddings**: OpenAI text-embedding-3-large for semantic search
- **Vector Store**: FAISS for efficient similarity search
- **Conversation Memory**: Maintains context across chat sessions
- **RAG Implementation**: Retrieval-Augmented Generation for accurate responses

## Notes

- The application requires a valid OpenAI API key in the `.env` file
- Vector store is automatically rebuilt when knowledge base changes
- Chatbot responses are based solely on the provided knowledge base
- Conversation history is maintained in memory and can be cleared 

# Contributing

Contributions are welcome! Please open issues or pull requests for bug fixes, features, or suggestions.

# License

This project is licensed under the MIT License. See the LICENSE file for details. 