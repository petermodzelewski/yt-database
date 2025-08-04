#!/usr/bin/env python3
"""
Integration test runner for YouTube-to-Notion integration.

This script runs integration tests that require real API keys and test databases.
It ensures proper environment setup and provides clear feedback about test results.

Usage:
    python run_integration_tests.py              # Run all integration tests
    python run_integration_tests.py --fast       # Skip slow tests
    python run_integration_tests.py --verbose    # Verbose output
"""

import sys
import os
import subprocess
import argparse
from pathlib import Path

# Add src to Python path for package imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / 'src'))


def check_test_environment():
    """Check that the test environment is properly configured."""
    env_test_path = project_root / '.env-test'
    
    if not env_test_path.exists():
        print("❌ ERROR: .env-test file not found")
        print("Integration tests require a separate test configuration file.")
        print("Please create .env-test with your test API keys and database settings.")
        return False
    
    # Load test environment to check configuration
    try:
        from dotenv import load_dotenv
        load_dotenv(env_test_path)
        
        required_vars = ['NOTION_TOKEN', 'GEMINI_API_KEY']
        missing_vars = []
        
        for var in required_vars:
            if not os.getenv(var) or os.getenv(var).startswith('your_'):
                missing_vars.append(var)
        
        if missing_vars:
            print("❌ ERROR: Missing or placeholder values in .env-test:")
            for var in missing_vars:
                print(f"  - {var}")
            print("\nPlease update .env-test with real API keys for integration testing.")
            return False
        
        # Check test mode indicator
        if os.getenv('TEST_MODE', '').lower() != 'true':
            print("❌ ERROR: TEST_MODE not set to 'true' in .env-test")
            print("This ensures integration tests use test configuration only.")
            return False
        
        print("✅ Test environment configuration looks good")
        return True
        
    except ImportError:
        print("❌ ERROR: python-dotenv not installed")
        print("Please install with: pip install python-dotenv")
        return False
    except Exception as e:
        print(f"❌ ERROR: Failed to validate test environment: {e}")
        return False


def run_integration_tests(args):
    """Run the integration tests with appropriate pytest arguments."""
    
    # Base pytest command
    cmd = [
        sys.executable, '-m', 'pytest',
        'tests/integration/',
        '-m', 'integration',
        '--tb=short'
    ]
    
    # Add optional arguments
    if args.verbose:
        cmd.append('-v')
    else:
        cmd.append('-q')
    
    if args.fast:
        cmd.extend(['-m', 'not slow'])
    
    if args.stop_on_first_failure:
        cmd.append('-x')
    
    if args.capture == 'no':
        cmd.append('-s')
    
    # Set environment variable to ensure test mode
    env = os.environ.copy()
    env['TEST_MODE'] = 'true'
    
    print("🧪 Running integration tests...")
    print(f"Command: {' '.join(cmd)}")
    print("-" * 60)
    
    try:
        result = subprocess.run(cmd, env=env, cwd=project_root)
        return result.returncode
    except KeyboardInterrupt:
        print("\n❌ Tests interrupted by user")
        return 1
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return 1


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Run integration tests for YouTube-to-Notion integration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_integration_tests.py                    # Run all integration tests
  python run_integration_tests.py --fast             # Skip slow tests
  python run_integration_tests.py --verbose          # Verbose output
  python run_integration_tests.py -x                 # Stop on first failure
  python run_integration_tests.py --capture=no       # Show print statements
        """
    )
    
    parser.add_argument(
        '--fast',
        action='store_true',
        help='Skip slow tests (marked with @pytest.mark.slow)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Verbose test output'
    )
    
    parser.add_argument(
        '--stop-on-first-failure', '-x',
        action='store_true',
        help='Stop on first test failure'
    )
    
    parser.add_argument(
        '--capture',
        choices=['yes', 'no'],
        default='yes',
        help='Capture stdout/stderr (default: yes)'
    )
    
    args = parser.parse_args()
    
    print("🔧 YouTube-to-Notion Integration Test Runner")
    print("=" * 50)
    
    # Check test environment
    if not check_test_environment():
        return 1
    
    # Run tests
    return_code = run_integration_tests(args)
    
    # Print summary
    print("-" * 60)
    if return_code == 0:
        print("✅ All integration tests passed!")
    else:
        print("❌ Some integration tests failed")
        print("\nTroubleshooting tips:")
        print("1. Check that your .env-test file has valid API keys")
        print("2. Ensure test Notion database exists and is accessible")
        print("3. Verify network connectivity to APIs")
        print("4. Check API quotas and rate limits")
    
    return return_code


if __name__ == '__main__':
    sys.exit(main())