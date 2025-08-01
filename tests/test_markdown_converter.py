"""
Unit tests for markdown_converter module.
Tests the conversion of markdown text to Notion rich text blocks.
"""

import unittest
from youtube_notion.utils.markdown_converter import parse_rich_text, markdown_to_notion_blocks


class TestParseRichText(unittest.TestCase):
    """Test cases for parse_rich_text function."""
    
    def test_plain_text(self):
        """Test parsing plain text without formatting."""
        result = parse_rich_text("Hello world")
        expected = [{"type": "text", "text": {"content": "Hello world"}}]
        self.assertEqual(result, expected)
    
    def test_bold_text(self):
        """Test parsing bold text."""
        result = parse_rich_text("This is **bold** text")
        expected = [
            {"type": "text", "text": {"content": "This is "}},
            {"type": "text", "text": {"content": "bold"}, "annotations": {"bold": True}},
            {"type": "text", "text": {"content": " text"}}
        ]
        self.assertEqual(result, expected)
    
    def test_italic_text(self):
        """Test parsing italic text."""
        result = parse_rich_text("This is *italic* text")
        expected = [
            {"type": "text", "text": {"content": "This is "}},
            {"type": "text", "text": {"content": "italic"}, "annotations": {"italic": True}},
            {"type": "text", "text": {"content": " text"}}
        ]
        self.assertEqual(result, expected)
    
    def test_mixed_formatting(self):
        """Test parsing text with both bold and italic."""
        result = parse_rich_text("**Bold** and *italic* text")
        expected = [
            {"type": "text", "text": {"content": "Bold"}, "annotations": {"bold": True}},
            {"type": "text", "text": {"content": " and "}},
            {"type": "text", "text": {"content": "italic"}, "annotations": {"italic": True}},
            {"type": "text", "text": {"content": " text"}}
        ]
        self.assertEqual(result, expected)
    
    def test_empty_text(self):
        """Test parsing empty text."""
        result = parse_rich_text("")
        expected = []
        self.assertEqual(result, expected)
    
    def test_multiple_bold(self):
        """Test parsing multiple bold sections."""
        result = parse_rich_text("**First** and **second** bold")
        expected = [
            {"type": "text", "text": {"content": "First"}, "annotations": {"bold": True}},
            {"type": "text", "text": {"content": " and "}},
            {"type": "text", "text": {"content": "second"}, "annotations": {"bold": True}},
            {"type": "text", "text": {"content": " bold"}}
        ]
        self.assertEqual(result, expected)
    
    def test_link_text(self):
        """Test parsing markdown links."""
        result = parse_rich_text("Check out [this link](https://example.com) for more info")
        expected = [
            {"type": "text", "text": {"content": "Check out "}},
            {"type": "text", "text": {"content": "this link", "link": {"url": "https://example.com"}}},
            {"type": "text", "text": {"content": " for more info"}}
        ]
        self.assertEqual(result, expected)
    
    def test_multiple_links(self):
        """Test parsing multiple links."""
        result = parse_rich_text("Visit [Google](https://google.com) and [GitHub](https://github.com)")
        expected = [
            {"type": "text", "text": {"content": "Visit "}},
            {"type": "text", "text": {"content": "Google", "link": {"url": "https://google.com"}}},
            {"type": "text", "text": {"content": " and "}},
            {"type": "text", "text": {"content": "GitHub", "link": {"url": "https://github.com"}}},
        ]
        self.assertEqual(result, expected)
    
    def test_bold_link(self):
        """Test parsing bold text within links."""
        result = parse_rich_text("Click [**bold link**](https://example.com) here")
        expected = [
            {"type": "text", "text": {"content": "Click "}},
            {"type": "text", "text": {"content": "bold link", "link": {"url": "https://example.com"}}, "annotations": {"bold": True}},
            {"type": "text", "text": {"content": " here"}}
        ]
        self.assertEqual(result, expected)
    
    def test_italic_link(self):
        """Test parsing italic text within links."""
        result = parse_rich_text("Click [*italic link*](https://example.com) here")
        expected = [
            {"type": "text", "text": {"content": "Click "}},
            {"type": "text", "text": {"content": "italic link", "link": {"url": "https://example.com"}}, "annotations": {"italic": True}},
            {"type": "text", "text": {"content": " here"}}
        ]
        self.assertEqual(result, expected)
    
    def test_mixed_formatting_with_links(self):
        """Test parsing mixed formatting including links."""
        result = parse_rich_text("**Bold** text with [link](https://example.com) and *italic*")
        expected = [
            {"type": "text", "text": {"content": "Bold"}, "annotations": {"bold": True}},
            {"type": "text", "text": {"content": " text with "}},
            {"type": "text", "text": {"content": "link", "link": {"url": "https://example.com"}}},
            {"type": "text", "text": {"content": " and "}},
            {"type": "text", "text": {"content": "italic"}, "annotations": {"italic": True}}
        ]
        self.assertEqual(result, expected)
    
    def test_timestamp_link(self):
        """Test parsing timestamp links (like those generated by timestamp enrichment)."""
        result = parse_rich_text("See [8:05](https://youtube.com/watch?v=test&t=485s) for details")
        expected = [
            {"type": "text", "text": {"content": "See "}},
            {"type": "text", "text": {"content": "8:05", "link": {"url": "https://youtube.com/watch?v=test&t=485s"}}},
            {"type": "text", "text": {"content": " for details"}}
        ]
        self.assertEqual(result, expected)


