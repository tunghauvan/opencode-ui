# OpenCode UI Quick Start Guide

## 🚀 Quick Setup

### Prerequisites
- Docker and Docker Compose
- GitHub OAuth App (for authentication)
- OpenCode agent image

### 1. Clone and Setup
```bash
git clone <repository-url>
cd opencode-ui

# Copy environment template
cp .env.example .env
```

### 2. Configure Environment
Edit `.env` with your settings:
```env
# GitHub OAuth
GITHUB_CLIENT_ID=your-github-client-id
GITHUB_CLIENT_SECRET=your-github-client-secret
GITHUB_COPILOT_CLIENT_ID=your-copilot-client-id

# OpenCode
OPENCODE_BASE_URL=http://localhost:4096

# Services
AGENT_CONTROLLER_URL=http://agent-controller:8001
AGENT_SERVICE_SECRET=your-secure-service-secret

# Database
DATABASE_URL=sqlite:///./data/db.sqlite3
```

### 3. Build OpenCode Agent Image
```bash
# Build the base agent image
docker build -t opencode-agent:latest .
```

### 4. Start All Services
```bash
# Start with Docker Compose (recommended)
docker-compose up --build

# Or start individual services
docker-compose up --build backend frontend agent-controller
```

### 5. Access the Application
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Agent Controller**: http://localhost:8001

## 📖 First Time Setup

### Step 1: Login with GitHub
1. Open browser: http://localhost:3000
2. Click "Login with GitHub"
3. Complete OAuth flow
4. You should be redirected back to the app

### Step 2: Create Your First Agent
1. Click the gear icon (Settings) in the top right
2. Navigate to "Agents" section
3. Click "Create New Agent"
4. Enter agent name and description
5. Complete the device code flow:
   - Copy the user code
   - Open the verification URL in a new tab
   - Paste the code and authorize

### Step 3: Start Chatting
1. Click "New Session" in the sidebar
2. Select your preferred AI model from the dropdown
3. Type a message and press Enter or click Send
4. Watch as your personalized agent responds!

## 🏗️ Architecture Overview

### Agent-Based Architecture
**Personalized Sessions**: Each chat session runs in its own isolated Docker container with your personal agent token.

### System Components
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Main Backend  │    │ Agent Controller│
│   (Vue.js)      │◄──►│   (FastAPI)     │◄──►│   (FastAPI)     │
│   Port: 3000    │    │   Port: 8000    │    │   Port: 8001    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                        │                        │
         ▼                        ▼                        ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Database      │    │   Docker Engine │    │ Agent Container │
│   (SQLite)      │    │                 │    │ (opencode serve)│
│                 │    │                 │    │ Port: 4096      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Container Isolation
- **Agent Containers**: `agent_{session_id}` (created per session)
- **Personal Tokens**: Each container uses your agent's GitHub token
- **Network Security**: Isolated Docker networks prevent external access
- **Resource Limits**: Configurable CPU and memory per container

## 🔧 Key Features

### 🤖 Agent Management
- **Multiple Agents**: Create different agents for different purposes
- **Token Security**: GitHub tokens encrypted and isolated per user
- **Device Flow**: Secure OAuth flow for headless environments
- **Agent Stats**: View creation dates and usage statistics

### 💬 Advanced Chat
- **Real AI Responses**: Direct integration with OpenCode AI service
- **Model Selection**: Choose from available AI models (grok-code, big-pickle, etc.)
- **Persistent History**: All conversations automatically saved
- **Session Switching**: Easily switch between multiple conversations
- **Markdown Support**: Rich text formatting in messages

### 🔧 Dynamic Model Management
- **Provider Discovery**: Automatically detects available AI providers
- **Real-Time Updates**: Model availability updated from containers
- **Fallback Support**: Graceful degradation when models unavailable
- **Model Switching**: Change models mid-conversation

## 🧪 Testing & Verification

### Integration Test
Run the comprehensive integration test:
```bash
python scripts/test_integration.py
```

