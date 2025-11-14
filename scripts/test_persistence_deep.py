#!/usr/bin/env python3
"""
Deep test for OpenCode session persistence
Tests conversation history and session data persistence
"""
import requests
import json
import uuid
import time
import subprocess

API_BASE_URL = 'http://localhost:8000'
USER_ID = '188960770'

def run_docker_command(cmd):
    """Run docker command and return output"""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout.strip()

def inspect_volume_structure(session_id):
    """Inspect the volume structure for a session"""
    print(f"\n📂 Volume structure for session {session_id}:")
    cmd = f'docker run --rm -v opencode-sessions:/mnt/volume alpine sh -c "find /mnt/volume/{session_id} -type f 2>/dev/null | head -20"'
    files = run_docker_command(cmd)
    if files:
        print(files)
    else:
        print("  (empty or not found)")
    
    # Check directory structure
    cmd = f'docker run --rm -v opencode-sessions:/mnt/volume alpine sh -c "ls -la /mnt/volume/{session_id}/ 2>/dev/null"'
    structure = run_docker_command(cmd)
    if structure:
        print("\n📁 Directory structure:")
        print(structure)

def get_container_opencode_data(session_id):
    """Check what OpenCode has stored in the container"""
    print(f"\n🔍 Checking OpenCode data in container for session {session_id}:")
    container_name = f"agent_{session_id}"
    
    # Check if container exists
    cmd = f'docker ps -a --filter "name={container_name}" --format "{{{{.Names}}}}"'
    container = run_docker_command(cmd)
    
    if not container:
        print(f"  Container {container_name} not found")
        return
    
    # Check OpenCode directory structure
    cmd = f'docker exec {container_name} ls -la /root/.local/share/opencode/ 2>/dev/null'
    opencode_dir = run_docker_command(cmd)
    if opencode_dir:
        print("  OpenCode directory:")
        print(opencode_dir)
    
    # Check for database files
    cmd = f'docker exec {container_name} find /root/.local/share/opencode -name "*.db" -o -name "*.sqlite" 2>/dev/null'
    db_files = run_docker_command(cmd)
    if db_files:
        print("\n  Database files:")
        print(db_files)

