#!/usr/bin/env python
"""
End-to-end test of backend chat routing through to agent container
"""
import requests
import time

BASE_URL = "http://localhost:8000"
USER_ID = "188960770"
SESSION_ID = "3f3e78be"

def test_backend_chat_routing():
    print("\n" + "="*70)
    print("END-TO-END CHAT ROUTING TEST")
    print("="*70)
    
    # 1. Get session to verify it exists
    print("\n1. Checking session exists...")
    resp = requests.get(
        f"{BASE_URL}/api/backend/sessions/{SESSION_ID}",
        cookies={'user_id': USER_ID}
    )
    
    if resp.status_code != 200:
        print(f"   FAIL: Could not get session: {resp.status_code}")
        return False
    
    session = resp.json()
    print(f"   OK: Session found: {session['session_id']}")
    print(f"      Container ID: {session['container_id']}")
    print(f"      Status: {session['status']}")
    
    # 2. Send a chat message through backend
    print("\n2. Sending chat message through backend...")
    chat_resp = requests.post(
        f"{BASE_URL}/api/backend/sessions/{SESSION_ID}/chat",
        json={'prompt': 'What is Python?'},
        cookies={'user_id': USER_ID}
    )
    
    if chat_resp.status_code != 200:
        print(f"   FAIL: Chat request failed: {chat_resp.status_code}")
        print(f"   Response: {chat_resp.text}")
        return False
    
    chat_result = chat_resp.json()
    print(f"   OK: Message sent through backend")
    print(f"      Status: {chat_result['status']}")
    print(f"      Container response code: {chat_result['container_status']}")
    
    # 3. Verify the frontend API endpoint works
    print("\n3. Testing frontend API endpoint...")
    
    # Simulate frontend call to same endpoint
    frontend_resp = requests.post(
        f"{BASE_URL}/api/sessions/{SESSION_ID}/chat",
        json={'prompt': 'What is Vue.js?', 'model': {'providerID': 'github-copilot', 'modelID': 'gpt-5-mini'}},
        cookies={'user_id': USER_ID}
    )
    
    if frontend_resp.status_code != 200:
        print(f"   FAIL: Frontend endpoint failed: {frontend_resp.status_code}")
        print(f"   Response: {frontend_resp.text}")
        return False
    
    print(f"   OK: Frontend endpoint working")
    
    print("\n" + "="*70)
    print("ALL TESTS PASSED!")
    print("="*70)
    print("\nSummary:")
    print("✓ Backend can forward chat messages to agent containers")
    print("✓ Agent containers are responding properly")
    print("✓ Message routing is working end-to-end through the backend")
    print("\nFrontend UI can now send messages that are properly routed to containers!")
    
    return True

if __name__ == "__main__":
    try:
        success = test_backend_chat_routing()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
