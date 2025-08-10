#!/usr/bin/env python3
"""
Command-line entry point for the YouTube to Notion Database Integration.
This script provides argument parsing for YouTube URL processing and example data mode.
"""

import argparse
import sys
import webbrowser
import time
from src.youtube_notion.main import main, main_ui, main_batch

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
  %(prog)s --ui                              # Start web UI mode for visual queue management
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
    
    input_group.add_argument(
        "--ui",
        action="store_true",
        help="Start web UI mode for visual queue management"
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
    
    # Check for UI mode first
    if args.ui:
        # UI mode - start web server and open browser
        print("Starting YouTube-to-Notion Web UI...")
        try:
            success = main_ui()
            sys.exit(0 if success else 1)
        except KeyboardInterrupt:
            print("\nShutting down web UI...")
            sys.exit(0)
        except Exception as e:
            print(f"Error starting web UI: {e}", file=sys.stderr)
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
        # Multiple URLs - use QueueManager for batch processing
        success = main_batch(urls)
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    main_cli()