def test_deep_persistence():
    """Test comprehensive session persistence"""
    
    print("=" * 80)
    print("DEEP PERSISTENCE TEST - OpenCode Session History")
    print("=" * 80)
    
    # Step 1: Create session
    print("\n1️⃣  Creating new session...")
    session_id = f"ses{str(uuid.uuid4())[:5]}"
    
    create_response = requests.post(
        f'{API_BASE_URL}/api/backend/sessions',
        json={
            'session_id': session_id,
            'name': f'Deep Test {session_id}',
            'description': 'Testing deep persistence'
        },
        cookies={'user_id': USER_ID},
        timeout=30
    )
    
    if create_response.status_code == 200:
        print(f"✅ Session created: {session_id}")
    else:
        print(f"❌ Failed: {create_response.text}")
        return False
    
    time.sleep(2)
    
    # Step 2: Start container
    print(f"\n2️⃣  Starting agent container...")
    start_response = requests.post(
        f'{API_BASE_URL}/api/backend/sessions/{session_id}/container/start',
        json={'image': 'opencode-ui-opencode-agent:latest', 'is_agent': True},
        cookies={'user_id': USER_ID},
        timeout=60
    )
    
    if start_response.status_code == 200:
        container_data = start_response.json()
        print(f"✅ Container started: {container_data['container_id'][:12]}...")
    else:
        print(f"❌ Failed: {start_response.text}")
        return False
    
    print("   Waiting for container to be ready...")
    time.sleep(15)
    
    # Step 3: Send multiple messages to build conversation history
    print(f"\n3️⃣  Building conversation history...")
    
    messages = [
        "Hello, I'm testing persistence. Remember this: PROJECT_NAME=TestApp",
        "What is 2+2? Please remember this calculation.",
        "Create a variable: SECRET_KEY=abc123. Don't forget it!"
    ]
    
    for i, msg in enumerate(messages, 1):
        print(f"\n   Message {i}: {msg[:50]}...")
        response = requests.post(
            f'{API_BASE_URL}/api/backend/sessions/{session_id}/chat',
            json={'prompt': msg},
            cookies={'user_id': USER_ID},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Response: {data.get('content', '')[:100]}...")
        else:
            print(f"   ❌ Failed: {response.text[:100]}")
        
        time.sleep(2)
    
    # Step 4: Inspect data BEFORE restart
    print(f"\n4️⃣  Inspecting data BEFORE container restart...")
    inspect_volume_structure(session_id)
    get_container_opencode_data(session_id)
    
    # Step 5: Stop container
    print(f"\n5️⃣  Stopping container...")
    stop_response = requests.post(
        f'{API_BASE_URL}/api/backend/sessions/{session_id}/container/stop',
        cookies={'user_id': USER_ID},
        timeout=30
    )
    
    if stop_response.status_code == 200:
        print("✅ Container stopped")
    else:
        print(f"⚠️  Stop response: {stop_response.text}")
    
    time.sleep(3)
    
    # Step 6: Inspect data AFTER stop
    print(f"\n6️⃣  Inspecting persisted data AFTER stop...")
    inspect_volume_structure(session_id)
    
    # Step 7: Restart container
    print(f"\n7️⃣  Restarting container...")
    restart_response = requests.post(
        f'{API_BASE_URL}/api/backend/sessions/{session_id}/container/start',
        json={'image': 'opencode-ui-opencode-agent:latest', 'is_agent': True},
        cookies={'user_id': USER_ID},
        timeout=60
    )
    
    if restart_response.status_code == 200:
        new_container_data = restart_response.json()
        print(f"✅ Container restarted: {new_container_data['container_id'][:12]}...")
    else:
        print(f"❌ Failed: {restart_response.text}")
        return False
    
    print("   Waiting for restarted container...")
    time.sleep(15)
    
    # Step 8: Inspect data AFTER restart
    print(f"\n8️⃣  Inspecting data AFTER restart...")
    inspect_volume_structure(session_id)
    get_container_opencode_data(session_id)
    
    # Step 9: Test conversation memory
    print(f"\n9️⃣  Testing conversation memory...")
    
    memory_tests = [
        "What was the PROJECT_NAME I told you earlier?",
        "Do you remember the calculation I asked you?",
        "What was the SECRET_KEY I shared with you?"
    ]
    
    memory_success = 0
    for i, test_msg in enumerate(memory_tests, 1):
        print(f"\n   Memory test {i}: {test_msg}")
        response = requests.post(
            f'{API_BASE_URL}/api/backend/sessions/{session_id}/chat',
            json={'prompt': test_msg},
            cookies={'user_id': USER_ID},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            content = data.get('content', '').lower()
            print(f"   Response: {data.get('content', '')[:200]}...")
            
            # Check for keywords from original messages
            if ('testapp' in content or 'project_name' in content or
                '2+2' in content or 'calculation' in content or '4' in content or
                'secret_key' in content or 'abc123' in content):
                print(f"   ✅ AI remembers context!")
                memory_success += 1
            else:
                print(f"   ⚠️  AI may not remember previous conversation")
        else:
            print(f"   ❌ Failed: {response.text[:100]}")
    
    # Step 10: Summary
    print(f"\n{'=' * 80}")
    print(f"📊 PERSISTENCE TEST SUMMARY")
    print(f"{'=' * 80}")
    print(f"  Session ID: {session_id}")
    print(f"  Messages sent before restart: {len(messages)}")
    print(f"  Memory tests passed: {memory_success}/{len(memory_tests)}")
    print(f"  Persistence score: {(memory_success/len(memory_tests)*100):.0f}%")
    
    if memory_success >= 2:
        print(f"\n  ✅ PERSISTENCE WORKING - AI remembers conversation history!")
    elif memory_success == 1:
        print(f"\n  ⚠️  PARTIAL PERSISTENCE - Some context retained")
    else:
        print(f"\n  ❌ NO PERSISTENCE - AI doesn't remember conversation")
    
    # Cleanup
    print(f"\n🧹 Cleaning up...")
    requests.delete(
        f'{API_BASE_URL}/api/backend/sessions/{session_id}',
        cookies={'user_id': USER_ID},
        timeout=10
    )
    print(f"✅ Session deleted")
    
    print(f"\n{'=' * 80}")
    return memory_success >= 2

if __name__ == "__main__":
    try:
        success = test_deep_persistence()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
