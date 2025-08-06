"""
Markdown to Notion converter utilities.
Converts markdown text to Notion's rich text block format.
"""

import re
from urllib.parse import urlparse, parse_qs


def parse_rich_text(text):
    """Parse text with markdown formatting to Notion rich text format.
    
    Supports:
    - Links: [text](url)
    - Bold: **text** (can contain links)
    - Italic: *text* (can contain links)
    - Strikethrough: ~~text~~ (can contain links)
    - Inline code: `code`
    """
    rich_text = []
    i = 0
    
    while i < len(text):
        # The order of matching is important:
        # 1. Links: [text](url) - Can contain other formatting.
        # 2. Strikethrough: ~~text~~
        # 3. Bold: **text**
        # 4. Italic: *text*
        # 5. Inline code: `code`

        # Look for markdown link pattern [text](url)
        link_match = re.match(r'\[([^\]]+)\]\(([^)]+)\)', text[i:])
        if link_match:
            link_text = link_match.group(1)
            link_url = link_match.group(2)
            
            # Check if link text has formatting
            if '**' in link_text and link_text.startswith('**') and link_text.endswith('**'):
                # Bold link
                rich_text.append({
                    "type": "text",
                    "text": {"content": link_text[2:-2], "link": {"url": link_url}},
                    "annotations": {"bold": True}
                })
            elif '*' in link_text and link_text.startswith('*') and link_text.endswith('*'):
                # Italic link
                rich_text.append({
                    "type": "text",
                    "text": {"content": link_text[1:-1], "link": {"url": link_url}},
                    "annotations": {"italic": True}
                })
            elif '~~' in link_text and link_text.startswith('~~') and link_text.endswith('~~'):
                # Strikethrough link
                rich_text.append({
                    "type": "text",
                    "text": {"content": link_text[2:-2], "link": {"url": link_url}},
                    "annotations": {"strikethrough": True}
                })
            else:
                # Regular link
                rich_text.append({
                    "type": "text",
                    "text": {"content": link_text, "link": {"url": link_url}}
                })
            
            i += link_match.end()
            continue
        
        # Look for strikethrough text ~~text~~ (may contain links)
        strikethrough_match = re.match(r'~~([^~]+)~~', text[i:])
        if strikethrough_match:
            strikethrough_content = strikethrough_match.group(1)

            # Check if strikethrough content contains links
            if '[' in strikethrough_content and '](' in strikethrough_content:
                # Parse the content recursively for links
                strikethrough_rich_text = parse_rich_text(strikethrough_content)
                # Apply strikethrough formatting to all parts
                for part in strikethrough_rich_text:
                    if 'annotations' not in part:
                        part['annotations'] = {}
                    part['annotations']['strikethrough'] = True
                    rich_text.append(part)
            else:
                # Simple strikethrough text
                rich_text.append({
                    "type": "text",
                    "text": {"content": strikethrough_content},
                    "annotations": {"strikethrough": True}
                })

            i += strikethrough_match.end()
            continue

        # Look for bold text **text** (may contain links)
        bold_match = re.match(r'\*\*([^*]+)\*\*', text[i:])
        if bold_match:
            bold_content = bold_match.group(1)
            
            # Check if bold content contains links
            if '[' in bold_content and '](' in bold_content:
                # Parse the bold content recursively for links
                bold_rich_text = parse_rich_text(bold_content)
                # Apply bold formatting to all parts
                for part in bold_rich_text:
                    if 'annotations' not in part:
                        part['annotations'] = {}
                    part['annotations']['bold'] = True
                    rich_text.append(part)
            else:
                # Simple bold text without links
                rich_text.append({
                    "type": "text",
                    "text": {"content": bold_content},
                    "annotations": {"bold": True}
                })
            
            i += bold_match.end()
            continue
        
        # Look for italic text *text* (may contain links)
        italic_match = re.match(r'\*([^*]+)\*', text[i:])
        if italic_match:
            italic_content = italic_match.group(1)
            
            # Check if italic content contains links
            if '[' in italic_content and '](' in italic_content:
                # Parse the italic content recursively for links
                italic_rich_text = parse_rich_text(italic_content)
                # Apply italic formatting to all parts
                for part in italic_rich_text:
                    if 'annotations' not in part:
                        part['annotations'] = {}
                    part['annotations']['italic'] = True
                    rich_text.append(part)
            else:
                # Simple italic text without links
                rich_text.append({
                    "type": "text",
                    "text": {"content": italic_content},
                    "annotations": {"italic": True}
                })
            
            i += italic_match.end()
            continue
        
        # Look for inline code `code` (no links inside)
        code_match = re.match(r'`([^`]+)`', text[i:])
        if code_match:
            code_content = code_match.group(1)
            rich_text.append({
                "type": "text",
                "text": {"content": code_content},
                "annotations": {"code": True}
            })
            i += code_match.end()
            continue

        # Regular character - find the next special character or end of string
        next_special = len(text)
        for pattern in [r'\[', r'~~', r'\*\*', r'\*', r'`']:
            match = re.search(pattern, text[i:])
            if match:
                next_special = min(next_special, i + match.start())
        
        if next_special > i:
            # Add regular text
            regular_text = text[i:next_special]
            if regular_text:
                rich_text.append({
                    "type": "text",
                    "text": {"content": regular_text}
                })
            i = next_special
        else:
            # Single character that didn't match any pattern
            rich_text.append({
                "type": "text",
                "text": {"content": text[i]}
            })
            i += 1
    
    return rich_text


