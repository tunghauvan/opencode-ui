#!/usr/bin/env python3
"""
Test script for OpenCode Agent Controller API
Tests all endpoints and functionality
"""

import requests
import json
import time
import sys
from typing import Dict, Any

# Configuration
BASE_URL = "http://localhost:8001"
TEST_SESSION_ID = "test-session-123"
SERVICE_SECRET = "default-secret-change-in-production"  # Should match AGENT_SERVICE_SECRET env var

def get_headers():
    """Get headers with service secret"""
    return {"X-Service-Secret": SERVICE_SECRET}

def test_health():
    """Test health endpoint"""
    print("🔍 Testing health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        response.raise_for_status()
        data = response.json()
        print(f"✅ Health check passed: {data}")
        return True
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_create_session():
    """Test session creation"""
    print(f"🔍 Testing session creation for {TEST_SESSION_ID}...")
    try:
        payload = {
            "session_id": TEST_SESSION_ID,
            "github_token": "ghu_test_token_123"
        }
        response = requests.post(f"{BASE_URL}/sessions", json=payload, headers=get_headers())
        response.raise_for_status()
        data = response.json()
        print(f"✅ Session created: {data}")
        return True
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 409:
            print(f"⚠️  Session {TEST_SESSION_ID} already exists")
            return True
        else:
            print(f"❌ Session creation failed: {e}")
            return False
    except Exception as e:
        print(f"❌ Session creation failed: {e}")
        return False

def test_get_session():
    """Test getting session info"""
    print(f"🔍 Testing get session {TEST_SESSION_ID}...")
    try:
        response = requests.get(f"{BASE_URL}/sessions/{TEST_SESSION_ID}", headers=get_headers())
        response.raise_for_status()
        data = response.json()
        print(f"✅ Session info: {json.dumps(data, indent=2)}")
        return True
    except Exception as e:
        print(f"❌ Get session failed: {e}")
        return False

def test_list_sessions():
    """Test listing all sessions"""
    print("🔍 Testing list sessions...")
    try:
        response = requests.get(f"{BASE_URL}/sessions", headers=get_headers())
        response.raise_for_status()
        data = response.json()
        print(f"✅ Sessions list: {len(data['sessions'])} sessions found")
        return True
    except Exception as e:
        print(f"❌ List sessions failed: {e}")
        return False

def test_update_auth():
    """Test updating auth data"""
    print(f"🔍 Testing update auth for {TEST_SESSION_ID}...")
    try:
        payload = {
            "github_copilot": {
                "type": "oauth",
                "refresh": "updated_token_456",
                "access_token": "access_token_789"
            }
        }
        response = requests.put(f"{BASE_URL}/sessions/{TEST_SESSION_ID}/auth", json=payload, headers=get_headers())
        response.raise_for_status()
        data = response.json()
        print(f"✅ Auth updated: {data}")
        return True
    except Exception as e:
        print(f"❌ Update auth failed: {e}")
        return False

def test_run_container():
    """Test running container for session"""
    print(f"🔍 Testing run container for {TEST_SESSION_ID}...")
    try:
        payload = {
            "image": "alpine:latest",
            "environment": {
                "TEST_VAR": "test_value"
            }
        }
        response = requests.post(f"{BASE_URL}/sessions/{TEST_SESSION_ID}/run", json=payload, headers=get_headers())
        response.raise_for_status()
        data = response.json()
        print(f"✅ Container started: {data}")

        # Wait a bit for container to start
        time.sleep(2)
        return True
    except Exception as e:
        print(f"❌ Run container failed: {e}")
        return False

def test_get_logs():
    """Test getting container logs"""
    print(f"🔍 Testing get logs for {TEST_SESSION_ID}...")
    try:
        response = requests.get(f"{BASE_URL}/sessions/{TEST_SESSION_ID}/logs", headers=get_headers())
        response.raise_for_status()
        data = response.json()
        print(f"✅ Container logs (first 200 chars): {data['logs'][:200]}...")
        return True
    except Exception as e:
        print(f"❌ Get logs failed: {e}")
        return False

def test_stop_container():
    """Test stopping container"""
    print(f"🔍 Testing stop container for {TEST_SESSION_ID}...")
    try:
        response = requests.post(f"{BASE_URL}/sessions/{TEST_SESSION_ID}/stop", headers=get_headers())
        response.raise_for_status()
        data = response.json()
        print(f"✅ Container stopping: {data}")

        # Wait for container to stop
        time.sleep(3)
        return True
    except Exception as e:
        print(f"❌ Stop container failed: {e}")
        return False

def test_delete_session():
    """Test deleting session"""
    print(f"🔍 Testing delete session {TEST_SESSION_ID}...")
    try:
        response = requests.delete(f"{BASE_URL}/sessions/{TEST_SESSION_ID}", headers=get_headers())
        response.raise_for_status()
        data = response.json()
        print(f"✅ Session deleted: {data}")
        return True
    except Exception as e:
        print(f"❌ Delete session failed: {e}")
        return False

def wait_for_service(timeout: int = 30):
    """Wait for service to be ready"""
    print("⏳ Waiting for agent-controller service to be ready...")
    start_time = time.time()

    while time.time() - start_time < timeout:
        try:
            response = requests.get(f"{BASE_URL}/health", timeout=5)
            if response.status_code == 200:
                print("✅ Service is ready!")
                return True
        except:
            pass

        time.sleep(2)

    print("❌ Service failed to start within timeout")
    return False

def main():
    """Run all tests"""
    print("🚀 Starting OpenCode Agent Controller API Tests")
    print("=" * 50)

    # Wait for service
    if not wait_for_service():
        sys.exit(1)

    # Run tests
    tests = [
        test_health,
        test_create_session,
        test_get_session,
        test_list_sessions,
        test_update_auth,
        test_run_container,
        test_get_logs,
        test_stop_container,
        test_delete_session,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1
        print()

    print("=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed!")
        sys.exit(0)
    else:
        print("❌ Some tests failed")
        sys.exit(1)

if __name__ == "__main__":
    main()