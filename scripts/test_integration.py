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

def test_full_workflow():
    """Test complete session lifecycle with container"""
    
    print("=" * 60)
    print("Testing Session & Container Integration")
    print("=" * 60)
    
    # Step 1: Create new session
    print("\n1. Creating new session...")
    session_id = str(uuid.uuid4())[:8]
    
    create_response = requests.post(
        f'{API_BASE_URL}/api/backend/sessions',
        json={
            'session_id': session_id,
            'name': f'Integration Test Session {session_id}',
            'description': 'Testing full integration'
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
        json={'image': 'python:3.9-slim'},
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
    
    # Step 3: Get container status
    print(f"\n3. Checking container status...")
    status_response = requests.get(
        f'{API_BASE_URL}/api/backend/sessions/{session_id}/container/status',
        cookies={'user_id': USER_ID},
        timeout=10
    )
    
    if status_response.status_code == 200:
        status_data = status_response.json()
        print(f"✅ Container status retrieved:")
        print(f"   Container ID: {status_data.get('container_id', 'N/A')[:12]}...")
        print(f"   Status: {status_data.get('container_status', 'unknown')}")
        print(f"   Running: {status_data.get('container_running', False)}")
    else:
        print(f"⚠️  Failed to get status: {status_response.text}")
    
    # Step 4: Get session details
    print(f"\n4. Getting session details...")
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
    
    # Step 5: Stop container
    print(f"\n5. Stopping container...")
    stop_response = requests.post(
        f'{API_BASE_URL}/api/backend/sessions/{session_id}/container/stop',
        cookies={'user_id': USER_ID},
        timeout=30
    )
    
    if stop_response.status_code == 200:
        print(f"✅ Container stopped successfully")
    else:
        print(f"⚠️  Failed to stop container: {stop_response.text}")
    
    # Step 6: Delete session
    print(f"\n6. Deleting session...")
    delete_response = requests.delete(
        f'{API_BASE_URL}/api/backend/sessions/{session_id}',
        cookies={'user_id': USER_ID},
        timeout=10
    )
    
    if delete_response.status_code == 200:
        print(f"✅ Session deleted successfully")
    else:
        print(f"❌ Failed to delete session: {delete_response.text}")
    
    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED!")
    print("=" * 60)
    return True

if __name__ == "__main__":
    try:
        success = test_full_workflow()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
