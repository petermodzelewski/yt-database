#!/usr/bin/env python3
"""
Command-line entry point for the YouTube to Notion Database Integration.
This script provides argument parsing for YouTube URL processing and example data mode.
"""

import argparse
import sys
from src.youtube_notion.main import main

def parse_arguments():
    """Parse command-line arguments for the YouTube to Notion integration."""
    parser = argparse.ArgumentParser(
        description="YouTube to Notion Database Integration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --example-data                    # Use example data (default)
  %(prog)s --url "https://youtube.com/watch?v=abc123"  # Process single YouTube video
  %(prog)s --urls "https://youtu.be/abc123,https://youtu.be/def456"  # Process multiple URLs
  %(prog)s --file urls.txt                   # Process URLs from file (one per line)
  %(prog)s --url "https://youtu.be/abc123" --prompt "Custom summary prompt"
        """
    )
    
    # Create mutually exclusive group for input modes
    input_group = parser.add_mutually_exclusive_group()
    
    input_group.add_argument(
        "--url",
        type=str,
        help="Single YouTube URL to process"
    )
    
    input_group.add_argument(
        "--urls",
        type=str,
        help="Comma-separated list of YouTube URLs to process"
    )
    
    input_group.add_argument(
        "--file",
        type=str,
        help="File containing YouTube URLs (one per line, empty lines ignored)"
    )
    
    input_group.add_argument(
        "--example-data",
        action="store_true",
        help="Use example data mode (default behavior)"
    )
    
    parser.add_argument(
        "--prompt",
        type=str,
        help="Custom prompt for AI summary generation (only used with --url)"
    )
    
    return parser.parse_args()

def parse_urls_from_file(file_path):
    """Parse YouTube URLs from a file, ignoring empty lines."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            urls = []
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if line:  # Ignore empty lines
                    urls.append(line)
            return urls
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error reading file '{file_path}': {e}", file=sys.stderr)
        sys.exit(1)

def main_cli():
    """Main CLI function that handles argument parsing and delegates to appropriate mode."""
    args = parse_arguments()
    
    # Validate arguments
    if args.prompt and not args.url:
        print("Error: --prompt can only be used with single --url", file=sys.stderr)
        sys.exit(1)
    
    # Determine execution mode and collect URLs
    urls = []
    
    if args.url:
        # Single YouTube URL processing mode
        urls = [args.url]
    elif args.urls:
        # Multiple URLs from comma-separated string
        urls = [url.strip() for url in args.urls.split(',') if url.strip()]
        if not urls:
            print("Error: No valid URLs found in comma-separated list", file=sys.stderr)
            sys.exit(1)
    elif args.file:
        # URLs from file
        urls = parse_urls_from_file(args.file)
        if not urls:
            print("Error: No URLs found in file", file=sys.stderr)
            sys.exit(1)
    else:
        # Example data mode (default or explicitly requested)
        main()
        return
    
    # Process URLs
    if len(urls) == 1:
        # Single URL - use existing main function
        main(youtube_url=urls[0], custom_prompt=args.prompt)
    else:
        # Multiple URLs - process each one
        print(f"Processing {len(urls)} YouTube URLs...")
        print("=" * 60)
        
        success_count = 0
        failed_urls = []
        
        for i, url in enumerate(urls, 1):
            print(f"\n[{i}/{len(urls)}] Processing: {url}")
            print("-" * 40)
            
            try:
                success = main(youtube_url=url, custom_prompt=None, batch_mode=True)
                if success:
                    success_count += 1
                else:
                    failed_urls.append(url)
            except Exception as e:
                print(f"✗ Error processing {url}: {e}")
                failed_urls.append(url)
        
        # Summary
        print("\n" + "=" * 60)
        print("BATCH PROCESSING SUMMARY")
        print("=" * 60)
        print(f"Total URLs processed: {len(urls)}")
        print(f"Successful: {success_count}")
        print(f"Failed: {len(failed_urls)}")
        
        if failed_urls:
            print("\nFailed URLs:")
            for url in failed_urls:
                print(f"  - {url}")
            sys.exit(1)
        else:
            print("\n✓ All URLs processed successfully!")
            sys.exit(0)

if __name__ == "__main__":
    main_cli()