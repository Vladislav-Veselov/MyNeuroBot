#!/usr/bin/env python3
"""
Test runner for NeuroBot database functionality.
Run this script to test all database features before deployment.
"""

import subprocess
import sys
from pathlib import Path

def run_test_script(script_path, description):
    """Run a test script and return success status."""
    print(f"\n🧪 Running {description}...")
    print("=" * 60)
    
    try:
        result = subprocess.run([
            sys.executable, str(script_path)
        ], capture_output=False, text=True)
        
        if result.returncode == 0:
            print(f"✅ {description} - PASSED")
            return True
        else:
            print(f"❌ {description} - FAILED")
            return False
            
    except Exception as e:
        print(f"💥 Error running {description}: {e}")
        return False

def main():
    """Main test runner."""
    print("🚀 NeuroBot Database Test Suite")
    print("=" * 60)
    print("This will test all database functionality before deployment")
    print("=" * 60)
    
    backend_dir = Path("Backend")
    
    # List of tests to run
    tests = [
        (backend_dir / "test_database.py", "Database Functionality Tests"),
        (backend_dir / "test_postgres_connection.py", "PostgreSQL Connection Test"),
    ]
    
    passed_tests = 0
    total_tests = len(tests)
    
    for script_path, description in tests:
        if not script_path.exists():
            print(f"⚠️  Test script not found: {script_path}")
            continue
            
        if run_test_script(script_path, description):
            passed_tests += 1
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    print(f"Tests passed: {passed_tests}/{total_tests}")
    
    if passed_tests == total_tests:
        print("🎉 ALL TESTS PASSED!")
        print("✅ Database functionality is working correctly")
        print("✅ Ready for PostgreSQL deployment to Render")
        print("\n📋 Next steps:")
        print("1. Create PostgreSQL database in Render Dashboard")
        print("2. Add DATABASE_URL environment variable")
        print("3. Deploy your changes")
        return True
    else:
        print("❌ SOME TESTS FAILED!")
        print("🔧 Please fix the issues before deploying")
        return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n💥 Unexpected error: {e}")
        sys.exit(1)
