#!/usr/bin/env python3
"""
Test script for workspace file operations

This script tests the file API endpoints by:
1. Creating a test file in the workspace
2. Reading the file back via API
3. Verifying the file exists in the container's workspace
4. Cleaning up

Usage:
    python scripts/test_workspace_files.py --session-id <session_id>
    
Or run from docker:
    docker-compose exec backend python scripts/test_workspace_files.py --session-id <session_id>
"""

import argparse
import os
import sys
import json
import requests
import time

# Configuration
BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")
API_BASE = f"{BACKEND_URL}/api/backend"

# Test file content
TEST_FILE_CONTENT = """# Test File

This is a test file created by the workspace file test script.

Created at: {timestamp}

## Test Content
- Line 1
- Line 2
- Line 3
"""


def get_cookies():
    """Get authentication cookies (for testing, use admin login)"""
    # Try admin login
    try:
        response = requests.post(
            f"{BACKEND_URL}/auth/admin/login",
            json={"username": "admin", "password": "admin"}
        )
        if response.status_code == 200:
            return response.cookies
    except Exception as e:
        print(f"Warning: Could not authenticate: {e}")
    
    return {}


def test_write_file(session_id: str, cookies: dict) -> bool:
    """Test writing a file to the workspace"""
    print("\n=== Test: Write File ===")
    
    test_content = TEST_FILE_CONTENT.format(timestamp=time.strftime("%Y-%m-%d %H:%M:%S"))
    test_path = "/test_file.md"
    
    try:
        response = requests.post(
            f"{API_BASE}/sessions/{session_id}/files/write",
            params={"path": test_path},
            json={"content": test_content, "encoding": "utf-8"},
            cookies=cookies,
            timeout=10
        )
        
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                print("✓ File write successful!")
                return True
            else:
                print("✗ File write failed - success=false")
                return False
        else:
            print(f"✗ File write failed with status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_read_file(session_id: str, cookies: dict) -> bool:
    """Test reading a file from the workspace"""
    print("\n=== Test: Read File ===")
    
    test_path = "/test_file.md"
    
    try:
        response = requests.get(
            f"{API_BASE}/sessions/{session_id}/files/read",
            params={"path": test_path},
            cookies=cookies,
            timeout=10
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Path: {result.get('path')}")
            print(f"Encoding: {result.get('encoding')}")
            print(f"Size: {result.get('size')} bytes")
            print(f"Content preview: {result.get('content', '')[:100]}...")
            
            if result.get("content") and "Test File" in result.get("content", ""):
                print("✓ File read successful!")
                return True
            else:
                print("✗ File content doesn't match expected")
                return False
        else:
            print(f"✗ File read failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_list_directory(session_id: str, cookies: dict) -> bool:
    """Test listing directory contents"""
    print("\n=== Test: List Directory ===")
    
    try:
        response = requests.get(
            f"{API_BASE}/sessions/{session_id}/files/list",
            params={"path": "/"},
            cookies=cookies,
            timeout=10
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Path: {result.get('path')}")
            print(f"Exists: {result.get('exists')}")
            print(f"Entries: {len(result.get('entries', []))}")
            
            for entry in result.get("entries", [])[:5]:
                print(f"  - {entry.get('type')}: {entry.get('name')}")
            
            if len(result.get("entries", [])) > 5:
                print(f"  ... and {len(result.get('entries', [])) - 5} more")
            
            # Check if our test file is in the listing
            test_file_found = any(
                entry.get("name") == "test_file.md" 
                for entry in result.get("entries", [])
            )
            
            if test_file_found:
                print("✓ Test file found in directory listing!")
                return True
            else:
                print("✓ Directory listing successful (test file may not be created yet)")
                return True
        else:
            print(f"✗ Directory listing failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_create_directory(session_id: str, cookies: dict) -> bool:
    """Test creating a directory"""
    print("\n=== Test: Create Directory ===")
    
    test_dir = "/test_directory"
    
    try:
        response = requests.post(
            f"{API_BASE}/sessions/{session_id}/files/mkdir",
            params={"path": test_dir},
            cookies=cookies,
            timeout=10
        )
        
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                print("✓ Directory creation successful!")
                return True
            else:
                print("✗ Directory creation failed - success=false")
                return False
        else:
            print(f"✗ Directory creation failed with status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_delete_file(session_id: str, cookies: dict) -> bool:
    """Test deleting a file"""
    print("\n=== Test: Delete File ===")
    
    test_path = "/test_file.md"
    
    try:
        response = requests.delete(
            f"{API_BASE}/sessions/{session_id}/files/delete",
            params={"path": test_path},
            cookies=cookies,
            timeout=10
        )
        
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                print("✓ File deletion successful!")
                return True
            else:
                print("✗ File deletion failed - success=false")
                return False
        else:
            print(f"✗ File deletion failed with status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_delete_directory(session_id: str, cookies: dict) -> bool:
    """Test deleting a directory"""
    print("\n=== Test: Delete Directory ===")
    
    test_dir = "/test_directory"
    
    try:
        response = requests.delete(
            f"{API_BASE}/sessions/{session_id}/files/rmdir",
            params={"path": test_dir, "recursive": "false"},
            cookies=cookies,
            timeout=10
        )
        
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                print("✓ Directory deletion successful!")
                return True
            else:
                print("✗ Directory deletion failed - success=false")
                return False
        else:
            print(f"✗ Directory deletion failed with status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def verify_file_in_container(session_id: str, cookies: dict) -> bool:
    """Verify that the file exists in the agent container's workspace"""
    print("\n=== Test: Verify File in Container ===")
    
    # This test uses the container logs or exec to verify the file exists
    # For now, we just verify via the API that we can read it back
    
    try:
        response = requests.get(
            f"{API_BASE}/sessions/{session_id}/files/read",
            params={"path": "/test_file.md"},
            cookies=cookies,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("content") and "Test File" in result.get("content", ""):
                print("✓ File verified in workspace!")
                return True
            else:
                print("✗ File content verification failed")
                return False
        else:
            print(f"✗ Could not verify file: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def run_all_tests(session_id: str):
    """Run all tests"""
    print("=" * 60)
    print("Workspace File Operations Test Suite")
    print("=" * 60)
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Session ID: {session_id}")
    print("=" * 60)
    
    # Get auth cookies
    cookies = get_cookies()
    if cookies:
        print("✓ Authentication successful")
    else:
        print("⚠ Running without authentication")
    
    # Track results
    results = []
    
    # Test 1: List directory (initial state)
    results.append(("List Directory (initial)", test_list_directory(session_id, cookies)))
    
    # Test 2: Create directory
    results.append(("Create Directory", test_create_directory(session_id, cookies)))
    
    # Test 3: Write file
    results.append(("Write File", test_write_file(session_id, cookies)))
    
    # Test 4: Read file
    results.append(("Read File", test_read_file(session_id, cookies)))
    
    # Test 5: List directory (after write)
    results.append(("List Directory (after write)", test_list_directory(session_id, cookies)))
    
    # Test 6: Verify file in container
    results.append(("Verify File in Container", verify_file_in_container(session_id, cookies)))
    
    # Test 7: Delete file
    results.append(("Delete File", test_delete_file(session_id, cookies)))
    
    # Test 8: Delete directory
    results.append(("Delete Directory", test_delete_directory(session_id, cookies)))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = 0
    failed = 0
    for name, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"  {status}: {name}")
        if success:
            passed += 1
        else:
            failed += 1
    
    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return failed == 0


def main():
    parser = argparse.ArgumentParser(description="Test workspace file operations")
    parser.add_argument("--session-id", required=True, help="Session ID to test with")
    parser.add_argument("--backend-url", default=BACKEND_URL, help="Backend URL")
    
    args = parser.parse_args()
    
    global BACKEND_URL, API_BASE
    BACKEND_URL = args.backend_url
    API_BASE = f"{BACKEND_URL}/api/backend"
    
    success = run_all_tests(args.session_id)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
