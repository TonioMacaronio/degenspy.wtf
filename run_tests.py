#!/usr/bin/env python3
"""
Test runner for Solana Token Holder Analyzer
"""

import subprocess
import sys
import os


def run_tests():
    """Run the test suite"""
    print("🧪 Running Solana Token Holder Analyzer Test Suite")
    print("=" * 60)
    
    # Check if dependencies are installed
    try:
        import pytest
        print("✅ pytest found")
    except ImportError:
        print("❌ pytest not found. Please install with: pip install pytest pytest-asyncio pytest-mock")
        return False
    
    try:
        import solana
        print("✅ solana-py found")
    except ImportError:
        print("❌ solana-py not found. Please install with: pip install -r requirements.txt")
        return False
    
    # Run tests
    print("\n🚀 Starting tests...")
    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "tests/", 
            "-v", 
            "--tb=short",
            "--color=yes"
        ], check=False)
        
        if result.returncode == 0:
            print("\n✅ All tests passed!")
            return True
        else:
            print(f"\n❌ Some tests failed (exit code: {result.returncode})")
            return False
            
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return False


def run_specific_test(test_name):
    """Run a specific test"""
    print(f"🧪 Running specific test: {test_name}")
    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            f"tests/test_token_analyzer.py::{test_name}",
            "-v", 
            "--tb=short",
            "--color=yes"
        ], check=False)
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Error running test: {e}")
        return False


def show_coverage():
    """Show test coverage"""
    print("📊 Generating test coverage report...")
    try:
        # Install coverage if not available
        subprocess.run([sys.executable, "-m", "pip", "install", "coverage"], check=False)
        
        # Run tests with coverage
        subprocess.run([
            sys.executable, "-m", "coverage", "run", 
            "-m", "pytest", "tests/"
        ], check=False)
        
        # Show coverage report
        subprocess.run([sys.executable, "-m", "coverage", "report"], check=False)
        subprocess.run([sys.executable, "-m", "coverage", "html"], check=False)
        
        print("\n📈 Coverage report generated in htmlcov/index.html")
        
    except Exception as e:
        print(f"❌ Error generating coverage: {e}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "--coverage":
            show_coverage()
        elif sys.argv[1] == "--test":
            if len(sys.argv) > 2:
                run_specific_test(sys.argv[2])
            else:
                print("❌ Please specify test name: python run_tests.py --test TestClassName::test_method")
        else:
            print("Usage:")
            print("  python run_tests.py                    # Run all tests")
            print("  python run_tests.py --coverage         # Run with coverage")
            print("  python run_tests.py --test TestName    # Run specific test")
    else:
        run_tests() 