#!/usr/bin/env python3
"""
Test script for OpenCode UI API session creation
"""
import requests
import json

# Configuration
API_BASE_URL = "http://localhost:8000"
USER_ID = "188960770"  # From our previous testing

def test_create_session():
    """Test creating a new session"""
    url = f"{API_BASE_URL}/api/sessions"

    # Create session with a title
    payload = {
        "title": "Test Session from Python Script"
    }

    # Set up cookies for authentication
    cookies = {
        'user_id': USER_ID
    }

    print(f"Creating session for user {USER_ID}...")
    print(f"POST {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print(f"Cookies: {cookies}")

    try:
        response = requests.post(
            url,
            json=payload,
            cookies=cookies,
            timeout=30
        )

        print(f"\nResponse Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")

        if response.status_code == 200:
            result = response.json()
            print(f"Success! Created session:")
            print(json.dumps(result, indent=2))
        else:
            error_detail = response.json() if response.content else "No response body"
            print(f"Error: {error_detail}")

    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")

def test_list_sessions():
    """Test listing sessions"""
    url = f"{API_BASE_URL}/api/sessions"

    cookies = {
        'user_id': USER_ID
    }

    print(f"\nListing sessions for user {USER_ID}...")
    print(f"GET {url}")

    try:
        response = requests.get(
            url,
            cookies=cookies,
            timeout=10
        )

        print(f"Response Status: {response.status_code}")

        if response.status_code == 200:
            sessions = response.json()
            print(f"Found {len(sessions)} sessions:")
            for session in sessions:
                print(f"  - ID: {session.get('id')}, Title: {session.get('title')}")
        else:
            error_detail = response.json() if response.content else "No response body"
            print(f"Error: {error_detail}")

    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")

def test_list_agents():
    """Test listing agents to see if user has any"""
    url = f"{API_BASE_URL}/api/agents"

    cookies = {
        'user_id': USER_ID
    }

    print(f"\nChecking agents for user {USER_ID}...")
    print(f"GET {url}")

    try:
        response = requests.get(
            url,
            cookies=cookies,
            timeout=10
        )

        print(f"Response Status: {response.status_code}")

        if response.status_code == 200:
            agents = response.json()
            print(f"Found {len(agents)} agents:")
            for agent in agents:
                print(f"  - ID: {agent.get('id')}, Name: {agent.get('name')}, Active: {agent.get('is_active', 'unknown')}")
        else:
            error_detail = response.json() if response.content else "No response body"
            print(f"Error: {error_detail}")

    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    print("OpenCode UI API Test Script")
    print("=" * 40)

    # First check if user has agents (required for session creation)
    test_list_agents()

    # Test listing existing sessions
    test_list_sessions()

    # Try to create a new session
    test_create_session()

    # List sessions again to see if creation worked
    test_list_sessions()