def markdown_to_notion_blocks(markdown_text):
    """Convert markdown text to Notion rich text blocks."""
    blocks = []
    lines = markdown_text.split('\n')
    i = 0
    
    while i < len(lines):
        line = lines[i] # Keep leading whitespace for code blocks
        
        stripped_line = line.strip()

        if not stripped_line:
            i += 1
            continue

        # Handle code blocks
        if stripped_line.startswith('```'):
            # Find the end of the code block
            end_index = -1
            for j in range(i + 1, len(lines)):
                if lines[j].strip() == '```':
                    end_index = j
                    break
            
            if end_index != -1:
                # Extract code content
                code_content = '\n'.join(lines[i+1:end_index])
                # Extract language from the starting fence
                language = stripped_line[3:].strip() or "plain text"

                blocks.append({
                    "object": "block",
                    "type": "code",
                    "code": {
                        "caption": [],
                        "language": language,
                        "rich_text": [{
                            "type": "text",
                            "text": {
                                "content": code_content
                            }
                        }]
                    }
                })
                i = end_index + 1
                continue

        # Handle headers (Notion supports only H1, H2, H3)
        if stripped_line.startswith('#'):
            # Count the number of # symbols
            header_level = 0
            for char in stripped_line:
                if char == '#':
                    header_level += 1
                else:
                    break
            
            header_text = stripped_line[header_level:].strip()
            
            if header_level == 1:
                blocks.append({
                    "object": "block",
                    "type": "heading_1",
                    "heading_1": { "rich_text": parse_rich_text(header_text) }
                })
            elif header_level == 2:
                blocks.append({
                    "object": "block",
                    "type": "heading_2", 
                    "heading_2": { "rich_text": parse_rich_text(header_text) }
                })
            elif header_level >= 3:
                # H3 and beyond all become H3 in Notion
                blocks.append({
                    "object": "block",
                    "type": "heading_3",
                    "heading_3": { "rich_text": parse_rich_text(header_text) }
                })
        # Handle blockquotes
        elif stripped_line.startswith('> '):
            quote_text = stripped_line[2:]
            blocks.append({
                "object": "block",
                "type": "quote",
                "quote": {
                    "rich_text": parse_rich_text(quote_text)
                }
            })
        # Handle bullet points
        elif stripped_line.startswith('* ') or stripped_line.startswith('- ') or stripped_line.startswith('*   '):
            if stripped_line.startswith('*   '):
                bullet_text = stripped_line[4:]
            else:
                bullet_text = stripped_line[2:]
            blocks.append({
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": { "rich_text": parse_rich_text(bullet_text) }
            })
        # Handle numbered lists
        elif re.match(r'^\d+\.', stripped_line):
            numbered_text = re.sub(r'^\d+\.\s*', '', stripped_line)
            blocks.append({
                "object": "block",
                "type": "numbered_list_item", 
                "numbered_list_item": { "rich_text": parse_rich_text(numbered_text) }
            })
        # Handle tables
        elif stripped_line.startswith('|') and i + 1 < len(lines) and re.match(r'[|:\-\s]+', lines[i+1].strip()):
            table_lines = [stripped_line]
            j = i + 1
            while j < len(lines) and lines[j].strip().startswith('|'):
                table_lines.append(lines[j].strip())
                j += 1

            table_block = _parse_table_block(table_lines)
            if table_block:
                blocks.append(table_block)

            i = j
            continue

        # Handle regular paragraphs
        else:
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": parse_rich_text(stripped_line)
                }
            })
        
        i += 1
    
    return blocks


