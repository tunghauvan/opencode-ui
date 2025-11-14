#!/usr/bin/env python3
"""
Comprehensive test for session and container integration
"""
import requests
import json
import uuid
import time

API_BASE_URL = 'http://localhost:8000'
USER_ID = '188960770'

def test_persistence_workflow():
    """Test session persistence across container restarts"""
    
    print("=" * 60)
    print("Testing Session Persistence Across Container Restarts")
    print("=" * 60)
    
    # Step 1: Create new session
    print("\n1. Creating new session...")
    session_id = f"ses{str(uuid.uuid4())[:5]}"
    
    create_response = requests.post(
        f'{API_BASE_URL}/api/backend/sessions',
        json={
            'session_id': session_id,
            'name': f'Persistence Test Session {session_id}',
            'description': 'Testing data persistence'
        },
        cookies={'user_id': USER_ID},
        timeout=30
    )
    
    if create_response.status_code == 200:
        session_data = create_response.json()
        print(f"✅ Session created: {session_data['session_id']}")
        print(f"   Name: {session_data['name']}")
    else:
        print(f"❌ Failed to create session: {create_response.text}")
        return False
    
    # Give background thread time to create in agent controller
    print("   Waiting for agent controller sync...")
    time.sleep(2)
    
    # Step 2: Start container
    print(f"\n2. Starting container for session {session_id}...")
    start_response = requests.post(
        f'{API_BASE_URL}/api/backend/sessions/{session_id}/container/start',
        json={'image': 'opencode-ui-opencode-agent:latest', 'is_agent': True},
        cookies={'user_id': USER_ID},
        timeout=60
    )
    
    if start_response.status_code == 200:
        container_data = start_response.json()
        container_id = container_data['container_id']
        print(f"✅ Container started: {container_id[:12]}...")
        print(f"   Status: {container_data['status']}")
    else:
        print(f"❌ Failed to start container: {start_response.text}")
        return False
    
    # Wait for agent container to be ready
    print("   Waiting for agent container to be ready...")
    time.sleep(10)
    
    # Step 3: Send first message and get AI response
    print(f"\n3. Sending FIRST test message to session...")
    message_response = requests.post(
        f'{API_BASE_URL}/api/backend/sessions/{session_id}/chat',
        json={'prompt': 'Hello, remember that I am testing persistence. What is 5+7?'},
        cookies={'user_id': USER_ID},
        timeout=30
    )
    
    if message_response.status_code == 200:
        message_data = message_response.json()
        print(f"✅ First message sent successfully")
        print(f"   Prompt: {message_data.get('prompt', 'N/A')}")
        if message_data.get('content'):
            print(f"   AI Response: {message_data['content'][:200]}...")
        print(f"   Container Status: {message_data.get('container_status', 'N/A')}")
    else:
        print(f"❌ Failed to send first message: {message_response.text}")
        return False

    # Step 4: Stop container (but keep session)
    print(f"\n4. Stopping container (keeping session)...")
    stop_response = requests.post(
        f'{API_BASE_URL}/api/backend/sessions/{session_id}/container/stop',
        cookies={'user_id': USER_ID},
        timeout=30
    )
    
    if stop_response.status_code == 200:
        print(f"✅ Container stopped successfully")
    else:
        print(f"⚠️  Failed to stop container: {stop_response.text}")
    
    # Wait a bit
    print("   Waiting 3 seconds...")
    time.sleep(3)
    
    # Step 5: Restart container
    print(f"\n5. Restarting container for session {session_id}...")
    restart_response = requests.post(
        f'{API_BASE_URL}/api/backend/sessions/{session_id}/container/start',
        json={'image': 'opencode-ui-opencode-agent:latest', 'is_agent': True},
        cookies={'user_id': USER_ID},
        timeout=60
    )
    
    if restart_response.status_code == 200:
        new_container_data = restart_response.json()
        new_container_id = new_container_data['container_id']
        print(f"✅ Container restarted: {new_container_id[:12]}...")
        print(f"   Status: {new_container_data['status']}")
        if new_container_id != container_id:
            print(f"   Note: New container ID (old: {container_id[:12]}...)")
    else:
        print(f"❌ Failed to restart container: {restart_response.text}")
        return False
    
    # Wait for agent container to be ready again
    print("   Waiting for restarted container to be ready...")
    time.sleep(10)
    
    # Step 6: Send second message to test persistence
    print(f"\n6. Sending SECOND test message to check persistence...")
    message2_response = requests.post(
        f'{API_BASE_URL}/api/backend/sessions/{session_id}/chat',
        json={'prompt': 'Do you remember our previous conversation? What was the math question I asked?'},
        cookies={'user_id': USER_ID},
        timeout=30
    )
    
    if message2_response.status_code == 200:
        message2_data = message2_response.json()
        print(f"✅ Second message sent successfully")
        print(f"   Prompt: {message2_data.get('prompt', 'N/A')}")
        if message2_data.get('content'):
            print(f"   AI Response: {message2_data['content'][:300]}...")
            # Check if AI remembers the previous conversation
            content_lower = message2_data['content'].lower()
            if '5+7' in content_lower or '12' in content_lower or 'persistence' in content_lower:
                print(f"   🎉 SUCCESS: AI remembers previous conversation!")
            else:
                print(f"   ⚠️  WARNING: AI may not remember previous conversation")
        print(f"   Container Status: {message2_data.get('container_status', 'N/A')}")
    else:
        print(f"❌ Failed to send second message: {message2_response.text}")
        return False

    # Step 7: Check session details
    print(f"\n7. Checking final session details...")
    get_response = requests.get(
        f'{API_BASE_URL}/api/backend/sessions/{session_id}',
        cookies={'user_id': USER_ID},
        timeout=10
    )
    
    if get_response.status_code == 200:
        session = get_response.json()
        print(f"✅ Session details:")
        print(f"   Name: {session['name']}")
        print(f"   Status: {session['status']}")
        print(f"   Active: {session['is_active']}")
        print(f"   Container: {session['container_id'][:12] if session.get('container_id') else 'None'}...")
    else:
        print(f"❌ Failed to get session: {get_response.text}")
    
    # Step 8: Clean up - Delete session
    print(f"\n8. Cleaning up - Deleting session...")
    delete_response = requests.delete(
        f'{API_BASE_URL}/api/backend/sessions/{session_id}',
        cookies={'user_id': USER_ID},
        timeout=10
    )
    
    if delete_response.status_code == 200:
        print(f"✅ Session deleted successfully")
    else:
        print(f"⚠️  Failed to delete session: {delete_response.text}")
    
    print("\n" + "=" * 60)
    print("✅ PERSISTENCE TEST COMPLETED!")
    print("   Check the AI responses above to verify if conversation history persisted")
    print("=" * 60)
    return True

if __name__ == "__main__":
    try:
        success = test_persistence_workflow()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
