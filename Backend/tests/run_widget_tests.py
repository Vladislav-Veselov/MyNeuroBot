#!/usr/bin/env python3
"""
Comprehensive test runner for widget functionality.
Runs both old widget and custom widget tests and provides a summary report.
"""

import subprocess
import sys
import time
from pathlib import Path

def run_test(test_name, test_file):
    """Run a single test and return the result"""
    print(f"\n{'='*60}")
    print(f"🧪 Running {test_name}")
    print(f"{'='*60}")
    
    try:
        # Run the test
        result = subprocess.run(
            [sys.executable, test_file],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        
        # Print output
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
            
        return result.returncode == 0, result.stdout
        
    except Exception as e:
        print(f"❌ Error running {test_name}: {e}")
        return False, str(e)

def main():
    """Main function to run all widget tests"""
    print("🚀 Starting Comprehensive Widget Functionality Tests")
    print("=" * 60)
    
    # Define tests
    tests = [
        ("Old Widget Functionality", "tests/test_old_widget_functionality.py"),
        ("Custom Widget Functionality", "tests/test_custom_widget_functionality.py")
    ]
    
    results = []
    total_tests = len(tests)
    passed_tests = 0
    
    # Run each test
    for test_name, test_file in tests:
        print(f"\n⏳ Starting {test_name}...")
        success, output = run_test(test_name, test_file)
        results.append({
            "name": test_name,
            "success": success,
            "output": output
        })
        
        if success:
            passed_tests += 1
            print(f"✅ {test_name} PASSED")
        else:
            print(f"❌ {test_name} FAILED")
            
        # Small delay between tests
        time.sleep(1)
    
    # Print comprehensive summary
    print(f"\n{'='*60}")
    print("📊 COMPREHENSIVE TEST SUMMARY")
    print(f"{'='*60}")
    
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Success Rate: {(passed_tests / total_tests) * 100:.1f}%")
    
    print(f"\n{'='*60}")
    print("📋 DETAILED RESULTS")
    print(f"{'='*60}")
    
    for result in results:
        status = "✅ PASSED" if result["success"] else "❌ FAILED"
        print(f"{status} - {result['name']}")
        
        # Extract key information from output
        if "Success Rate:" in result["output"]:
            lines = result["output"].split('\n')
            for line in lines:
                if "Success Rate:" in line:
                    print(f"   {line.strip()}")
                    break
    
    print(f"\n{'='*60}")
    if passed_tests == total_tests:
        print("🎉 ALL TESTS PASSED!")
        print("✅ Old widget functionality is working correctly")
        print("✅ Custom widget functionality is working correctly")
        print("✅ Persona sliders feature is fully operational")
        print("✅ No breaking changes to existing functionality")
        sys.exit(0)
    else:
        print("⚠️  SOME TESTS FAILED")
        print("Please check the implementation and fix any issues")
        sys.exit(1)

if __name__ == "__main__":
    main()
