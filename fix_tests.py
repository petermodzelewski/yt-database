#!/usr/bin/env python3
"""
Script to fix YouTubeProcessor constructor calls in test files.
Updates from old individual parameter style to new from_api_keys class method.
"""

import os
import re
import glob

def fix_youtube_processor_calls(content):
    """Fix YouTubeProcessor constructor calls in the given content."""
    
    # Pattern 1: Simple constructor with just gemini_api_key
    pattern1 = r'YouTubeProcessor\(gemini_api_key="([^"]+)"\)'
    replacement1 = r'YouTubeProcessor.from_api_keys(gemini_api_key="\1")'
    content = re.sub(pattern1, replacement1, content)
    
    # Pattern 2: Constructor with gemini_api_key and youtube_api_key
    pattern2 = r'YouTubeProcessor\(\s*gemini_api_key="([^"]+)",\s*youtube_api_key="([^"]+)"\s*\)'
    replacement2 = r'YouTubeProcessor.from_api_keys(gemini_api_key="\1", youtube_api_key="\2")'
    content = re.sub(pattern2, replacement2, content)
    
    # Pattern 3: Constructor with additional parameters (max_retries, etc.)
    pattern3 = r'YouTubeProcessor\(\s*gemini_api_key="([^"]+)",\s*max_retries=(\d+)\s*\)'
    replacement3 = r'YouTubeProcessor.from_api_keys(gemini_api_key="\1", max_retries=\2)'
    content = re.sub(pattern3, replacement3, content)
    
    # Pattern 4: Multi-line constructor calls - simple case
    pattern4 = r'YouTubeProcessor\(\s*\n\s*gemini_api_key="([^"]+)"\s*\n\s*\)'
    replacement4 = r'YouTubeProcessor.from_api_keys(\n            gemini_api_key="\1"\n        )'
    content = re.sub(pattern4, replacement4, content, flags=re.MULTILINE | re.DOTALL)
    
    # Pattern 5: Multi-line constructor calls - with youtube_api_key
    pattern5 = r'YouTubeProcessor\(\s*\n\s*gemini_api_key="([^"]+)",\s*\n\s*youtube_api_key="([^"]+)"\s*\n\s*\)'
    replacement5 = r'YouTubeProcessor.from_api_keys(\n            gemini_api_key="\1",\n            youtube_api_key="\2"\n        )'
    content = re.sub(pattern5, replacement5, content, flags=re.MULTILINE | re.DOTALL)
    
    # Pattern 6: Multi-line constructor calls - complex with multiple params
    pattern6 = r'YouTubeProcessor\(\s*\n\s*gemini_api_key="([^"]+)",\s*\n\s*youtube_api_key="([^"]+)",\s*\n\s*default_prompt="([^"]*)",\s*\n\s*max_retries=(\d+),\s*\n\s*timeout_seconds=(\d+)\s*\n\s*\)'
    replacement6 = r'YouTubeProcessor.from_api_keys(\n            gemini_api_key="\1",\n            youtube_api_key="\2",\n            default_prompt="\3",\n            max_retries=\4,\n            timeout_seconds=\5\n        )'
    content = re.sub(pattern6, replacement6, content, flags=re.MULTILINE | re.DOTALL)
    
    # Pattern 7: Constructor with None values
    pattern7 = r'YouTubeProcessor\(gemini_api_key=None\)'
    replacement7 = r'YouTubeProcessor.from_api_keys(gemini_api_key=None)'
    content = re.sub(pattern7, replacement7, content)
    
    # Pattern 8: Constructor with empty string
    pattern8 = r'YouTubeProcessor\(gemini_api_key=""\)'
    replacement8 = r'YouTubeProcessor.from_api_keys(gemini_api_key="")'
    content = re.sub(pattern8, replacement8, content)
    
    return content

def main():
    """Main function to fix all test files."""
    test_files = glob.glob("tests/test_*.py")
    
    for file_path in test_files:
        print(f"Processing {file_path}...")
        
        # Read the file
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Fix the constructor calls
        original_content = content
        content = fix_youtube_processor_calls(content)
        
        # Write back if changed
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"  ✓ Updated {file_path}")
        else:
            print(f"  - No changes needed for {file_path}")

if __name__ == "__main__":
    main()