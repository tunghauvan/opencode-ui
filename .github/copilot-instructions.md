# OpenCode UI - AI Coding Guidelines

## Architecture Overview

**Full-Stack Web App**: FastAPI backend + Vue.js 3 frontend with Pinia state management. Three main services:
- **Backend** (FastAPI): REST API with GitHub OAuth, SQLAlchemy ORM, cookie-based auth
- **Frontend** (Vue.js): Composition API, Pinia stores, Vue Router with auth guards
- **OpenCode Agent**: External AI service (runs on port 4096)

## Core Patterns & Conventions

### 🔐 Authentication & Security
- **Cookie-based auth**: Use `withCredentials: true` in frontend API calls
- **User ID in cookies**: Backend validates via `request.cookies.get('user_id')`
- **GitHub OAuth flows**:
  - Main app login: Web flow with redirect
  - Agent creation: Device code flow (polling)
- **CORS**: Specific origins only (`http://localhost:3000`)

### 🗄️ Database & Models
- **SQLAlchemy ORM** with SQLite (`data/db.sqlite3`)
- **User-Agent relationship**: One user can have multiple agents
- **Foreign keys**: `Agent.user_id` references `User.id`
- **Auto-init**: Database tables created via `init_db()` in `main.py`

### 🔌 API Communication Patterns

#### Frontend API Calls (`services/api.js`)
```javascript
// Always include credentials for auth
const response = await api.get('/sessions', { withCredentials: true })

// OpenCode API responses have nested structure
if (response.parts) {
  content = response.parts.find(p => p.type === 'text')?.text
}
```

#### Backend API Responses (`main.py`)
```python
# Handle OpenCode API response format
if 'parts' in response:
    for part in response['parts']:
        if part.get('type') == 'text':
            content += part['text']
```

### 🎯 Vue.js Frontend Patterns

#### Store Structure (`stores/`)
- **Pinia stores** with Composition API
- **Reactive state** with `ref()` and `computed()`
- **Async actions** with proper error handling
- **Store-to-store communication** via direct imports

#### Component Patterns
- **Modal dialogs**: Use `<Teleport to="body">` for overlays
- **Settings modal**: Tabbed interface with reactive tab switching
- **Form handling**: `v-model` with validation, `isAuthenticating` states

### 🔧 Development Workflow

#### Local Development (Docker Compose - RECOMMENDED)
```bash
# Full stack development (preferred method)
docker-compose up --build

# Rebuild specific services
docker-compose up --build backend frontend

# Rebuild and run in background
docker-compose up --build -d

# Stop all services
docker-compose down

# Rebuild from scratch (clean build)
docker-compose down --volumes --remove-orphans
docker-compose up --build
```

#### Direct Development (Use only when Docker isn't available)
```bash
# Backend only (fallback)
python -m uvicorn app.main:app --reload --port 8000

# Frontend only (fallback)
cd ui && npm run dev
```

#### Testing OpenCode API
```bash
# CLI testing tool (works with or without Docker)
python cli_tester.py --list-sessions
python cli_tester.py --chat <session_id> "Hello"
```

### 🚨 Critical Integration Points

#### OpenCode API Client (`core/opencode_client.py`)
- **External dependency**: Connects to OpenCode service on port 4096
- **Response parsing**: Handle both dict and object responses
- **Error handling**: Graceful fallbacks when API unavailable

#### GitHub OAuth (`core/github_oauth.py`)
- **Dual client IDs**: Main app vs Copilot client
- **Device flow polling**: 5-second intervals, expiration handling
- **Token storage**: Separate tokens for users vs agents

### 📁 Key Files & Directories

- **`app/main.py`**: FastAPI app, all routes, auth middleware
- **`app/core/models.py`**: SQLAlchemy User/Agent models
- **`ui/src/stores/`**: Pinia stores (session, user, chat)
- **`ui/src/services/api.js`**: Axios config, API client functions
- **`ui/src/components/SettingsDialog.vue`**: Main settings modal
- **`docker-compose.yml`**: Multi-service development setup

### ⚠️ Common Pitfalls

- **Development environment**: Always use `docker-compose up --build` for full development setup instead of running npm/python directly
- **CORS issues**: Always include `credentials: 'include'` in fetch calls
- **OpenCode API responses**: Check both `response.parts` and direct properties
- **Database paths**: Use `data/db.sqlite3`, not scattered `app.db` files
- **Modal state**: Reset form data when closing agent creation modal
- **OAuth redirects**: Never expose tokens in URL parameters

### 🔄 Data Flow Examples

#### User Authentication
1. Frontend: `fetch('/auth/me', { credentials: 'include' })`
2. Backend: Check `request.cookies.get('user_id')`
3. Database: Query `User` table by ID

#### Agent Creation
1. Frontend: Device code request → Polling loop
2. Backend: GitHub OAuth device flow → Create `Agent` record
3. Database: Link agent to user via `user_id` foreign key

#### Chat Message
1. Frontend: `api.post('/sessions/{id}/chat', { prompt, model })`
2. Backend: Forward to OpenCode API → Parse response parts
3. Frontend: Display extracted text content

### 🛠️ Build & Deployment

- **Frontend**: Vite build (`npm run build`) → Static files
- **Backend**: Uvicorn server with auto-reload
- **Docker**: Multi-stage builds, volume mounts for data
- **Environment**: `.env` file for secrets, `VITE_` prefix for frontend

### 📝 Code Style Notes

- **Python**: Type hints, async/await, Pydantic models
- **Vue.js**: Composition API, reactive refs, TypeScript-style JSDoc
- **Error handling**: Try/catch with user-friendly messages
- **Imports**: Absolute paths from project root
- **Naming**: `snake_case` (Python), `camelCase` (JavaScript)

Remember: This app bridges a Vue.js UI with an external OpenCode AI service via FastAPI. Focus on clean API contracts and robust error handling for external service dependencies.