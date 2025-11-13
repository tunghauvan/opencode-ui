#!/usr/bin/env python3
"""
Test OpenCode agent API through backend
"""
import requests
import json

API_BASE = "http://localhost:8000"
USER_ID = "188960770"

print("=" * 70)
print("Testing OpenCode Agent API through Backend")
print("=" * 70)

# Use existing session
session_id = "3f3e78be"

print(f"\n1. Checking session status...")
resp = requests.get(
    f"{API_BASE}/api/backend/sessions/{session_id}",
    cookies={"user_id": USER_ID}
)

if resp.status_code == 200:
    session = resp.json()
    print(f"✅ Session found: {session_id}")
    print(f"   Name: {session['name']}")
    print(f"   Container: {session.get('container_id', 'None')[:12]}...")
    print(f"   Status: {session['status']}")
else:
    print(f"❌ Session not found: {resp.status_code}")
    exit(1)

print(f"\n2. Sending chat message through backend...")
message = "What is machine learning?"
print(f"   Prompt: '{message}'")

resp = requests.post(
    f"{API_BASE}/api/backend/sessions/{session_id}/chat",
    json={"prompt": message},
    cookies={"user_id": USER_ID},
    timeout=30
)

print(f"   Status: {resp.status_code}")
if resp.status_code == 200:
    result = resp.json()
    print(f"✅ Message sent successfully!")
    print(f"   Response: {json.dumps(result, indent=3)}")
else:
    print(f"❌ Error: {resp.text[:300]}")

print("\n" + "=" * 70)
print("Test completed! Message went through backend API")
print("=" * 70)
