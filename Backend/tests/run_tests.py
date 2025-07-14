#!/usr/bin/env python3
"""
Simple test runner for NeuroBot tests.
This script sets up the environment and runs the comprehensive test suite.
"""

import sys
import os
import subprocess
import time
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed."""
    required_packages = ['requests', 'flask', 'flask-cors']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ Missing required packages:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\nPlease install missing packages with:")
        print(f"pip install {' '.join(missing_packages)}")
        return False
    
    print("✅ All required dependencies are installed")
    return True

def check_server_status(url="http://localhost:5001"):
    """Check if the Flask server is running."""
    try:
        import requests
        response = requests.get(url, timeout=5)
        return response.status_code == 200
    except:
        return False

def start_server():
    """Start the Flask server in the background."""
    print("🚀 Starting Flask server...")
    
    # Change to the Backend directory
    backend_dir = Path(__file__).parent
    os.chdir(backend_dir)
    
    # Start server in background
    try:
        process = subprocess.Popen(
            [sys.executable, "app.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait a bit for server to start
        time.sleep(3)
        
        # Check if server started successfully
        if check_server_status():
            print("✅ Server started successfully")
            return process
        else:
            print("❌ Server failed to start")
            process.terminate()
            return None
            
    except Exception as e:
        print(f"❌ Error starting server: {str(e)}")
        return None

def run_tests():
    """Run the comprehensive test suite."""
    print("🧪 Running NeuroBot Viewer and Database Tests")
    print("=" * 60)
    
    # Check dependencies
    if not check_dependencies():
        return False
    
    # Check if server is already running
    if check_server_status():
        print("✅ Server is already running")
        server_process = None
    else:
        # Start server
        server_process = start_server()
        if not server_process:
            print("❌ Could not start server. Please start it manually with:")
            print("   cd Backend && python app.py")
            return False
    
    try:
        # Import and run tests
        from test_viewer_and_db import NeuroBotTester
        
        tester = NeuroBotTester()
        success = tester.run_all_tests()
        
        return success
        
    except Exception as e:
        print(f"❌ Error running tests: {str(e)}")
        return False
    
    finally:
        # Clean up server process if we started it
        if server_process:
            print("🛑 Stopping server...")
            server_process.terminate()
            server_process.wait()

def main():
    """Main function."""
    print("NeuroBot Test Suite Runner")
    print("=" * 40)
    
    # Check if we're in the right directory
    if not Path("app.py").exists():
        print("❌ Error: app.py not found in current directory")
        print("Please run this script from the Backend directory")
        return 1
    
    # Run tests
    success = run_tests()
    
    if success:
        print("\n🎉 All tests completed successfully!")
        return 0
    else:
        print("\n💥 Some tests failed. Please check the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 