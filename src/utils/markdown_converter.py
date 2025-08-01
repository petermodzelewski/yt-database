"""
Markdown to Notion converter utilities.
Converts markdown text to Notion's rich text block format.
"""

import re


def parse_rich_text(text):
    """Parse text with markdown formatting to Notion rich text format."""
    rich_text = []
    
    # Simple regex patterns for bold and italic
    parts = re.split(r'(\*\*.*?\*\*|\*.*?\*)', text)
    
    for part in parts:
        if not part:
            continue
            
        if part.startswith('**') and part.endswith('**'):
            # Bold text
            rich_text.append({
                "type": "text",
                "text": {"content": part[2:-2]},
                "annotations": {"bold": True}
            })
        elif part.startswith('*') and part.endswith('*'):
            # Italic text
            rich_text.append({
                "type": "text", 
                "text": {"content": part[1:-1]},
                "annotations": {"italic": True}
            })
        else:
            # Regular text
            rich_text.append({
                "type": "text",
                "text": {"content": part}
            })
    
    return rich_text


def markdown_to_notion_blocks(markdown_text):
    """Convert markdown text to Notion rich text blocks."""
    blocks = []
    lines = markdown_text.split('\n')
    i = 0
    
    while i < len(lines):
        line = lines[i].strip()
        
        if not line:
            i += 1
            continue
            
        # Handle headers (Notion supports only H1, H2, H3)
        if line.startswith('#'):
            # Count the number of # symbols
            header_level = 0
            for char in line:
                if char == '#':
                    header_level += 1
                else:
                    break
            
            header_text = line[header_level:].strip()
            
            if header_level == 1:
                blocks.append({
                    "object": "block",
                    "type": "heading_1",
                    "heading_1": {
                        "rich_text": [{"type": "text", "text": {"content": header_text}}]
                    }
                })
            elif header_level == 2:
                blocks.append({
                    "object": "block",
                    "type": "heading_2", 
                    "heading_2": {
                        "rich_text": [{"type": "text", "text": {"content": header_text}}]
                    }
                })
            elif header_level >= 3:
                # H3 and beyond all become H3 in Notion
                blocks.append({
                    "object": "block",
                    "type": "heading_3",
                    "heading_3": {
                        "rich_text": [{"type": "text", "text": {"content": header_text}}]
                    }
                })
        # Handle bullet points
        elif line.startswith('*   ') or line.startswith('- '):
            bullet_text = line[4:] if line.startswith('*   ') else line[2:]
            blocks.append({
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": parse_rich_text(bullet_text)
                }
            })
        # Handle numbered lists
        elif re.match(r'^\d+\.', line):
            numbered_text = re.sub(r'^\d+\.\s*', '', line)
            blocks.append({
                "object": "block",
                "type": "numbered_list_item", 
                "numbered_list_item": {
                    "rich_text": parse_rich_text(numbered_text)
                }
            })
        # Handle regular paragraphs
        else:
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": parse_rich_text(line)
                }
            })
        
        i += 1
    
    return blocks