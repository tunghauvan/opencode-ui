# OpenCode UI

A modern, containerized web interface for OpenCode AI agents with personalized session management, real-time chat, and GitHub OAuth integration.

![OpenCode UI](https://img.shields.io/badge/OpenCode-UI-blue)
![Vue 3](https://img.shields.io/badge/Vue-3-green)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-red)
![Docker](https://img.shields.io/badge/Docker-Ready-blue)

## 🌟 Key Features

### 🤖 Agent-Based Architecture
- **Personalized Sessions**: Each user session runs in its own isolated Docker container
- **Agent Management**: Create and manage multiple AI agents with GitHub OAuth
- **Container Isolation**: Complete separation between user sessions for security and performance
- **Dynamic Scaling**: Containers created on-demand and cleaned up automatically

### 💬 Real-Time Chat Interface
- **Modern UI**: Clean, responsive design built with Vue 3 and Tailwind CSS
- **Persistent History**: Chat conversations automatically saved and restored
- **Markdown Support**: Rich text formatting in chat messages
- **Streaming Support**: Real-time message streaming (when available)

### 🔧 Advanced Model Management
- **Dynamic Provider Discovery**: Automatically fetches available AI models from OpenCode
- **Model Selection**: Choose from multiple providers (OpenCode, etc.) and models
- **Real-time Updates**: Model availability updated from running agent containers
- **Fallback Support**: Graceful degradation when models are unavailable

### 🔐 Enterprise-Ready Authentication
- **GitHub OAuth**: Secure authentication for both users and agents
- **Device Code Flow**: Support for headless environments and CI/CD
- **Token Management**: Automatic token refresh and secure storage
- **Role-Based Access**: User and agent separation with proper permissions

### 🐳 Container Management
- **Docker Integration**: Seamless container lifecycle management
- **Network Isolation**: Secure inter-service communication via Docker networks
- **Resource Limits**: Configurable CPU and memory limits per container
- **Health Monitoring**: Automatic container health checks and restart logic

## 🚀 Quick Start

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

## 📖 User Guide

### First Time Setup

1. **Login with GitHub**
   - Visit http://localhost:3000
   - Click "Login with GitHub"
   - Authorize the application

2. **Create Your First Agent**
   - Go to Settings → Agents
   - Click "Create New Agent"
   - Enter agent name and description
   - Complete GitHub device code authentication

3. **Start Chatting**
   - Click "New Session" in the sidebar
   - Select your preferred AI model
   - Start typing messages!

### Managing Agents

- **Create Agent**: Settings → Agents → "Create New Agent"
- **View Agents**: See all your agents with creation dates and usage stats
- **Delete Agent**: Remove agents you no longer need

### Session Management

- **Create Session**: Click "New Session" button
- **Switch Sessions**: Click on any session in the sidebar
- **Delete Session**: Right-click session → Delete
- **Session History**: All messages automatically saved and restored

### Model Selection

- **Access Settings**: Click gear icon → Preferences → AI Model
- **Choose Provider**: Select from available AI providers
- **Select Model**: Pick your preferred model for conversations
- **Auto-Detection**: Models automatically discovered from your agent containers

## 🏗️ Architecture

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

### Data Flow

1. **User Authentication**: GitHub OAuth → User created in database
2. **Agent Creation**: Device code flow → Agent token stored securely
3. **Session Creation**: Agent check → Container created → Session stored
4. **Chat Message**: Frontend → Backend → Agent container → AI response
5. **Model Discovery**: Backend queries agent containers → Returns available models

### Security Model

- **Authentication**: GitHub OAuth with secure cookie storage
- **Authorization**: User-scoped access to agents and sessions
- **Container Isolation**: Each session runs in separate container
- **Token Security**: Agent tokens encrypted and isolated per user
- **Network Security**: Internal Docker networks prevent external access

## 🔧 API Reference

### Authentication Endpoints
- `GET /auth/login` - Get GitHub OAuth URL
- `GET /auth/device` - Get device code for agent creation
- `POST /auth/device/poll` - Poll for device code completion
- `GET /auth/me` - Get current user info
- `POST /auth/refresh-token` - Refresh access tokens

### Session Management
- `GET /api/sessions` - List user sessions
- `POST /api/sessions` - Create new session
- `GET /api/sessions/{id}` - Get session details
- `DELETE /api/sessions/{id}` - Delete session
- `POST /api/sessions/{id}/chat` - Send chat message

### Agent Management
- `GET /api/agents` - List user agents
- `POST /api/agents` - Create new agent
- `DELETE /api/agents/{id}` - Delete agent

### Model Management
- `GET /api/models` - Get available AI models and providers

### Backend API (Container Management)
- `GET /api/backend/sessions` - List sessions with container info
- `POST /api/backend/sessions/{id}/container/start` - Start container
- `POST /api/backend/sessions/{id}/container/stop` - Stop container
- `GET /api/backend/sessions/{id}/container/status` - Get container status
- `GET /api/backend/sessions/{id}/container/logs` - Get container logs

## 🧪 Testing

### Integration Tests
```bash
# Run comprehensive integration tests
python scripts/test_integration.py

# Test specific components
python scripts/test_backend_chat.py
python scripts/test_session_api.py
python scripts/test_opencode_api.py
```

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
- [ ] Chat message sending and receiving
- [ ] Model selection and provider switching
- [ ] Session switching and history restoration
- [ ] Container cleanup on session deletion

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | SQLite database path | `sqlite:///./data/db.sqlite3` |
| `GITHUB_CLIENT_ID` | GitHub OAuth client ID | Required |
| `GITHUB_CLIENT_SECRET` | GitHub OAuth client secret | Required |
| `GITHUB_COPILOT_CLIENT_ID` | GitHub Copilot client ID | Required |
| `AGENT_CONTROLLER_URL` | Agent controller service URL | `http://agent-controller:8001` |
| `AGENT_SERVICE_SECRET` | Service-to-service authentication | Required |
| `OPENCODE_BASE_URL` | OpenCode API base URL | `http://localhost:4096` |

### Docker Configuration

```yaml
# docker-compose.yml
version: '3.8'
services:
  backend:
    build:
      context: .
      dockerfile: docker/Dockerfile.backend
    environment:
      - DATABASE_URL=sqlite:///./data/db.sqlite3
    volumes:
      - ./data:/app/data
    networks:
      - opencode-network

  frontend:
    build:
      context: .
      dockerfile: docker/Dockerfile.frontend
    ports:
      - "3000:3000"
    networks:
      - opencode-network

  agent-controller:
    build:
      context: .
      dockerfile: docker/Dockerfile.backend
    command: python -m app.agent-controller
    environment:
      - AGENT_SERVICE_SECRET=your-secret
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
    networks:
      - opencode-network

networks:
  opencode-network:
    driver: bridge
```

## 📊 Monitoring & Troubleshooting

### Health Checks
- **Application Health**: `GET /health`
- **Container Status**: Check Docker container logs
- **Database Health**: Verify SQLite file accessibility

### Common Issues

#### "No agent configured" Error
**Solution**: Create an agent in Settings before creating sessions

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

### Performance Optimization

- **Container Startup**: ~2-5 seconds for new sessions
- **Memory Usage**: ~200-500MB per agent container
- **Concurrent Sessions**: Limited by host resources
- **Database**: SQLite suitable for development, consider PostgreSQL for production

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make your changes and add tests
4. Run tests: `python scripts/test_integration.py`
5. Commit your changes: `git commit -am 'Add your feature'`
6. Push to the branch: `git push origin feature/your-feature`
7. Submit a pull request

### Development Setup

```bash
# Install dependencies
pip install -r requirements.txt
cd ui && npm install

# Run in development mode
docker-compose -f docker-compose.dev.yml up

# Run tests
python scripts/test_integration.py
```

## 📚 Documentation

- **[Quick Start Guide](docs/QUICK_START.md)** - Step-by-step setup instructions
- **[Agent Session Implementation](docs/AGENT_SESSION_IMPLEMENTATION_SUMMARY.md)** - Technical implementation details
- **[API Documentation](http://localhost:8000/docs)** - Interactive API docs (when running)
- **[Project Structure](docs/project_structure.txt)** - File organization overview

## 🛡️ Security

### Authentication & Authorization
- GitHub OAuth 2.0 for user authentication
- Device code flow for agent creation
- Secure cookie-based sessions
- Service-to-service authentication with secrets

### Container Security
- Non-root container execution
- Minimal base images
- Network isolation via Docker networks
- Resource limits and constraints

### Data Protection
- Agent tokens encrypted at rest
- No sensitive data in logs
- Secure API communication
- Input validation and sanitization

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [OpenCode](https://opencode.ai) - AI platform powering the agents
- [Vue.js](https://vuejs.org/) - Progressive JavaScript framework
- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [Docker](https://www.docker.com/) - Containerization platform

## 📞 Support

For support and questions:
- **Issues**: [GitHub Issues](https://github.com/your-repo/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-repo/discussions)
- **Documentation**: Check the `docs/` directory for detailed guides

---

**Built with ❤️ for the OpenCode community**