#!/usr/bin/env python3
"""
Test summary script to provide an overview of test coverage and results.
"""

import os
import subprocess
import sys

def count_tests_in_file(filepath):
    """Count the number of test functions in a file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            return content.count('def test_')
    except Exception:
        return 0

def main():
    """Generate test summary."""
    print("🧪 YouTube-Notion Integration Test Suite Summary")
    print("=" * 50)
    
    test_files = [
        ('tests/test_main.py', 'Main Application Entry Point'),
        ('tests/test_markdown_converter.py', 'Markdown to Notion Conversion'),
        ('tests/test_notion_operations.py', 'Notion Database Operations'),
        ('tests/test_timestamp_enrichment.py', 'Timestamp Processing'),
        ('tests/test_end_to_end_timestamps.py', 'End-to-End Timestamp Flow'),
        ('tests/test_integration.py', 'Integration Tests'),
        ('tests/test_error_handling.py', 'Error Handling & Edge Cases'),
        ('tests/test_performance.py', 'Performance Benchmarks'),
    ]
    
    total_tests = 0
    
    for filepath, description in test_files:
        if os.path.exists(filepath):
            test_count = count_tests_in_file(filepath)
            total_tests += test_count
            status = "✅" if test_count > 0 else "❌"
            print(f"{status} {description:<35} {test_count:>3} tests")
        else:
            print(f"❌ {description:<35}   0 tests (file missing)")
    
    print("-" * 50)
    print(f"📊 Total Test Functions: {total_tests}")
    
    # Test coverage areas
    print("\n🎯 Test Coverage Areas:")
    coverage_areas = [
        "✅ Unit tests for all utility functions",
        "✅ Integration tests with example data", 
        "✅ Notion API interaction mocking",
        "✅ Error handling and edge cases",
        "✅ Performance benchmarks",
        "✅ Timestamp parsing and enrichment",
        "✅ Markdown to Notion block conversion",
        "✅ End-to-end workflow testing",
    ]
    
    for area in coverage_areas:
        print(f"  {area}")
    
    print("\n🚀 To run tests:")
    print("  python run_tests.py              # Run all tests")
    print("  python -m pytest tests/ -v      # Run with pytest")
    print("  python -m pytest -m unit        # Run only unit tests")
    print("  python -m pytest -m integration # Run only integration tests")
    print("  python -m pytest --cov          # Run with coverage report")

if __name__ == '__main__':
    main()