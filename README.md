# OpenCode UI

A modern web interface and CLI tool for interacting with the OpenCode API, featuring a Vue.js frontend and FastAPI backend.

## Features

### Web UI (Vue.js)
- 🎨 **Modern Interface** - Clean, responsive design with Tailwind CSS
- 💬 **Interactive Chat** - Real-time messaging with markdown support
- 📁 **Session Management** - Create, switch, and manage chat sessions
- 💾 **Persistent Chat History** - Conversations automatically saved locally
- ⚡ **Fast & Reactive** - Built with Vue 3 and Vite

### CLI Tool
- 🔌 **API Integration** - Direct integration with OpenCode API
- 📁 **Session Management** - List, create, and manage OpenCode sessions
- 💬 **Chat Functionality** - Send prompts and receive responses
- 🧪 **Testing Tools** - Built-in test cases for chat functionality
- 🐍 **Python Native** - Pure Python implementation with type hints

## Quick Start

### Web UI (Recommended)

1. **Check Environment:**
```bash
python check_env.py
```

2. **Install Dependencies:**
```bash
# Python backend
pip install -r requirements.txt

# Vue.js frontend
cd ui
npm install
cd ..
```

3. **Start Development Servers:**

**Windows PowerShell:**
```powershell
.\start-dev.ps1
```

**Linux/Mac:**
```bash
chmod +x start-dev.sh
./start-dev.sh
```

**Or manually:**
```bash
# Terminal 1 - Backend
python -m uvicorn app.main:app --reload --port 8000

# Terminal 2 - Frontend
cd ui
npm run dev
```

4. **Access the Application:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Docker Setup

For containerized deployment:

1. **Environment Setup:**
```bash
cp .env.example .env
# Edit .env with your configuration
# Note: Backend connects to real OpenCode service
```

2. **Build and Run:**
```bash
# Build and start all services
docker-compose up --build

# Or run in background
docker-compose up -d --build
```

3. **Access the Application:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

4. **Stop Services:**
```bash
docker-compose down
```

**Note:** The UI can only interact with existing OpenCode sessions. Session creation must be done through the OpenCode CLI first.

### CLI Tool

Install dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

Set environment variables:

```bash
# OpenCode settings
export OPENCODE_BASE_URL=http://localhost:4096
export OPENCODE_API_KEY=your-api-key  # optional
```

## Usage

### CLI Tester

The main CLI tool for testing and interacting with OpenCode:

```bash
# Test connection
python cli_tester.py --test-connection

# List all sessions
python cli_tester.py --list-sessions

# List sessions with detailed information
python cli_tester.py --list-sessions --detailed

# Get details of a specific session
python cli_tester.py --session-details <session_id>

# Send a chat message
python cli_tester.py --chat <session_id> "Hello, how are you?"

# Get server information
python cli_tester.py --server-info
```

### Chat Test Case

Run comprehensive chat functionality tests:

```bash
python chat_test_case.py
```

## Project Structure

```
opencode-ui/
├── ui/                         # Vue.js Web Application
│   ├── src/
│   │   ├── components/        # Vue components
│   │   ├── stores/            # Pinia state management
│   │   ├── services/          # API client
│   │   ├── views/             # Route views
│   │   └── router/            # Vue Router
│   ├── package.json
│   └── vite.config.js
├── app/                        # FastAPI Backend
│   ├── core/
│   │   ├── config.py          # Configuration
│   │   └── opencode_client.py # OpenCode API client
│   └── main.py                # FastAPI application
├── cli_tester.py              # CLI tool
├── check_env.py               # Environment checker
├── start-dev.ps1              # Windows startup script
├── start-dev.sh               # Linux/Mac startup script
├── requirements.txt           # Python dependencies
├── QUICKSTART.md              # Quick start guide
├── README_UI.md               # Detailed UI documentation
└── README.md                  # This file
```

## Documentation

- **[Quick Start Guide](QUICKSTART.md)** - Get started quickly
- **[UI Documentation](README_UI.md)** - Detailed UI documentation
- **[API Docs](http://localhost:8000/docs)** - Interactive API documentation (when running)

## Technology Stack

**Frontend:**
- Vue 3 (Composition API)
- Vite
- Tailwind CSS
- Pinia (State Management)
- Vue Router
- Axios

**Backend:**
- FastAPI
- Uvicorn
- OpenCode AI SDK
- Pydantic

## Development

### Frontend Development
```bash
cd ui
npm run dev      # Start dev server
npm run build    # Build for production
npm run preview  # Preview production build
```

### Backend Development
```bash
python -m uvicorn app.main:app --reload
```

### Running Tests
```bash
python chat_test_case.py
```

## License

MIT License