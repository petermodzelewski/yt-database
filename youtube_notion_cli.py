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
  %(prog)s --url "https://youtube.com/watch?v=abc123"  # Process YouTube video
  %(prog)s --url "https://youtu.be/abc123" --prompt "Custom summary prompt"
        """
    )
    
    # Create mutually exclusive group for input modes
    input_group = parser.add_mutually_exclusive_group()
    
    input_group.add_argument(
        "--url",
        type=str,
        help="YouTube URL to process"
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

def main_cli():
    """Main CLI function that handles argument parsing and delegates to appropriate mode."""
    args = parse_arguments()
    
    # Validate arguments
    if args.prompt and not args.url:
        print("Error: --prompt can only be used with --url", file=sys.stderr)
        sys.exit(1)
    
    # Determine execution mode
    if args.url:
        # YouTube URL processing mode
        main(youtube_url=args.url, custom_prompt=args.prompt)
    else:
        # Example data mode (default or explicitly requested)
        main()

if __name__ == "__main__":
    main_cli()