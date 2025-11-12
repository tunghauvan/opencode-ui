# Quick Start Guide - Agent Session Feature

## Architecture Overview

**Agent-Only Architecture**: All sessions now require personalized agent containers. No shared service fallback.

### Agent Containers (`agent_{session_id}`)
- **Purpose**: Personalized agent sessions
- **Container**: Created per session (e.g., `agent_abc123`)
- **Port**: 4096 (internal Docker network only)
- **Usage**: All sessions use agent-based containers with custom tokens
- **Isolation**: Each container has its own agent token

## Build and Start

### 1. Build the OpenCode Agent Image
```powershell
docker build -t opencode-agent:latest .
```

### 2. Start All Services
```powershell
docker-compose up --build
```

This will start:
- **Backend** (port 8000): Main API server
- **Frontend** (port 3000): Vue.js UI
- **Agent Controller** (port 8001): Container management service

**Note**: No shared OpenCode service - all sessions require agents!

### 3. Verify Services are Running
```powershell
docker ps
```

You should see 3 containers running (backend, frontend, agent-controller).

## Testing the Feature

### Step 1: Login
1. Open browser: http://localhost:3000
2. Click "Login with GitHub"
3. Complete OAuth flow
4. You should be redirected back to the app

### Step 2: Create an Agent
1. Click on your profile/settings
2. Navigate to "Agents" section
3. Click "Create Agent"
4. Enter agent name and description
5. Complete the device code flow:
   - Copy the user code
   - Open the verification URL
   - Paste the code
   - Authorize the agent

### Step 3: Create a Session
1. Click "New Session" button
2. The system will:
   - Check if you have an agent (you do!)
   - Call agent-controller to create agent container
   - Start container with `opencode serve`
   - Save session with agent_id and base_url

Watch the Docker logs to see the container being created:
```powershell
docker-compose logs -f agent-controller
```

### Step 4: Send a Chat Message
1. In the new session, type a message
2. Click Send
3. The system will:
   - Look up the session in database
   - Find the base_url (http://agent_{session_id}:4096)
   - Send the message to your personal agent container
   - Display the response

### Step 5: Verify Container Isolation
1. Create another session
2. Check running containers:
```powershell
docker ps | grep agent_
```

You should see **agent containers only**:
- `agent_{session_id_1}` (your first agent session)
- `agent_{session_id_2}` (your second agent session)

Each agent session gets its own isolated container with the agent's personal token.
```powershell
python check_db.py
```

You should see sessions table with:
- `agent_id` field populated
- `base_url` field with container URL
- `container_id` field with Docker container ID

## Troubleshooting

### Issue: "No agent configured" error
**Solution**: Create an agent first in Settings

### Issue: Container not starting
**Solution**: Check agent-controller logs:
```powershell
docker-compose logs agent-controller
```

**Verify Docker socket is mounted:**
```yaml
volumes:
  - /var/run/docker.sock:/var/run/docker.sock
```

### Issue: Cannot connect to agent container
**Solution**: Verify network configuration:
```powershell
docker network inspect opencode-network
```

All services should be on the same network.

### Issue: Agent container exits immediately
**Solution**: Check container logs:
```powershell
docker logs agent_{session_id}
```

Verify `opencode` CLI is installed in the image.

## Debugging Commands

### View Backend Logs
```powershell
docker-compose logs -f backend
```

### View Agent Container Logs
```powershell
docker logs -f agent_{session_id}
```

### Inspect Database
```powershell
python check_db.py
```

### Test Agent Controller Directly
```powershell
# Create session (replace with your values)
curl -X POST http://localhost:8001/sessions/agent `
  -H "X-Service-Secret: default-secret-change-in-production" `
  -H "Content-Type: application/json" `
  -d '{\"session_id\": \"test123\", \"agent_id\": 1, \"agent_token\": \"your_token\"}'
```

### Check Network Connectivity
```powershell
# Get backend container name
docker ps | grep backend

# Test DNS resolution
docker exec <backend_container> ping -c 1 agent_test123
```

## Clean Up

### Stop All Services
```powershell
docker-compose down
```

### Remove All Containers
```powershell
docker-compose down --volumes --remove-orphans
```

### Remove Agent Containers
```powershell
docker ps -a | grep agent_ | awk '{print $1}' | ForEach-Object { docker rm -f $_ }
```

## Expected Behavior

### Successful Agent Session Creation
```json
{
  "session_id": "abc123",
  "agent_id": 1,
  "container_id": "docker_container_id",
  "container_status": "running",
  "base_url": "http://agent_abc123:4096",
  "created_at": "2025-11-12T10:30:00Z"
}
```

### Container Architecture
- **Agent Containers**: `agent_{session_id}` (created per session, port 4096 internal)
- **Network**: All services on `opencode-network` for DNS resolution

### Chat Routing
- **All Sessions**: Route to `http://agent_{session_id}:4096` (agent required)

## Performance Notes

- **First session creation**: 5-10 seconds (container startup)
- **Subsequent messages**: <2 seconds
- **Container resources**: ~200-500MB RAM per container
- **Container startup**: 2-5 seconds

## Next Steps

1. ✅ Test the complete flow
2. ✅ Verify container isolation
3. ⚠️ Implement container cleanup on session deletion
4. ⚠️ Add health checks for agent containers
5. ⚠️ Implement error recovery for failed containers
6. ⚠️ Add monitoring and metrics
7. ⚠️ Optimize container startup time (pooling)

## Support

If you encounter issues:
1. Check all service logs: `docker-compose logs`
2. Verify database state: `python check_db.py`
3. Check network: `docker network inspect opencode-network`
4. Review implementation summary: `AGENT_SESSION_IMPLEMENTATION_SUMMARY.md`
