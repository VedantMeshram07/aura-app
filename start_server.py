#!/usr/bin/env python3
"""
Enhanced server startup script with comprehensive error handling and diagnostics
"""
import os
import sys
import subprocess
import time
import socket
from pathlib import Path

def check_port_availability(port):
    """Check if a port is available"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('127.0.0.1', port))
            return True
    except OSError:
        return False

def check_dependencies():
    """Check if all required dependencies are installed"""
    print("🔍 Checking dependencies...")
    
    required_packages = [
        ('flask', 'flask'),
        ('flask_cors', 'flask_cors'), 
        ('firebase_admin', 'firebase_admin'),
        ('passlib', 'passlib'),
        ('python_dotenv', 'dotenv')
    ]
    
    missing_packages = []
    for pip_name, import_name in required_packages:
        try:
            __import__(import_name)
            print(f"   ✅ {pip_name}")
        except ImportError:
            missing_packages.append(pip_name)
            print(f"   ❌ {pip_name}")
    
    if missing_packages:
        print(f"\n❌ Missing packages: {', '.join(missing_packages)}")
        print("   Run: pip3 install --break-system-packages " + " ".join(missing_packages))
        return False
    
    print("✅ All dependencies are installed")
    return True

def check_firebase_config():
    """Check Firebase configuration"""
    print("\n🔍 Checking Firebase configuration...")
    
    backend_dir = Path(__file__).parent / "backend"
    service_key_path = backend_dir / "serviceAccountKey.json"
    
    if service_key_path.exists():
        print("   ✅ Firebase service account key found")
        return True
    else:
        print("   ⚠️  Firebase service account key not found")
        print("   📝 This is not critical - the app will use in-memory storage")
        print("   📝 To enable Firebase persistence:")
        print("      1. Get your service account key from Firebase Console")
        print("      2. Save it as 'backend/serviceAccountKey.json'")
        print("      3. Restart the application")
        return False

def check_file_structure():
    """Check if all required files exist"""
    print("\n🔍 Checking file structure...")
    
    required_files = [
        "backend/main.py",
        "backend/agents/auth_agent.py",
        "frontend/index.html",
        "frontend/script.js",
        "frontend/styles.css"
    ]
    
    missing_files = []
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"   ✅ {file_path}")
        else:
            missing_files.append(file_path)
            print(f"   ❌ {file_path}")
    
    if missing_files:
        print(f"\n❌ Missing files: {', '.join(missing_files)}")
        return False
    
    print("✅ All required files are present")
    return True

def run_auth_tests():
    """Run authentication tests"""
    print("\n🧪 Running authentication tests...")
    
    try:
        # Change to backend directory
        os.chdir("backend")
        
        # Run the test script
        result = subprocess.run([
            sys.executable, "test_auth_issue.py"
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✅ Authentication tests passed")
            return True
        else:
            print("❌ Authentication tests failed")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Authentication tests timed out")
        return False
    except Exception as e:
        print(f"❌ Error running authentication tests: {e}")
        return False
    finally:
        # Change back to original directory
        os.chdir("..")

def start_server():
    """Start the Flask server with proper error handling"""
    print("\n🚀 Starting server...")
    
    # Check if port is available
    if not check_port_availability(5000):
        print("❌ Port 5000 is already in use")
        print("   Kill existing processes or use a different port")
        return False
    
    try:
        os.chdir("backend")
        
        # Start the server
        print("📡 Server starting on http://127.0.0.1:5000")
        print("📡 Frontend available at http://127.0.0.1:5000/")
        print("\n🔧 Server logs:")
        print("-" * 50)
        
        # Run the server
        subprocess.run([sys.executable, "main.py"], check=True)
        
    except KeyboardInterrupt:
        print("\n\n🛑 Server stopped by user")
        return True
    except Exception as e:
        print(f"\n❌ Server failed to start: {e}")
        return False
    finally:
        os.chdir("..")

def main():
    """Main startup routine"""
    print("=" * 60)
    print("🌟 AURA Mental Health App - Server Startup")
    print("=" * 60)
    
    # Check dependencies
    if not check_dependencies():
        print("\n❌ Dependency check failed. Please install missing packages.")
        return 1
    
    # Check file structure
    if not check_file_structure():
        print("\n❌ File structure check failed. Please ensure all files are present.")
        return 1
    
    # Check Firebase config
    firebase_ok = check_firebase_config()
    
    # Run authentication tests
    if not run_auth_tests():
        print("\n⚠️  Authentication tests failed, but continuing anyway...")
    
    # Start server
    print("\n" + "=" * 60)
    print("🎯 All checks complete - starting server")
    print("=" * 60)
    
    if firebase_ok:
        print("🔥 Firebase: ENABLED - Data will persist")
    else:
        print("💾 Firebase: DISABLED - Using in-memory storage")
    
    start_server()
    return 0

if __name__ == "__main__":
    sys.exit(main())