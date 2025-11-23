#!/usr/bin/env python3
"""
Test script for admin login functionality
"""
import requests
import json

API_URL = "http://localhost:8000"

def test_admin_login():
    """Test admin login endpoint"""
    print("=" * 60)
    print("Testing Admin Login")
    print("=" * 60)
    
    # Test 1: Login with correct credentials
    print("\n1. Testing login with correct credentials (admin/admin)")
    response = requests.post(
        f"{API_URL}/auth/admin/login",
        json={"username": "admin", "password": "admin"},
        allow_redirects=False
    )
    
    print(f"   Status Code: {response.status_code}")
    print(f"   Response: {response.json()}")
    
    if response.status_code == 200:
        print("   ✅ Login successful!")
        
        # Check if user_id cookie is set
        if 'user_id' in response.cookies:
            user_id = response.cookies['user_id']
            print(f"   ✅ user_id cookie set: {user_id}")
            
            # Test 2: Check if we can access protected endpoint
            print("\n2. Testing access to protected endpoint (/auth/me)")
            me_response = requests.get(
                f"{API_URL}/auth/me",
                cookies={'user_id': user_id}
            )
            
            print(f"   Status Code: {me_response.status_code}")
            if me_response.status_code == 200:
                print(f"   Response: {json.dumps(me_response.json(), indent=2)}")
                print("   ✅ Protected endpoint access successful!")
            else:
                print(f"   ❌ Protected endpoint access failed: {me_response.text}")
        else:
            print("   ⚠️  user_id cookie not set")
    else:
        print(f"   ❌ Login failed: {response.text}")
    
    # Test 3: Login with incorrect credentials
    print("\n3. Testing login with incorrect credentials (admin/wrong)")
    response = requests.post(
        f"{API_URL}/auth/admin/login",
        json={"username": "admin", "password": "wrong"}
    )
    
    print(f"   Status Code: {response.status_code}")
    if response.status_code == 401:
        print("   ✅ Correctly rejected invalid credentials")
    else:
        print(f"   ❌ Expected 401, got {response.status_code}")
    
    # Test 4: Login without credentials
    print("\n4. Testing login without credentials")
    try:
        response = requests.post(
            f"{API_URL}/auth/admin/login",
            json={}
        )
        print(f"   Status Code: {response.status_code}")
        if response.status_code == 422:
            print("   ✅ Correctly rejected missing credentials")
        else:
            print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"   ✅ Request validation failed as expected: {e}")
    
    print("\n" + "=" * 60)
    print("Test Complete!")
    print("=" * 60)

if __name__ == "__main__":
    test_admin_login()
