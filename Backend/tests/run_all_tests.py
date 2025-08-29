#!/usr/bin/env python3
"""
Master test runner for JSON migration.
Runs all test suites and provides comprehensive reporting.
"""

import subprocess
import sys
import time
from pathlib import Path

def run_test(test_name: str, command: str, description: str = ""):
    """Run a test and return results"""
    print(f"\n{'='*60}")
    print(f"🧪 Running: {test_name}")
    if description:
        print(f"📝 {description}")
    print(f"{'='*60}")
    
    start_time = time.time()
    
    try:
        # Run the test
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent
        )
        
        execution_time = time.time() - start_time
        
        # Print output
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print("⚠️  Warnings/Errors:")
            print(result.stderr)
            
        # Determine success
        success = result.returncode == 0
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"\n{status} {test_name} completed in {execution_time:.2f}s")
        
        return {
            "name": test_name,
            "success": success,
            "return_code": result.returncode,
            "execution_time": execution_time,
            "stdout": result.stdout,
            "stderr": result.stderr
        }
        
    except Exception as e:
        execution_time = time.time() - start_time
        print(f"❌ CRASH {test_name} crashed: {str(e)}")
        
        return {
            "name": test_name,
            "success": False,
            "return_code": -1,
            "execution_time": execution_time,
            "stdout": "",
            "stderr": str(e)
        }

def main():
    """Run all tests"""
    print("🚀 NeuroBot JSON Migration - Comprehensive Test Suite")
    print("=" * 80)
    print("This script will run all available tests to verify the JSON migration.")
    print("=" * 80)
    
    # Define all tests
    tests = [
        {
            "name": "Simple JSON Tests",
            "command": "python test_simple.py",
            "description": "Tests basic JSON functionality, CRUD operations, edge cases, and performance"
        },
        {
            "name": "Comprehensive Tests",
            "command": "python test_json_migration.py",
            "description": "Tests all system components including vector store integration and error handling"
        }
    ]
    
    # Check if we're in the right directory
    if not Path("app").exists():
        print("❌ Error: Please run this script from the Backend directory")
        print("   cd Backend && python run_all_tests.py")
        return 1
        
    # Run all tests
    results = []
    for test in tests:
        result = run_test(test["name"], test["command"], test["description"])
        results.append(result)
        
        # Add a small delay between tests
        time.sleep(1)
    
    # Print comprehensive summary
    print(f"\n{'='*80}")
    print("📊 COMPREHENSIVE TEST SUMMARY")
    print(f"{'='*80}")
    
    total_tests = len(results)
    passed_tests = sum(1 for r in results if r["success"])
    failed_tests = total_tests - passed_tests
    total_time = sum(r["execution_time"] for r in results)
    
    print(f"Total Test Suites: {total_tests}")
    print(f"✅ Passed: {passed_tests}")
    print(f"❌ Failed: {failed_tests}")
    print(f"⏱️  Total Execution Time: {total_time:.2f}s")
    
    # Detailed results
    print(f"\n📋 Detailed Results:")
    print("-" * 80)
    
    for result in results:
        status = "✅ PASS" if result["success"] else "❌ FAIL"
        print(f"{status} {result['name']}")
        print(f"    Time: {result['execution_time']:.2f}s")
        print(f"    Return Code: {result['return_code']}")
        
        if result["stderr"]:
            print(f"    Errors: {result['stderr'][:100]}...")
            
    # Recommendations
    print(f"\n💡 Recommendations:")
    print("-" * 80)
    
    if failed_tests == 0:
        print("🎉 All test suites passed! The JSON migration is working correctly.")
        print("✅ The system is ready for production use.")
        print("✅ Consider running vector store rebuilds for active knowledge bases.")
        print("✅ Monitor system performance in production.")
    else:
        print(f"🔧 {failed_tests} test suite(s) failed.")
        print("❌ Review the failed tests above before deployment.")
        print("❌ Check error logs for specific issues.")
        print("❌ Consider rolling back if critical failures occur.")
        
    # Next steps
    print(f"\n🚀 Next Steps:")
    print("-" * 80)
    
    if failed_tests == 0:
        print("1. ✅ Deploy the JSON migration to production")
        print("2. ✅ Run vector store rebuilds for active KBs")
        print("3. ✅ Monitor system performance")
        print("4. ✅ Consider removing old knowledge.txt files")
    else:
        print("1. ❌ Fix failing tests before deployment")
        print("2. ❌ Review error logs and fix issues")
        print("3. ❌ Re-run tests to verify fixes")
        print("4. ❌ Only deploy when all tests pass")
        
    # API testing note
    print(f"\n📡 API Testing:")
    print("-" * 80)
    print("To test the actual Flask API endpoints:")
    print("1. Start the Flask server: python app.py")
    print("2. In another terminal: python test_api_endpoints.py")
    print("3. This will test all REST endpoints with real HTTP requests")
    
    return 0 if failed_tests == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