class TestMarkdownToNotionBlocks(unittest.TestCase):
    """Test cases for markdown_to_notion_blocks function."""
    
    def test_heading_1(self):
        """Test parsing H1 heading."""
        result = markdown_to_notion_blocks("# Main Title")
        expected = [{
            "object": "block",
            "type": "heading_1",
            "heading_1": {
                "rich_text": [{"type": "text", "text": {"content": "Main Title"}}]
            }
        }]
        self.assertEqual(result, expected)
    
    def test_heading_2(self):
        """Test parsing H2 heading."""
        result = markdown_to_notion_blocks("## Subtitle")
        expected = [{
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [{"type": "text", "text": {"content": "Subtitle"}}]
            }
        }]
        self.assertEqual(result, expected)
    
    def test_heading_3(self):
        """Test parsing H3 heading."""
        result = markdown_to_notion_blocks("### Section Title")
        expected = [{
            "object": "block",
            "type": "heading_3",
            "heading_3": {
                "rich_text": [{"type": "text", "text": {"content": "Section Title"}}]
            }
        }]
        self.assertEqual(result, expected)
    
    def test_heading_4(self):
        """Test parsing H4 heading (should become H3 in Notion)."""
        result = markdown_to_notion_blocks("#### Subsection Title")
        expected = [{
            "object": "block",
            "type": "heading_3",
            "heading_3": {
                "rich_text": [{"type": "text", "text": {"content": "Subsection Title"}}]
            }
        }]
        self.assertEqual(result, expected)
    
    def test_heading_5(self):
        """Test parsing H5 heading (should become H3 in Notion)."""
        result = markdown_to_notion_blocks("##### Deep Subsection")
        expected = [{
            "object": "block",
            "type": "heading_3",
            "heading_3": {
                "rich_text": [{"type": "text", "text": {"content": "Deep Subsection"}}]
            }
        }]
        self.assertEqual(result, expected)
    
    def test_heading_6(self):
        """Test parsing H6 heading (should become H3 in Notion)."""
        result = markdown_to_notion_blocks("###### Deepest Level")
        expected = [{
            "object": "block",
            "type": "heading_3",
            "heading_3": {
                "rich_text": [{"type": "text", "text": {"content": "Deepest Level"}}]
            }
        }]
        self.assertEqual(result, expected)
    
    def test_paragraph(self):
        """Test parsing regular paragraph."""
        result = markdown_to_notion_blocks("This is a paragraph")
        expected = [{
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"type": "text", "text": {"content": "This is a paragraph"}}]
            }
        }]
        self.assertEqual(result, expected)
    
    def test_bullet_list_dash(self):
        """Test parsing bullet list with dash."""
        result = markdown_to_notion_blocks("- First item")
        expected = [{
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{"type": "text", "text": {"content": "First item"}}]
            }
        }]
        self.assertEqual(result, expected)
    
    def test_bullet_list_asterisk(self):
        """Test parsing bullet list with asterisk."""
        result = markdown_to_notion_blocks("*   First item")
        expected = [{
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{"type": "text", "text": {"content": "First item"}}]
            }
        }]
        self.assertEqual(result, expected)
    
    def test_numbered_list(self):
        """Test parsing numbered list."""
        result = markdown_to_notion_blocks("1. First item")
        expected = [{
            "object": "block",
            "type": "numbered_list_item",
            "numbered_list_item": {
                "rich_text": [{"type": "text", "text": {"content": "First item"}}]
            }
        }]
        self.assertEqual(result, expected)
    
    def test_multiple_blocks(self):
        """Test parsing multiple blocks."""
        markdown = """# Title
        
This is a paragraph.

## Subtitle

- Bullet item
1. Numbered item"""
        
        result = markdown_to_notion_blocks(markdown)
        
        # Should have 5 blocks (title, paragraph, subtitle, bullet, numbered)
        self.assertEqual(len(result), 5)
        
        # Check first block is H1
        self.assertEqual(result[0]["type"], "heading_1")
        self.assertEqual(result[0]["heading_1"]["rich_text"][0]["text"]["content"], "Title")
        
        # Check second block is paragraph
        self.assertEqual(result[1]["type"], "paragraph")
        self.assertEqual(result[1]["paragraph"]["rich_text"][0]["text"]["content"], "This is a paragraph.")
        
        # Check third block is H2
        self.assertEqual(result[2]["type"], "heading_2")
        self.assertEqual(result[2]["heading_2"]["rich_text"][0]["text"]["content"], "Subtitle")
        
        # Check fourth block is bullet list
        self.assertEqual(result[3]["type"], "bulleted_list_item")
        self.assertEqual(result[3]["bulleted_list_item"]["rich_text"][0]["text"]["content"], "Bullet item")
        
        # Check fifth block is numbered list
        self.assertEqual(result[4]["type"], "numbered_list_item")
        self.assertEqual(result[4]["numbered_list_item"]["rich_text"][0]["text"]["content"], "Numbered item")
    
    def test_empty_lines_ignored(self):
        """Test that empty lines are ignored."""
        markdown = """# Title


This is a paragraph."""
        
        result = markdown_to_notion_blocks(markdown)
        
        # Should have 2 blocks (title and paragraph), empty lines ignored
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["type"], "heading_1")
        self.assertEqual(result[1]["type"], "paragraph")
    
    def test_formatted_text_in_blocks(self):
        """Test that formatting is preserved in blocks."""
        result = markdown_to_notion_blocks("This is **bold** text")
        
        # Should have 1 paragraph block with formatted rich text
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["type"], "paragraph")
        
        rich_text = result[0]["paragraph"]["rich_text"]
        self.assertEqual(len(rich_text), 3)  # "This is ", "bold", " text"
        self.assertEqual(rich_text[1]["annotations"]["bold"], True)
    
    def test_complex_numbered_list(self):
        """Test parsing numbered list with different numbers."""
        markdown = """1. First item
2. Second item
10. Tenth item"""
        
        result = markdown_to_notion_blocks(markdown)
        
        # Should have 3 numbered list items
        self.assertEqual(len(result), 3)
        for block in result:
            self.assertEqual(block["type"], "numbered_list_item")
        
        self.assertEqual(result[0]["numbered_list_item"]["rich_text"][0]["text"]["content"], "First item")
        self.assertEqual(result[1]["numbered_list_item"]["rich_text"][0]["text"]["content"], "Second item")
        self.assertEqual(result[2]["numbered_list_item"]["rich_text"][0]["text"]["content"], "Tenth item")
    
    def test_all_header_levels(self):
        """Test parsing all header levels in one document."""
        markdown = """# Main Title
## Section
### Subsection
#### Deep Section
##### Deeper Section
###### Deepest Section"""
        
        result = markdown_to_notion_blocks(markdown)
        
        # Should have 6 blocks
        self.assertEqual(len(result), 6)
        
        # Check header types
        self.assertEqual(result[0]["type"], "heading_1")
        self.assertEqual(result[0]["heading_1"]["rich_text"][0]["text"]["content"], "Main Title")
        
        self.assertEqual(result[1]["type"], "heading_2")
        self.assertEqual(result[1]["heading_2"]["rich_text"][0]["text"]["content"], "Section")
        
        self.assertEqual(result[2]["type"], "heading_3")
        self.assertEqual(result[2]["heading_3"]["rich_text"][0]["text"]["content"], "Subsection")
        
        # H4, H5, H6 should all become H3
        self.assertEqual(result[3]["type"], "heading_3")
        self.assertEqual(result[3]["heading_3"]["rich_text"][0]["text"]["content"], "Deep Section")
        
        self.assertEqual(result[4]["type"], "heading_3")
        self.assertEqual(result[4]["heading_3"]["rich_text"][0]["text"]["content"], "Deeper Section")
        
        self.assertEqual(result[5]["type"], "heading_3")
        self.assertEqual(result[5]["heading_3"]["rich_text"][0]["text"]["content"], "Deepest Section")


if __name__ == '__main__':
    unittest.main()