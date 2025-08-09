#!/usr/bin/env python3
"""
Comprehensive test runner for both Python and JavaScript tests.

This script runs all unit tests (Python and JavaScript) and provides
a summary of test results. It's designed to be fast and efficient
for development workflow.

Usage:
    python run_all_tests.py
    python run_all_tests.py --verbose
    python run_all_tests.py --python-only
    python run_all_tests.py --js-only
"""

import sys
import os
import subprocess
import argparse
import time
from pathlib import Path

# Add src to Python path
project_root = Path(__file__).parent
src_path = project_root / 'src'

# Set PYTHONPATH environment variable
env = os.environ.copy()
current_path = env.get('PYTHONPATH', '')
new_paths = [str(src_path)]
if current_path:
    new_paths.append(current_path)
env['PYTHONPATH'] = os.pathsep.join(new_paths)


def run_python_tests(verbose=False):
    """Run Python unit tests using pytest."""
    print("🐍 Running Python unit tests...")
    start_time = time.time()
    
    try:
        cmd = [sys.executable, '-m', 'pytest', 'tests/unit/', '-v' if verbose else '-q']
        result = subprocess.run(cmd, env=env, capture_output=not verbose, text=True)
        
        duration = time.time() - start_time
        
        if result.returncode == 0:
            print(f"✅ Python tests passed ({duration:.1f}s)")
            if not verbose and result.stdout:
                # Extract test count from output
                lines = result.stdout.strip().split('\n')
                summary_line = next((line for line in lines if 'passed' in line and 'in' in line), '')
                if summary_line:
                    print(f"   {summary_line}")
            return True
        else:
            print(f"❌ Python tests failed ({duration:.1f}s)")
            if not verbose:
                print("   Run with --verbose for detailed output")
            else:
                print(result.stdout)
                print(result.stderr)
            return False
            
    except FileNotFoundError:
        print("❌ pytest not available. Please install: pip install pytest")
        return False
    except Exception as e:
        print(f"❌ Error running Python tests: {e}")
        return False


def run_javascript_tests(verbose=False):
    """Run JavaScript unit tests using Jest."""
    print("🟨 Running JavaScript unit tests...")
    start_time = time.time()
    
    web_static_dir = project_root / 'web' / 'static'
    
    if not (web_static_dir / 'package.json').exists():
        print("❌ No package.json found in web/static directory")
        return False
    
    try:
        # Check if node_modules exists
        if not (web_static_dir / 'node_modules').exists():
            print("📦 Installing JavaScript dependencies...")
            npm_install = subprocess.run(
                ['npm', 'install'], 
                cwd=web_static_dir, 
                capture_output=True, 
                text=True
            )
            if npm_install.returncode != 0:
                print("❌ Failed to install JavaScript dependencies")
                print(npm_install.stderr)
                return False
        
        # Run Jest tests
        cmd = ['npm', 'test', '--', '--passWithNoTests']
        if not verbose:
            cmd.extend(['--silent'])
        
        result = subprocess.run(
            cmd, 
            cwd=web_static_dir, 
            capture_output=not verbose, 
            text=True
        )
        
        duration = time.time() - start_time
        
        if result.returncode == 0:
            print(f"✅ JavaScript tests passed ({duration:.1f}s)")
            if not verbose and result.stdout:
                # Extract test summary
                lines = result.stdout.strip().split('\n')
                summary_lines = [line for line in lines if 'Tests:' in line or 'Test Suites:' in line]
                for line in summary_lines:
                    print(f"   {line.strip()}")
            return True
        else:
            print(f"❌ JavaScript tests failed ({duration:.1f}s)")
            if not verbose:
                print("   Run with --verbose for detailed output")
            else:
                print(result.stdout)
                print(result.stderr)
            return False
            
    except FileNotFoundError:
        print("❌ npm not available. Please install Node.js and npm")
        return False
    except Exception as e:
        print(f"❌ Error running JavaScript tests: {e}")
        return False


def run_integration_tests(verbose=False):
    """Run integration tests (optional, slower)."""
    print("🔗 Running integration tests...")
    start_time = time.time()
    
    try:
        cmd = [sys.executable, '-m', 'pytest', 'tests/integration/', '-v' if verbose else '-q']
        result = subprocess.run(cmd, env=env, capture_output=not verbose, text=True)
        
        duration = time.time() - start_time
        
        if result.returncode == 0:
            print(f"✅ Integration tests passed ({duration:.1f}s)")
            if not verbose and result.stdout:
                lines = result.stdout.strip().split('\n')
                summary_line = next((line for line in lines if 'passed' in line and 'in' in line), '')
                if summary_line:
                    print(f"   {summary_line}")
            return True
        else:
            print(f"❌ Integration tests failed ({duration:.1f}s)")
            if not verbose:
                print("   Run with --verbose for detailed output")
            return False
            
    except Exception as e:
        print(f"❌ Error running integration tests: {e}")
        return False


def print_summary(python_passed, js_passed, integration_passed=None, total_time=0):
    """Print test summary."""
    print("\n" + "="*50)
    print("📊 TEST SUMMARY")
    print("="*50)
    
    total_tests = 2 if integration_passed is None else 3
    passed_tests = sum([python_passed, js_passed] + ([integration_passed] if integration_passed is not None else []))
    
    print(f"🐍 Python Unit Tests:    {'✅ PASSED' if python_passed else '❌ FAILED'}")
    print(f"🟨 JavaScript Unit Tests: {'✅ PASSED' if js_passed else '❌ FAILED'}")
    if integration_passed is not None:
        print(f"🔗 Integration Tests:     {'✅ PASSED' if integration_passed else '❌ FAILED'}")
    
    print(f"\n📈 Overall: {passed_tests}/{total_tests} test suites passed")
    print(f"⏱️  Total time: {total_time:.1f}s")
    
    if passed_tests == total_tests:
        print("🎉 All tests passed!")
        return True
    else:
        print("💥 Some tests failed!")
        return False


def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(description='Run comprehensive test suite')
    parser.add_argument('--verbose', '-v', action='store_true', 
                       help='Show detailed test output')
    parser.add_argument('--python-only', action='store_true',
                       help='Run only Python tests')
    parser.add_argument('--js-only', action='store_true',
                       help='Run only JavaScript tests')
    parser.add_argument('--integration', action='store_true',
                       help='Also run integration tests (slower)')
    parser.add_argument('--fast', action='store_true',
                       help='Skip integration tests for faster execution')
    
    args = parser.parse_args()
    
    if args.python_only and args.js_only:
        print("❌ Cannot specify both --python-only and --js-only")
        return 1
    
    start_time = time.time()
    
    print("🚀 Starting comprehensive test suite...")
    print(f"📁 Project root: {project_root}")
    print()
    
    python_passed = True
    js_passed = True
    integration_passed = None
    
    # Run Python tests
    if not args.js_only:
        python_passed = run_python_tests(args.verbose)
        print()
    
    # Run JavaScript tests
    if not args.python_only:
        js_passed = run_javascript_tests(args.verbose)
        print()
    
    # Run integration tests if requested
    if args.integration and not args.fast:
        integration_passed = run_integration_tests(args.verbose)
        print()
    
    total_time = time.time() - start_time
    
    # Print summary
    all_passed = print_summary(
        python_passed if not args.js_only else True,
        js_passed if not args.python_only else True,
        integration_passed,
        total_time
    )
    
    return 0 if all_passed else 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)