"""
Docker operations for OpenCode Agent Controller
"""

import json
import docker
from typing import Optional, Dict, Any

# Docker client
docker_client = docker.from_env()

# Configuration
VOLUME_NAME = "opencode-sessions"

def ensure_volume_exists() -> None:
    """Ensure the sessions volume exists"""
    try:
        volumes = docker_client.volumes.list()
        if not any(v.name == VOLUME_NAME for v in volumes):
            docker_client.volumes.create(name=VOLUME_NAME)
            print(f"Created volume: {VOLUME_NAME}")
    except Exception as e:
        print(f"Error ensuring volume exists: {e}")

def create_session_folder(session_id: str, github_token: str = None) -> Dict[str, Any]:
    """Create session folder and auth.json in volume"""
    try:
        folder_path = f"/root/.local/share/opencode/{session_id}"

        # Create auth data
        auth_data = {
            "github-copilot": {
                "type": "oauth",
                "refresh": github_token or session_id
            }
        }

        # Create temp container to write auth.json
        temp_container = docker_client.containers.run(
            'alpine',
            command=['sh', '-c', f'mkdir -p {folder_path} && cat > {folder_path}/auth.json << EOF\n{json.dumps(auth_data, indent=2)}\nEOF'],
            volumes={VOLUME_NAME: {'bind': '/root/.local/share/opencode', 'mode': 'rw'}},
            detach=True,
            remove=True
        )

        return auth_data
    except Exception as e:
        raise Exception(f"Failed to create session folder: {str(e)}")

def get_session_auth_data(session_id: str) -> Optional[Dict[str, Any]]:
    """Get auth data from session folder"""
    try:
        # Run temp container to read auth.json
        temp_container = docker_client.containers.run(
            'alpine',
            command=['sh', '-c', f'cat /root/.local/share/opencode/{session_id}/auth.json 2>/dev/null || echo "null"'],
            volumes={VOLUME_NAME: {'bind': '/root/.local/share/opencode', 'mode': 'ro'}},
            detach=False,
            remove=True,
            stdout=True
        )

        output = temp_container.decode('utf-8').strip()
        if output and output != "null":
            return json.loads(output)
        return None
    except Exception as e:
        print(f"Error reading auth data: {e}")
        return None

def update_session_auth_data(session_id: str, auth_data: Dict[str, Any]) -> None:
    """Update auth.json in session folder"""
    try:
        folder_path = f"/root/.local/share/opencode/{session_id}"

        # Update auth.json in volume
        temp_container = docker_client.containers.run(
            'alpine',
            command=['sh', '-c', f'cat > {folder_path}/auth.json << EOF\n{json.dumps(auth_data, indent=2)}\nEOF'],
            volumes={VOLUME_NAME: {'bind': '/root/.local/share/opencode', 'mode': 'rw'}},
            detach=True,
            remove=True
        )
    except Exception as e:
        raise Exception(f"Failed to update auth data: {str(e)}")

def remove_session_folder(session_id: str) -> None:
    """Remove session folder from volume"""
    try:
        docker_client.containers.run(
            'alpine',
            command=['sh', '-c', f'rm -rf /root/.local/share/opencode/{session_id}'],
            volumes={VOLUME_NAME: {'bind': '/root/.local/share/opencode', 'mode': 'rw'}},
            detach=True,
            remove=True
        )
    except Exception as e:
        print(f"Error removing session folder: {e}")

def cleanup_container(container_id: str) -> None:
    """Cleanup container in background"""
    try:
        container = docker_client.containers.get(container_id)
        container.stop(timeout=10)
        container.remove()
        print(f"Cleaned up container: {container_id}")
    except Exception as e:
        print(f"Error cleaning up container {container_id}: {e}")

def run_session_container(session_id: str, image: str, environment: Dict[str, str], agent_token: Optional[str] = None, is_agent: bool = False) -> str:
    """Run container for session
    
    Args:
        session_id: Unique session identifier
        image: Docker image to run
        environment: Environment variables for the container
        agent_token: GitHub OAuth token for agent authentication
        is_agent: If True, runs 'opencode serve' for agent containers
    
    Returns:
        Container ID
    """
    if is_agent:
        # Agent container: run opencode serve
        entrypoint_script = f'''
mkdir -p /root/.local/share/opencode
if [ -f /mnt/volume/{session_id}/auth.json ]; then
    cp /mnt/volume/{session_id}/auth.json /root/.local/share/opencode/auth.json
fi
echo "Starting OpenCode agent server for session {session_id}"
opencode serve --port 4096 --hostname 0.0.0.0 --print-logs
'''
        container_name = f"agent_{session_id}"
        
        # Default environment for agent
        env_vars = {
            "SESSION_ID": session_id,
        }
        
        # Add agent token if provided
        if agent_token:
            env_vars["GITHUB_TOKEN"] = agent_token
            
    else:
        # Regular session container
        entrypoint_script = f'''
mkdir -p /root/.local/share/opencode
if [ -f /mnt/volume/{session_id}/auth.json ]; then
    cp /mnt/volume/{session_id}/auth.json /root/.local/share/opencode/auth.json
fi
echo "Session {session_id} container started"
sleep infinity
'''
        container_name = f"opencode-session-{session_id}"
        
        # Default environment
        env_vars = {
            "SESSION_ID": session_id,
            "DB_PASSWORD": "my-super-secret-password-12345",
            "API_KEY": "sk-1234567890abcdef",
            "SECRET_TOKEN": "token-xyz-987654321"
        }

    # Merge with request environment
    if environment:
        env_vars.update(environment)

    # Run container
    container = docker_client.containers.run(
        image,
        detach=True,
        name=container_name,
        environment=env_vars,
        volumes={VOLUME_NAME: {'bind': '/mnt/volume', 'mode': 'rw'}},
        network="opencode-ui_opencode-network" if is_agent else None,  # Join network for agent containers
        ports={'4096/tcp': None} if is_agent else None,  # Expose port 4096 for agent containers
        command=['sh', '-c', entrypoint_script]
    )

    return container.id

def get_container_logs(container_id: str, tail: int = 100) -> str:
    """Get logs from container"""
    try:
        container = docker_client.containers.get(container_id)
        logs = container.logs(tail=tail).decode('utf-8')
        return logs
    except Exception as e:
        raise Exception(f"Failed to get logs: {str(e)}")