#!/usr/bin/env python3
"""
Quick persistence test - manual user creation flow
"""
import requests
import json
import time
import subprocess

API_BASE_URL = 'http://localhost:8000'

def create_test_user():
    """Create a test user directly via API"""
    # For testing, we'll use the backend's user creation endpoint
    # In production, this would be done via GitHub OAuth
    return "test_user_123"  # Placeholder user ID

def test_session_persistence():
    """Test if session conversations persist across container restarts"""
    
    print("=" * 80)
    print("QUICK PERSISTENCE TEST")
    print("=" * 80)
    
    # Since auth requires GitHub OAuth, let's test the core functionality directly
    # by checking if the OpenCode session ID is being stored in the database
    
    print("\n1️⃣  Testing session creation...")
    
    # Create session via API (this requires auth, so we'll check the database directly)
    print("   Note: Full test requires GitHub authentication")
    print("   Checking database schema instead...")
    
    # Check if database has the new column
    try:
        import sqlite3
        conn = sqlite3.connect('data/db.sqlite3')
        cursor = conn.cursor()
        
        # Check if opencode_session_id column exists
        cursor.execute("PRAGMA table_info(sessions)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        print(f"\n✅ Database columns: {column_names}")
        
        if 'opencode_session_id' in column_names:
            print("✅ opencode_session_id column exists in database!")
        else:
            print("❌ opencode_session_id column NOT found")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Database check failed: {e}")
    
    print("\n2️⃣  Testing symbolic link setup in docker_ops.py...")
    
    # Read docker_ops.py to verify symlink setup
    with open('app/core/docker_ops.py', 'r') as f:
        content = f.read()
        if 'opencode-data' in content and 'ln -sf' in content:
            print("✅ Symbolic link setup found in docker_ops.py")
        else:
            print("❌ Symbolic link setup NOT found")
    
    print("\n3️⃣  Testing session reuse logic in routes.py...")
    
    # Read routes.py to verify session reuse
    with open('app/backend/routes.py', 'r') as f:
        content = f.read()
        if 'existing_opencode_session_id' in content:
            print("✅ Session reuse logic found in routes.py")
        else:
            print("❌ Session reuse logic NOT found")
    
    print("\n" + "=" * 80)
    print("MANUAL TEST INSTRUCTIONS:")
    print("=" * 80)
    print("""
To fully test persistence:

1. Login via GitHub OAuth at http://localhost:3000
2. Create a new chat session
3. Send a message: "Remember this: blue elephant"
4. Note the session ID from the URL
5. Run: docker stop agent_<session_id>
6. Send another message in the same session
7. Ask: "What did I tell you to remember?"
8. If it responds with "blue elephant", persistence works! ✅

Expected behavior:
- Session data persists in volume: /mnt/volume/<session_id>/opencode-data
- OpenCode session ID is stored in database
- Chat endpoint reuses existing OpenCode session ID
- AI remembers conversation history after container restart
""")

if __name__ == '__main__':
    test_session_persistence()
