# backend/test.py

import requests
import json

def test_backend():
    """Test the basic backend functionality"""
    base_url = "http://127.0.0.1:5000"
    
    print("Testing AURA Backend...")
    
    # Test 1: Check if server is running
    try:
        response = requests.get(f"{base_url}/")
        print(f"✅ Server is running: {response.status_code}")
    except Exception as e:
        print(f"❌ Server not running: {e}")
        return
    
    # Test 2: Test signup endpoint
    try:
        signup_data = {
            "name": "Test User",
            "age": 25,
            "email": "test@example.com",
            "password": "testpassword123"
        }
        response = requests.post(f"{base_url}/auth/signup", json=signup_data)
        print(f"✅ Signup endpoint: {response.status_code}")
        if response.status_code == 201:
            print("   - User created successfully")
        elif response.status_code == 409:
            print("   - User already exists (expected)")
    except Exception as e:
        print(f"❌ Signup test failed: {e}")
    
    # Test 3: Test login endpoint
    try:
        login_data = {
            "email": "test@example.com",
            "password": "testpassword123"
        }
        response = requests.post(f"{base_url}/auth/login", json=login_data)
        print(f"✅ Login endpoint: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   - Login successful for user: {data.get('name')}")
            user_id = data.get('userId')
        else:
            print(f"   - Login failed: {response.json().get('error')}")
            return
    except Exception as e:
        print(f"❌ Login test failed: {e}")
        return
    
    # Test 4: Test Elara greeting
    try:
        greeting_data = {
            "userId": user_id,
            "metrics": {"anxiety": 50, "depression": 50, "stress": 50}
        }
        response = requests.post(f"{base_url}/elara/greeting", json=greeting_data)
        print(f"✅ Elara greeting: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   - Greeting: {data.get('response')[:50]}...")
    except Exception as e:
        print(f"❌ Elara greeting test failed: {e}")
    
    # Test 5: Test Vero resource
    try:
        resource_data = {"query": "stress"}
        response = requests.post(f"{base_url}/vero/getResource", json=resource_data)
        print(f"✅ Vero resource: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   - Resource: {data.get('title')}")
    except Exception as e:
        print(f"❌ Vero resource test failed: {e}")
    
    print("\n🎉 Backend tests completed!")

if __name__ == "__main__":
    test_backend()