This will test:
- Session creation with agent containers
- Chat message sending and receiving
- Real AI responses from OpenCode
- Container lifecycle management

### CLI Testing Tools
```bash
# Test connection to OpenCode
python cli_tester.py --test-connection

# List all sessions
python cli_tester.py --list-sessions

# Send test message
python cli_tester.py --chat <session_id> "Hello, world!"
```

### Manual Testing Checklist
- [ ] User registration and login
- [ ] Agent creation with device code flow
- [ ] Session creation and container startup
- [ ] Chat message sending and receiving real AI responses
- [ ] Model selection and provider switching
- [ ] Session switching and history restoration
- [ ] Container cleanup on session deletion

## 📊 Monitoring & Troubleshooting

### Health Checks
- **Application Health**: `GET /health`
- **Container Status**: Check Docker container logs
- **Database Health**: Verify SQLite file accessibility

### Common Issues

#### "No agent configured" Error
**Solution**: Create an agent in Settings → Agents before creating sessions

#### Container Not Starting
**Symptoms**: Session creation fails, container not found
**Debug**:
```bash
# Check agent controller logs
docker-compose logs agent-controller

# Verify Docker socket mounting
docker-compose exec agent-controller docker ps
```

#### Chat Messages Not Working
**Symptoms**: Messages sent but no response
**Debug**:
```bash
# Check backend logs
docker-compose logs backend

# Check agent container logs
docker logs agent_{session_id}

# Verify network connectivity
docker exec backend ping agent_{session_id}
```

#### Authentication Issues
**Symptoms**: Login fails or agent creation fails
**Debug**:
```bash
# Check GitHub OAuth configuration
# Verify client IDs and secrets in .env
# Check GitHub app permissions
```

### Debugging Commands

#### View Service Logs
```bash
# All services
docker-compose logs

# Specific service
docker-compose logs -f backend
docker-compose logs -f agent-controller

# Agent container logs
docker logs agent_{session_id}
```

#### Inspect Database
```bash
python scripts/check_db.py
```

#### Check Network Connectivity
```bash
# Get container names
docker ps

# Test DNS resolution
docker exec backend ping -c 1 agent_{session_id}
```

#### Verify Container Creation
```bash
# List agent containers
docker ps | grep agent_

# Check container status
docker inspect agent_{session_id}
```

## 🧹 Cleanup

### Stop All Services
```bash
docker-compose down
```

### Remove All Containers and Volumes
```bash
docker-compose down --volumes --remove-orphans
```

### Remove Agent Containers
```bash
docker ps -a | grep agent_ | awk '{print $1}' | xargs docker rm -f
```

## ⚡ Performance Notes

- **Container Startup**: ~2-5 seconds for new sessions
- **Memory Usage**: ~200-500MB per agent container
- **Concurrent Sessions**: Limited by host resources
- **Message Response**: <2 seconds for subsequent messages
- **Database**: SQLite suitable for development

## 🔄 Data Flow

1. **User Authentication**: GitHub OAuth → User created in database
2. **Agent Creation**: Device code flow → Agent token stored securely
3. **Session Creation**: Agent check → Container created → Session stored
4. **Chat Message**: Frontend → Backend → Agent container → AI response
5. **Model Discovery**: Backend queries agent containers → Returns available models

## 📚 Next Steps

1. ✅ Complete the quick start setup
2. ✅ Test the complete chat flow
3. ✅ Verify container isolation
4. 🔄 Explore advanced features (model selection, multiple agents)
5. 🔄 Check out the full documentation in `docs/`
6. 🔄 Run additional tests and monitoring

## 📞 Support

For support and questions:
- **Issues**: [GitHub Issues](https://github.com/your-repo/issues)
- **Documentation**: Check the `docs/` directory for detailed guides
- **Logs**: Use the debugging commands above to gather information
- **API Docs**: Visit http://localhost:8000/docs when running

---

**Happy chatting with your personalized OpenCode agents! 🤖✨**
