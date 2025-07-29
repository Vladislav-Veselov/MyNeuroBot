# NeuroBot 🤖

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/Flask-3.0.2-green.svg)](https://flask.palletsprojects.com/)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--3.5-orange.svg)](https://openai.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A sophisticated web application featuring an intelligent chatbot powered by OpenAI GPT-3.5 with Retrieval-Augmented Generation (RAG) capabilities. This application provides a modern, user-friendly interface to interact with your knowledge base using advanced AI.

## ✨ Features

- 🤖 **Intelligent Chatbot**: Powered by OpenAI GPT-3.5 with RAG capabilities
- 📚 **Knowledge Base Management**: View, edit, and manage Q&A pairs
- 🔍 **Semantic Search**: Advanced vector-based search using FAISS
- ⚙️ **Customizable Settings**: Adjust tone, humor, and brevity levels
- 📊 **Analytics Dashboard**: View knowledge base statistics
- 🎨 **Modern UI**: Clean, responsive design with dark theme
- 🔄 **Conversation Memory**: Maintains context across chat sessions
- 🧹 **Chat Management**: Clear conversation history functionality
- 🔒 **Secure**: Environment-based API key management

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- OpenAI API key ([Get one here](https://platform.openai.com/api-keys))

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/NeuroBot.git
   cd NeuroBot
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   
   Create a `.env` file in the `Backend` directory:
   ```bash
   cd Backend
   echo OPENAI_API_KEY=your-api-key-here > .env
   ```

5. **Set up user data structure (optional)**
   
   Run the setup script to create the user data directory structure:
   ```bash
   python setup_user_data.py
   ```

6. **Run the application**
   ```bash
   python app.py
   ```

6. **Open your browser**
   
   Navigate to: `http://localhost:5000`

7. **Create your account**
   
   - Click "Sign up" to create your account
   - Or use the existing admin account (if available)
   - Each user gets their own personal data directory

## 📁 Project Structure

```
NeuroBot/
├── Backend/                    # Flask backend application
│   ├── app.py                 # Main Flask application
│   ├── chatbot_service.py     # OpenAI GPT-3.5 chatbot service
│   ├── vectorize.py           # Vector store management
│   ├── dialogue_storage.py    # Conversation storage
│   ├── retrieve.py            # Retrieval logic
│   ├── requirements.txt       # Python dependencies
│   ├── system_prompt.txt      # Chatbot behavior settings
│   └── tests/                # Test suite
│       ├── test_chatbot.py
│       ├── test_chatbot_api.py
│       └── test_retrieval.py
├── Frontend/                  # Web interface
│   ├── static/
│   │   ├── css/
│   │   │   ├── style.css     # Base styles
│   │   │   ├── viewer.css    # Viewer page styles
│   │   │   ├── chatbot.css   # Chatbot styles
│   │   │   └── analytics.css # Analytics styles
│   │   ├── js/
│   │   │   ├── main.js       # Main frontend logic
│   │   │   ├── viewer.js     # Viewer functionality
│   │   │   ├── chatbot.js    # Chatbot frontend
│   │   │   ├── settings.js   # Settings management
│   │   │   └── analytics.js  # Analytics dashboard
│   │   └── logo.png          # Application logo
│   └── templates/
│       ├── index.html        # Home page
│       ├── viewer.html       # Knowledge base viewer
│       ├── chatbot.html      # Chatbot interface
│       ├── settings.html     # Settings page
│       ├── analytics.html    # Analytics dashboard
│       └── about.html        # About page
├── user_data/                # User-specific data
│   └── admin/               # Admin user data
│       ├── knowledge.txt     # Knowledge base Q&A pairs
│       ├── dialogues.json    # Conversation history
│       ├── users.json        # User data
│       ├── last_fingerprint.json # System fingerprint
│       ├── system_prompt.txt # Chatbot behavior settings
│       └── vector_KB/       # FAISS vector store (auto-generated)
├── requirements.txt           # Root dependencies
├── README.md                 # This file
├── LICENSE                   # MIT License
└── .gitignore               # Git ignore rules
```

## 🔐 Authentication

NeuroBot now includes user authentication with the following features:

- **User Registration**: Create new accounts with username and password
- **User Login**: Secure login with session management
- **Personal Data**: Each user gets their own data directory
- **Session Management**: Automatic session handling with Flask sessions

### User Data Isolation

Each user has their own personal data directory:
- `user_data/{username}/knowledge.txt` - Personal knowledge base
- `user_data/{username}/dialogues.json` - Personal conversation history
- `user_data/{username}/system_prompt.txt` - Personal chatbot settings
- `user_data/{username}/vector_KB/` - Personal vector store

## 🎯 Usage

### Getting Started
1. **Sign up** for a new account or **login** with existing credentials
2. **Access your personal dashboard** with your own data
3. **Customize your chatbot** settings in the Settings page

### Chatbot Interface
1. Navigate to the **Chatbot** page
2. Type your question in the chat input
3. The AI will search the knowledge base and provide intelligent responses
4. Use the "Clear Chat" button to start a new conversation

### Knowledge Base Management
1. Use the **Viewer** page to browse and edit Q&A pairs
2. Add new questions and answers through the interface
3. Search and filter content as needed
4. The vector store automatically rebuilds when knowledge base changes

### Settings Configuration
1. Adjust chatbot behavior in the **Settings** page:
   - **Tone**: Choose between friendly, formal, casual, or professional
   - **Humor**: Set humor level from 0 (none) to 5 (very active)
   - **Brevity**: Control response length from 0 (very detailed) to 5 (very brief)
   - **Additional Prompt**: Add custom instructions for the AI

### Analytics Dashboard
1. View knowledge base statistics in the **Analytics** page
2. Monitor usage patterns and system performance

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/chatbot` | Send a message to the chatbot |
| `POST` | `/api/chatbot/clear` | Clear conversation history |
| `GET` | `/api/documents` | Get knowledge base documents |
| `POST` | `/api/add_qa` | Add new Q&A pair |
| `GET` | `/api/settings` | Get chatbot settings |
| `POST` | `/api/save_settings` | Save chatbot settings |

## 🛠️ Technical Details

### Core Technologies
- **Backend**: Flask 3.0.2
- **AI Model**: OpenAI GPT-3.5-turbo
- **Embeddings**: OpenAI text-embedding-3-large
- **Vector Store**: FAISS (Facebook AI Similarity Search)
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **Styling**: Custom CSS with responsive design

### Key Features
- **RAG Implementation**: Retrieval-Augmented Generation for accurate responses
- **Semantic Search**: Vector-based similarity search using FAISS
- **Conversation Memory**: Maintains context across chat sessions
- **Real-time Updates**: Vector store rebuilds automatically
- **Cross-platform**: Works on Windows, macOS, and Linux

## 🧪 Testing

Run the test suite:

```bash
cd Backend
python -m pytest tests/
```

## 🔧 Configuration

### User Data Structure

NeuroBot stores all user-specific data in the `user_data/admin/` directory:

- **knowledge.txt**: Knowledge base Q&A pairs
- **dialogues.json**: Conversation history and session data
- **users.json**: User management data
- **last_fingerprint.json**: System fingerprint for vector store updates
- **system_prompt.txt**: Chatbot behavior settings (user-specific)
- **vector_KB/**: FAISS vector store (auto-generated from knowledge base)

This separation ensures that:
- User data is isolated from application code
- Data can be easily backed up or migrated
- Multiple users can have separate data directories
- Application updates don't affect user data

### Environment Variables

Create a `.env` file in the `Backend` directory:

```env
OPENAI_API_KEY=your-openai-api-key-here
```

### Knowledge Base

The knowledge base is stored in `user_data/admin/knowledge.txt` in Q&A format:

```
Q: What is NeuroBot?
A: NeuroBot is an intelligent chatbot powered by OpenAI GPT-3.5 with RAG capabilities.

Q: How does it work?
A: It uses semantic search to find relevant information and generates responses using GPT-3.5.
```

## 🤝 Contributing

We welcome contributions! Please feel free to submit issues and pull requests.

### How to Contribute

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup

1. Follow the installation steps above
2. Install development dependencies:
   ```bash
   pip install pytest pytest-cov
   ```
3. Run tests with coverage:
   ```bash
   python -m pytest tests/ --cov=.
   ```

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- OpenAI for providing the GPT-3.5 API
- FAISS for efficient vector similarity search
- Flask for the web framework
- The open-source community for inspiration and tools

## 📞 Support

If you encounter any issues or have questions:

1. Check the [Issues](https://github.com/yourusername/NeuroBot/issues) page
2. Create a new issue with detailed information
3. Include your Python version, OS, and error messages

---

**Made with ❤️ by the NeuroBot team** 