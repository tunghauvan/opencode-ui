#!/usr/bin/env python3
"""
Session management utilities
"""
import requests
import json

API_BASE_URL = 'http://localhost:8000'
USER_ID = '188960770'

def list_sessions():
    """List all sessions with status"""
    print('📋 Listing all sessions...')
    response = requests.get(
        f'{API_BASE_URL}/api/backend/sessions',
        cookies={'user_id': USER_ID},
        timeout=10
    )

    if response.status_code == 200:
        data = response.json()
        sessions = data.get('sessions', [])
        print(f'Found {len(sessions)} sessions:')

        for session in sessions:
            status = '🟢' if session['is_active'] else '🔴'
            container = '🐳' if session.get('container_id') else '❌'
            print(f'{status} {container} {session["session_id"]} - {session["name"]}')
            if session.get('container_status'):
                print(f'    Container: {session["container_status"]}')
    else:
        print(f'Error: {response.text}')

def get_session_details(session_id):
    """Get detailed session info"""
    print(f'📋 Getting details for session {session_id}...')
    response = requests.get(
        f'{API_BASE_URL}/api/backend/sessions/{session_id}',
        cookies={'user_id': USER_ID},
        timeout=10
    )

    if response.status_code == 200:
        session = response.json()
        print(f'Session: {session["session_id"]}')
        print(f'Name: {session["name"]}')
        print(f'Status: {session["status"]}')
        print(f'Active: {session["is_active"]}')
        print(f'Container ID: {session.get("container_id", "None")}')
        print(f'Container Status: {session.get("container_status", "None")}')
        print(f'Created: {session["created_at"]}')
    else:
        print(f'Error: {response.text}')

def stop_container(session_id):
    """Stop session container"""
    print(f'🛑 Stopping container for session {session_id}...')
    response = requests.post(
        f'{API_BASE_URL}/api/backend/sessions/{session_id}/container/stop',
        cookies={'user_id': USER_ID},
        timeout=30
    )

    if response.status_code == 200:
        print('✅ Container stopped successfully')
    else:
        print(f'Error: {response.text}')

def start_container(session_id, image='python:3.9-slim', is_agent=False):
    """Start session container"""
    print(f'🚀 Starting container for session {session_id}...')
    payload = {
        'image': image,
        'is_agent': is_agent
    }
    
    response = requests.post(
        f'{API_BASE_URL}/api/backend/sessions/{session_id}/container/start',
        json=payload,
        cookies={'user_id': USER_ID},
        timeout=60
    )

    if response.status_code == 200:
        container_data = response.json()
        container_id = container_data['container_id']
        print(f'✅ Container started: {container_id[:12]}...')
        print(f'   Status: {container_data["status"]}')
        if is_agent:
            print(f'   Mode: Agent container (opencode serve)')
        else:
            print(f'   Mode: Regular session container')
        return container_id
    else:
        print(f'Error: {response.text}')
        return None

def get_container_status(session_id):
    """Get container status"""
    print(f'📊 Getting container status for session {session_id}...')
    response = requests.get(
        f'{API_BASE_URL}/api/backend/sessions/{session_id}/container/status',
        cookies={'user_id': USER_ID},
        timeout=10
    )

    if response.status_code == 200:
        status_data = response.json()
        print(f'✅ Container status:')
        print(f'   Container ID: {status_data.get("container_id", "N/A")[:12]}...')
        print(f'   Status: {status_data.get("container_status", "unknown")}')
        print(f'   Running: {status_data.get("container_running", False)}')
        return status_data
    else:
        print(f'Error: {response.text}')
        return None

def create_session(name=None, agent_id=None):
    """Create a new session"""
    import uuid
    
    # Generate session_id
    session_id = str(uuid.uuid4())[:8]
    
    if not name:
        name = f'Session {len(list_sessions_silent()) + 1}'
    
    print(f'➕ Creating new session: {name}...')
    
    payload = {
        'session_id': session_id,
        'name': name
    }
    if agent_id:
        payload['agent_id'] = agent_id
    
    response = requests.post(
        f'{API_BASE_URL}/api/backend/sessions',
        json=payload,
        cookies={'user_id': USER_ID},
        timeout=30
    )

    if response.status_code == 200:
        session = response.json()
        print(f'✅ Session created: {session["session_id"]}')
        print(f'   Name: {session["name"]}')
        print(f'   Status: {session["status"]}')
        return session['session_id']
    else:
        print(f'Error: {response.text}')
        return None

def list_sessions_silent():
    """List sessions without printing (for internal use)"""
    try:
        response = requests.get(
            f'{API_BASE_URL}/api/backend/sessions',
            cookies={'user_id': USER_ID},
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            return data.get('sessions', [])
    except:
        pass
    return []

def delete_session(session_id):
    """Delete session and cleanup"""
    print(f'🗑️  Deleting session {session_id}...')

    # First stop container if running
    stop_response = requests.post(
        f'{API_BASE_URL}/api/backend/sessions/{session_id}/container/stop',
        cookies={'user_id': USER_ID},
        timeout=30
    )

    if stop_response.status_code == 200:
        print('   Container stopped')
    else:
        print(f'   Warning: Could not stop container: {stop_response.text}')

    # Then delete session
    delete_response = requests.delete(
        f'{API_BASE_URL}/api/backend/sessions/{session_id}',
        cookies={'user_id': USER_ID},
        timeout=10
    )

    if delete_response.status_code == 200:
        print('✅ Session deleted successfully')
    else:
        print(f'Error: {delete_response.text}')

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python session_utils.py list")
        print("  python session_utils.py create [name] [agent_id]")
        print("  python session_utils.py details <session_id>")
        print("  python session_utils.py start <session_id> [image] [--agent]")
        print("  python session_utils.py status <session_id>")
        print("  python session_utils.py stop <session_id>")
        print("  python session_utils.py delete <session_id>")
        sys.exit(1)

    command = sys.argv[1]

    if command == "list":
        list_sessions()
    elif command == "create":
        name = sys.argv[2] if len(sys.argv) > 2 else None
        agent_id = sys.argv[3] if len(sys.argv) > 3 else None
        create_session(name, agent_id)
    elif command == "details" and len(sys.argv) > 2:
        get_session_details(sys.argv[2])
    elif command == "start" and len(sys.argv) > 2:
        image = 'python:3.9-slim'
        is_agent = False
        
        # Parse arguments
        args = sys.argv[2:]
        session_id = args[0]
        
        for arg in args[1:]:
            if arg.startswith('--agent') or arg == '--is-agent':
                is_agent = True
            elif not arg.startswith('--'):
                image = arg
        
        start_container(session_id, image, is_agent)
    elif command == "status" and len(sys.argv) > 2:
        get_container_status(sys.argv[2])
    elif command == "stop" and len(sys.argv) > 2:
        stop_container(sys.argv[2])
    elif command == "delete" and len(sys.argv) > 2:
        delete_session(sys.argv[2])
    else:
        print("Invalid command or missing arguments")
        sys.exit(1)