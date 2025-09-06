#!/usr/bin/env python3
"""
Test script to reproduce login issues
"""
import sys
import os
sys.path.append('.')

from flask import Flask
from agents.auth_agent import auth_bp
import json

def test_auth_flow():
    """Test the complete authentication flow"""
    app = Flask(__name__)
    app.register_blueprint(auth_bp)
    
    print("=== AUTHENTICATION FLOW TEST ===")
    
    with app.test_client() as client:
        # Test 1: Signup
        print("\n1. Testing Signup...")
        signup_data = {
            'name': 'Test User',
            'email': 'test@example.com', 
            'password': 'testpass123',
            'age': 25,
            'region': 'US'
        }
        
        signup_response = client.post('/auth/signup', 
                                    json=signup_data,
                                    content_type='application/json')
        print(f"   Status: {signup_response.status_code}")
        signup_result = signup_response.get_json()
        print(f"   Response: {signup_result}")
        
        if signup_response.status_code != 201:
            print("   ❌ SIGNUP FAILED")
            return False
        else:
            print("   ✅ SIGNUP SUCCESS")
        
        # Test 2: Login with correct credentials
        print("\n2. Testing Login with correct credentials...")
        login_data = {
            'email': 'test@example.com',
            'password': 'testpass123'
        }
        
        login_response = client.post('/auth/login',
                                   json=login_data, 
                                   content_type='application/json')
        print(f"   Status: {login_response.status_code}")
        login_result = login_response.get_json()
        print(f"   Response: {login_result}")
        
        if login_response.status_code != 200:
            print("   ❌ LOGIN FAILED")
            return False
        else:
            print("   ✅ LOGIN SUCCESS")
        
        # Test 3: Login with case variations
        print("\n3. Testing Login with uppercase email...")
        login_upper = {
            'email': 'TEST@EXAMPLE.COM',
            'password': 'testpass123'
        }
        
        login_response_upper = client.post('/auth/login',
                                         json=login_upper,
                                         content_type='application/json')
        print(f"   Status: {login_response_upper.status_code}")
        print(f"   Response: {login_response_upper.get_json()}")
        
        if login_response_upper.status_code != 200:
            print("   ❌ CASE INSENSITIVE LOGIN FAILED")
            return False
        else:
            print("   ✅ CASE INSENSITIVE LOGIN SUCCESS")
        
        # Test 4: Login with wrong password
        print("\n4. Testing Login with wrong password...")
        login_wrong = {
            'email': 'test@example.com',
            'password': 'wrongpass'
        }
        
        login_response_wrong = client.post('/auth/login',
                                         json=login_wrong,
                                         content_type='application/json')
        print(f"   Status: {login_response_wrong.status_code}")
        print(f"   Response: {login_response_wrong.get_json()}")
        
        if login_response_wrong.status_code != 401:
            print("   ❌ WRONG PASSWORD TEST FAILED")
            return False
        else:
            print("   ✅ WRONG PASSWORD TEST SUCCESS")
        
        # Test 5: Login with non-existent user
        print("\n5. Testing Login with non-existent user...")
        login_nonexistent = {
            'email': 'nonexistent@example.com',
            'password': 'somepass'
        }
        
        login_response_nonexistent = client.post('/auth/login',
                                               json=login_nonexistent,
                                               content_type='application/json')
        print(f"   Status: {login_response_nonexistent.status_code}")
        print(f"   Response: {login_response_nonexistent.get_json()}")
        
        if login_response_nonexistent.status_code != 401:
            print("   ❌ NON-EXISTENT USER TEST FAILED")
            return False
        else:
            print("   ✅ NON-EXISTENT USER TEST SUCCESS")
    
    print("\n=== ALL TESTS PASSED ===")
    return True

def test_firebase_status():
    """Test Firebase connectivity and status"""
    print("\n=== FIREBASE STATUS TEST ===")
    
    try:
        from agents.auth_agent import _get_db_or_none
        db = _get_db_or_none()
        if db:
            print("✅ Firebase connected successfully")
            return True
        else:
            print("❌ Firebase not available - using in-memory fallback")
            return False
    except Exception as e:
        print(f"❌ Firebase error: {e}")
        return False

def main():
    print("Starting Authentication Issue Diagnosis...")
    
    # Test Firebase status
    firebase_ok = test_firebase_status()
    
    # Test authentication flow
    auth_ok = test_auth_flow()
    
    print("\n=== DIAGNOSIS SUMMARY ===")
    print(f"Firebase Status: {'✅ OK' if firebase_ok else '❌ ISSUE'}")
    print(f"Auth Flow: {'✅ OK' if auth_ok else '❌ ISSUE'}")
    
    if not firebase_ok:
        print("\n🔧 RECOMMENDATIONS:")
        print("1. Firebase is not configured - using in-memory storage")
        print("2. This should not affect basic login/signup functionality")
        print("3. Data will not persist between server restarts")
        
    if not auth_ok:
        print("\n🚨 CRITICAL ISSUE FOUND:")
        print("Authentication flow is broken - needs immediate attention")
    else:
        print("\n✅ Authentication flow appears to be working correctly")

if __name__ == "__main__":
    main()