def _parse_table_block(table_lines):
    """Parse a list of markdown table lines into a Notion table block."""
    header_line = table_lines[0]
    separator_line = table_lines[1]
    row_lines = table_lines[2:]

    # Extract header cells
    header_cells = [cell.strip() for cell in header_line.split('|') if cell.strip()]
    num_columns = len(header_cells)

    # Validate separator line
    separator_cells = [cell.strip() for cell in separator_line.split('|') if cell.strip()]
    if len(separator_cells) != num_columns or not all(re.match(r':?--+:?', cell) for cell in separator_cells):
        return None

    # Create table block
    table_block = {
        "object": "block",
        "type": "table",
        "table": {
            "table_width": num_columns,
            "has_column_header": True,
            "has_row_header": False,
            "children": []
        }
    }

    # Add header row
    header_row = {
        "type": "table_row",
        "table_row": {
            "cells": [parse_rich_text(cell) for cell in header_cells]
        }
    }
    table_block["table"]["children"].append(header_row)

    # Add data rows
    for row_line in row_lines:
        row_cells = [cell.strip() for cell in row_line.split('|') if cell.strip()]
        if len(row_cells) != num_columns:
            continue

        row = {
            "type": "table_row",
            "table_row": {
                "cells": [parse_rich_text(cell) for cell in row_cells]
            }
        }
        table_block["table"]["children"].append(row)

    return table_block


def parse_timestamp_to_seconds(timestamp):
    """Convert timestamp string like '8:05' or '1:23:45' to seconds."""
    parts = timestamp.split(':')
    if len(parts) == 2:  # MM:SS
        minutes, seconds = map(int, parts)
        if seconds >= 60:
            raise ValueError(f"Invalid seconds value: {seconds} (must be < 60)")
        return minutes * 60 + seconds
    elif len(parts) == 3:  # HH:MM:SS
        hours, minutes, seconds = map(int, parts)
        if minutes >= 60:
            raise ValueError(f"Invalid minutes value: {minutes} (must be < 60)")
        if seconds >= 60:
            raise ValueError(f"Invalid seconds value: {seconds} (must be < 60)")
        return hours * 3600 + minutes * 60 + seconds
    else:
        raise ValueError(f"Invalid timestamp format: {timestamp}")


def get_youtube_video_id(url):
    """Extract video ID from YouTube URL."""
    parsed_url = urlparse(url)
    
    if parsed_url.hostname in ['www.youtube.com', 'youtube.com']:
        if parsed_url.path == '/watch':
            return parse_qs(parsed_url.query).get('v', [None])[0]
    elif parsed_url.hostname in ['youtu.be']:
        return parsed_url.path[1:]  # Remove leading slash
    
    return None


def create_youtube_timestamp_url(video_url, timestamp_seconds):
    """Create YouTube URL with timestamp parameter."""
    video_id = get_youtube_video_id(video_url)
    if not video_id:
        return video_url  # Return original URL if we can't parse it
    
    return f"https://www.youtube.com/watch?v={video_id}&t={timestamp_seconds}s"


def enrich_timestamps_with_links(markdown_text, video_url):
    """Replace timestamps in markdown with YouTube timestamp links.
    
    Supports formats like:
    - [8:05] -> single timestamp
    - [8:05-8:24] -> timestamp range (links to start time)
    - [0:01-0:07, 0:56-1:21] -> multiple timestamps (links each separately)
    """
    def replace_timestamp_match(match):
        full_match = match.group(0)  # e.g., "[8:05-8:24]" or "[1:43-1:53]"
        timestamp_content = match.group(1)  # e.g., "8:05-8:24" or "1:43-1:53"
        
        # Handle multiple timestamps separated by commas
        if ',' in timestamp_content:
            parts = [part.strip() for part in timestamp_content.split(',')]
            linked_parts = []
            
            for part in parts:
                if '-' in part:
                    # Range like "8:05-8:24" - link to start time
                    start_time = part.split('-')[0].strip()
                else:
                    # Single timestamp like "8:05"
                    start_time = part.strip()
                
                try:
                    seconds = parse_timestamp_to_seconds(start_time)
                    timestamp_url = create_youtube_timestamp_url(video_url, seconds)
                    linked_parts.append(f"[{part}]({timestamp_url})")
                except ValueError:
                    # If parsing fails, keep original
                    linked_parts.append(part)
            
            return ', '.join(linked_parts)
        else:
            # Single timestamp or range
            if '-' in timestamp_content:
                # Range like "8:05-8:24" - link to start time
                start_time = timestamp_content.split('-')[0].strip()
            else:
                # Single timestamp like "8:05"
                start_time = timestamp_content.strip()
            
            try:
                seconds = parse_timestamp_to_seconds(start_time)
                timestamp_url = create_youtube_timestamp_url(video_url, seconds)
                return f"[{timestamp_content}]({timestamp_url})"
            except ValueError:
                # If parsing fails, return original
                return full_match
    
    # Regex to match timestamps in brackets
    # Matches: [8:05], [8:05-8:24], [0:01-0:07, 0:56-1:21]
    timestamp_pattern = r'\[([0-9]+:[0-9]+(?:-[0-9]+:[0-9]+)?(?:\s*,\s*[0-9]+:[0-9]+(?:-[0-9]+:[0-9]+)?)*)\]'
    
    return re.sub(timestamp_pattern, replace_timestamp_match, markdown_text)