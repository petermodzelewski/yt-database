"""
Unit tests for markdown_converter module.
Tests the conversion of markdown text to Notion rich text blocks.
"""

from youtube_notion.utils.markdown_converter import parse_rich_text, markdown_to_notion_blocks


class TestParseRichText:
    """Test cases for parse_rich_text function."""
    
    def test_plain_text(self):
        """Test parsing plain text without formatting."""
        result = parse_rich_text("Hello world")
        expected = [{"type": "text", "text": {"content": "Hello world"}}]
        assert result == expected
    
    def test_bold_text(self):
        """Test parsing bold text."""
        result = parse_rich_text("This is **bold** text")
        expected = [
            {"type": "text", "text": {"content": "This is "}},
            {"type": "text", "text": {"content": "bold"}, "annotations": {"bold": True}},
            {"type": "text", "text": {"content": " text"}}
        ]
        assert result == expected
    
    def test_italic_text(self):
        """Test parsing italic text."""
        result = parse_rich_text("This is *italic* text")
        expected = [
            {"type": "text", "text": {"content": "This is "}},
            {"type": "text", "text": {"content": "italic"}, "annotations": {"italic": True}},
            {"type": "text", "text": {"content": " text"}}
        ]
        assert result == expected
    
    def test_mixed_formatting(self):
        """Test parsing text with both bold and italic."""
        result = parse_rich_text("**Bold** and *italic* text")
        expected = [
            {"type": "text", "text": {"content": "Bold"}, "annotations": {"bold": True}},
            {"type": "text", "text": {"content": " and "}},
            {"type": "text", "text": {"content": "italic"}, "annotations": {"italic": True}},
            {"type": "text", "text": {"content": " text"}}
        ]
        assert result == expected
    
    def test_empty_text(self):
        """Test parsing empty text."""
        result = parse_rich_text("")
        expected = []
        assert result == expected
    
    def test_multiple_bold(self):
        """Test parsing multiple bold sections."""
        result = parse_rich_text("**First** and **second** bold")
        expected = [
            {"type": "text", "text": {"content": "First"}, "annotations": {"bold": True}},
            {"type": "text", "text": {"content": " and "}},
            {"type": "text", "text": {"content": "second"}, "annotations": {"bold": True}},
            {"type": "text", "text": {"content": " bold"}}
        ]
        assert result == expected
    
    def test_link_text(self):
        """Test parsing markdown links."""
        result = parse_rich_text("Check out [this link](https://example.com) for more info")
        expected = [
            {"type": "text", "text": {"content": "Check out "}},
            {"type": "text", "text": {"content": "this link", "link": {"url": "https://example.com"}}},
            {"type": "text", "text": {"content": " for more info"}}
        ]
        assert result == expected
    
    def test_multiple_links(self):
        """Test parsing multiple links."""
        result = parse_rich_text("Visit [Google](https://google.com) and [GitHub](https://github.com)")
        expected = [
            {"type": "text", "text": {"content": "Visit "}},
            {"type": "text", "text": {"content": "Google", "link": {"url": "https://google.com"}}},
            {"type": "text", "text": {"content": " and "}},
            {"type": "text", "text": {"content": "GitHub", "link": {"url": "https://github.com"}}},
        ]
        assert result == expected
    
    def test_bold_link(self):
        """Test parsing bold text within links."""
        result = parse_rich_text("Click [**bold link**](https://example.com) here")
        expected = [
            {"type": "text", "text": {"content": "Click "}},
            {"type": "text", "text": {"content": "bold link", "link": {"url": "https://example.com"}}, "annotations": {"bold": True}},
            {"type": "text", "text": {"content": " here"}}
        ]
        assert result == expected
    
    def test_italic_link(self):
        """Test parsing italic text within links."""
        result = parse_rich_text("Click [*italic link*](https://example.com) here")
        expected = [
            {"type": "text", "text": {"content": "Click "}},
            {"type": "text", "text": {"content": "italic link", "link": {"url": "https://example.com"}}, "annotations": {"italic": True}},
            {"type": "text", "text": {"content": " here"}}
        ]
        assert result == expected
    
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
        assert result == expected
    
    def test_timestamp_link(self):
        """Test parsing timestamp links (like those generated by timestamp enrichment)."""
        result = parse_rich_text("See [8:05](https://youtube.com/watch?v=test&t=485s) for details")
        expected = [
            {"type": "text", "text": {"content": "See "}},
            {"type": "text", "text": {"content": "8:05", "link": {"url": "https://youtube.com/watch?v=test&t=485s"}}},
            {"type": "text", "text": {"content": " for details"}}
        ]
        assert result == expected
    
    def test_link_inside_bold_text(self):
        """Test parsing links inside bold text - the main fix for the reported issue."""
        result = parse_rich_text("**Parenting Advice [01:16-01:49](https://www.youtube.com/watch?v=8fVHFt7Shf4&t=76s):** Alex uses Claude")
        expected = [
            {"type": "text", "text": {"content": "Parenting Advice "}, "annotations": {"bold": True}},
            {"type": "text", "text": {"content": "01:16-01:49", "link": {"url": "https://www.youtube.com/watch?v=8fVHFt7Shf4&t=76s"}}, "annotations": {"bold": True}},
            {"type": "text", "text": {"content": ":"}, "annotations": {"bold": True}},
            {"type": "text", "text": {"content": " Alex uses Claude"}}
        ]
        assert result == expected
    
    def test_link_inside_italic_text(self):
        """Test parsing links inside italic text."""
        result = parse_rich_text("*Check out [this link](https://example.com) for more info*")
        expected = [
            {"type": "text", "text": {"content": "Check out "}, "annotations": {"italic": True}},
            {"type": "text", "text": {"content": "this link", "link": {"url": "https://example.com"}}, "annotations": {"italic": True}},
            {"type": "text", "text": {"content": " for more info"}, "annotations": {"italic": True}}
        ]
        assert result == expected
    
    def test_multiple_links_inside_bold_text(self):
        """Test parsing multiple links inside bold text."""
        result = parse_rich_text("**Visit [Google](https://google.com) and [GitHub](https://github.com)**")
        expected = [
            {"type": "text", "text": {"content": "Visit "}, "annotations": {"bold": True}},
            {"type": "text", "text": {"content": "Google", "link": {"url": "https://google.com"}}, "annotations": {"bold": True}},
            {"type": "text", "text": {"content": " and "}, "annotations": {"bold": True}},
            {"type": "text", "text": {"content": "GitHub", "link": {"url": "https://github.com"}}, "annotations": {"bold": True}}
        ]
        assert result == expected
    
    def test_bold_text_with_link_and_regular_text(self):
        """Test bold text containing a link followed by regular text."""
        result = parse_rich_text("**Bold with [link](https://example.com)** and regular text")
        expected = [
            {"type": "text", "text": {"content": "Bold with "}, "annotations": {"bold": True}},
            {"type": "text", "text": {"content": "link", "link": {"url": "https://example.com"}}, "annotations": {"bold": True}},
            {"type": "text", "text": {"content": " and regular text"}}
        ]
        assert result == expected
    
    def test_complex_formatting_with_links(self):
        """Test complex scenario with multiple formatting types and links."""
        result = parse_rich_text("**Bold [link1](https://example1.com)** and *italic [link2](https://example2.com)* text")
        expected = [
            {"type": "text", "text": {"content": "Bold "}, "annotations": {"bold": True}},
            {"type": "text", "text": {"content": "link1", "link": {"url": "https://example1.com"}}, "annotations": {"bold": True}},
            {"type": "text", "text": {"content": " and "}},
            {"type": "text", "text": {"content": "italic "}, "annotations": {"italic": True}},
            {"type": "text", "text": {"content": "link2", "link": {"url": "https://example2.com"}}, "annotations": {"italic": True}},
            {"type": "text", "text": {"content": " text"}}
        ]
        assert result == expected
    
    def test_youtube_timestamp_in_bold_bullet_point(self):
        """Test the specific case from the bug report - YouTube timestamp in bold bullet point."""
        # This simulates the markdown after timestamp enrichment
        result = parse_rich_text("**Parenting Advice [01:16-01:49](https://www.youtube.com/watch?v=8fVHFt7Shf4&t=76s):** Alex uses Claude to get an objective perspective.")
        expected = [
            {"type": "text", "text": {"content": "Parenting Advice "}, "annotations": {"bold": True}},
            {"type": "text", "text": {"content": "01:16-01:49", "link": {"url": "https://www.youtube.com/watch?v=8fVHFt7Shf4&t=76s"}}, "annotations": {"bold": True}},
            {"type": "text", "text": {"content": ":"}, "annotations": {"bold": True}},
            {"type": "text", "text": {"content": " Alex uses Claude to get an objective perspective."}}
        ]
        assert result == expected
    
    def test_nested_formatting_edge_cases(self):
        """Test edge cases with nested formatting."""
        # Bold text with no links should still work
        result = parse_rich_text("**Just bold text**")
        expected = [
            {"type": "text", "text": {"content": "Just bold text"}, "annotations": {"bold": True}}
        ]
        assert result == expected
        
        # Italic text with no links should still work
        result = parse_rich_text("*Just italic text*")
        expected = [
            {"type": "text", "text": {"content": "Just italic text"}, "annotations": {"italic": True}}
        ]
        assert result == expected
    
    def test_malformed_links_in_formatted_text(self):
        """Test that malformed links in formatted text don't break parsing."""
        # Missing closing bracket - should be treated as regular text
        result = parse_rich_text("**Bold with [incomplete link**")
        expected = [
            {"type": "text", "text": {"content": "Bold with [incomplete link"}, "annotations": {"bold": True}}
        ]
        assert result == expected
        
        # Empty URL parentheses - regex requires at least one char, so treated as regular text
        result = parse_rich_text("**Bold with [text]() empty URL**")
        expected = [
            {"type": "text", "text": {"content": "Bold with "}, "annotations": {"bold": True}},
            {"type": "text", "text": {"content": "["}, "annotations": {"bold": True}},
            {"type": "text", "text": {"content": "text]() empty URL"}, "annotations": {"bold": True}}
        ]
        assert result == expected
        
        # Incomplete link pattern - should be treated as regular text
        result = parse_rich_text("**Bold with [text] no parentheses**")
        expected = [
            {"type": "text", "text": {"content": "Bold with [text] no parentheses"}, "annotations": {"bold": True}}
        ]
        assert result == expected

    def test_table(self):
        """Test parsing a markdown table."""
        markdown = """| Header 1 | Header 2 |
|----------|----------|
| Cell 1   | Cell 2   |
| Cell 3   | Cell 4   |"""
        result = markdown_to_notion_blocks(markdown)
        expected = [
            {
                "object": "block",
                "type": "table",
                "table": {
                    "table_width": 2,
                    "has_column_header": True,
                    "has_row_header": False,
                    "children": [
                        {
                            "type": "table_row",
                            "table_row": {
                                "cells": [
                                    [{"type": "text", "text": {"content": "Header 1"}}],
                                    [{"type": "text", "text": {"content": "Header 2"}}]
                                ]
                            }
                        },
                        {
                            "type": "table_row",
                            "table_row": {
                                "cells": [
                                    [{"type": "text", "text": {"content": "Cell 1"}}],
                                    [{"type": "text", "text": {"content": "Cell 2"}}]
                                ]
                            }
                        },
                        {
                            "type": "table_row",
                            "table_row": {
                                "cells": [
                                    [{"type": "text", "text": {"content": "Cell 3"}}],
                                    [{"type": "text", "text": {"content": "Cell 4"}}]
                                ]
                            }
                        }
                    ]
                }
            }
        ]
        assert result == expected


class TestMarkdownToNotionBlocks:
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
        assert result == expected
    
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
        assert result == expected
    
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
        assert result == expected
    
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
        assert result == expected
    
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
        assert result == expected
    
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
        assert result == expected
    
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
        assert result == expected
    
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
        assert result == expected
    
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
        assert result == expected
    
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
        assert result == expected
    
    def test_multiple_blocks(self):
        """Test parsing multiple blocks."""
        markdown = """# Title
        
This is a paragraph.

## Subtitle

- Bullet item
1. Numbered item"""
        
        result = markdown_to_notion_blocks(markdown)
        
        # Should have 5 blocks (title, paragraph, subtitle, bullet, numbered)
        assert len(result) == 5
        
        # Check first block is H1
        assert result[0]["type"] == "heading_1"
        assert result[0]["heading_1"]["rich_text"][0]["text"]["content"] == "Title"
        
        # Check second block is paragraph
        assert result[1]["type"] == "paragraph"
        assert result[1]["paragraph"]["rich_text"][0]["text"]["content"] == "This is a paragraph."
        
        # Check third block is H2
        assert result[2]["type"] == "heading_2"
        assert result[2]["heading_2"]["rich_text"][0]["text"]["content"] == "Subtitle"
        
        # Check fourth block is bullet list
        assert result[3]["type"] == "bulleted_list_item"
        assert result[3]["bulleted_list_item"]["rich_text"][0]["text"]["content"] == "Bullet item"
        
        # Check fifth block is numbered list
        assert result[4]["type"] == "numbered_list_item"
        assert result[4]["numbered_list_item"]["rich_text"][0]["text"]["content"] == "Numbered item"
    
    def test_empty_lines_ignored(self):
        """Test that empty lines are ignored."""
        markdown = """# Title


This is a paragraph."""
        
        result = markdown_to_notion_blocks(markdown)
        
        # Should have 2 blocks (title and paragraph), empty lines ignored
        assert len(result) == 2
        assert result[0]["type"] == "heading_1"
        assert result[1]["type"] == "paragraph"
    
    def test_formatted_text_in_blocks(self):
        """Test that formatting is preserved in blocks."""
        result = markdown_to_notion_blocks("This is **bold** text")
        
        # Should have 1 paragraph block with formatted rich text
        assert len(result) == 1
        assert result[0]["type"] == "paragraph"
        
        rich_text = result[0]["paragraph"]["rich_text"]
        assert len(rich_text) == 3  # "This is ", "bold", " text"
        assert rich_text[1]["annotations"]["bold"] is True
    
    def test_complex_numbered_list(self):
        """Test parsing numbered list with different numbers."""
        markdown = """1. First item
2. Second item
10. Tenth item"""
        
        result = markdown_to_notion_blocks(markdown)
        
        # Should have 3 numbered list items
        assert len(result) == 3
        for block in result:
            assert block["type"] == "numbered_list_item"
        
        assert result[0]["numbered_list_item"]["rich_text"][0]["text"]["content"] == "First item"
        assert result[1]["numbered_list_item"]["rich_text"][0]["text"]["content"] == "Second item"
        assert result[2]["numbered_list_item"]["rich_text"][0]["text"]["content"] == "Tenth item"
    
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
        assert len(result) == 6
        
        # Check header types
        assert result[0]["type"] == "heading_1"
        assert result[0]["heading_1"]["rich_text"][0]["text"]["content"] == "Main Title"
        
        assert result[1]["type"] == "heading_2"
        assert result[1]["heading_2"]["rich_text"][0]["text"]["content"] == "Section"
        
        assert result[2]["type"] == "heading_3"
        assert result[2]["heading_3"]["rich_text"][0]["text"]["content"] == "Subsection"
        
        # H4, H5, H6 should all become H3
        assert result[3]["type"] == "heading_3"
        assert result[3]["heading_3"]["rich_text"][0]["text"]["content"] == "Deep Section"
        
        assert result[4]["type"] == "heading_3"
        assert result[4]["heading_3"]["rich_text"][0]["text"]["content"] == "Deeper Section"
        
        assert result[5]["type"] == "heading_3"
        assert result[5]["heading_3"]["rich_text"][0]["text"]["content"] == "Deepest Section"
    
    def test_bullet_point_with_bold_timestamp_link(self):
        """Test the full pipeline for bullet points with bold timestamp links."""
        # This tests the exact scenario from the bug report
        markdown = "*   **Parenting Advice [01:16-01:49](https://www.youtube.com/watch?v=8fVHFt7Shf4&t=76s):** Alex uses Claude to get an objective perspective."
        
        result = markdown_to_notion_blocks(markdown)
        
        # Should have 1 bulleted list item
        assert len(result) == 1
        assert result[0]["type"] == "bulleted_list_item"
        
        # Check the rich text structure
        rich_text = result[0]["bulleted_list_item"]["rich_text"]
        assert len(rich_text) == 4  # "Parenting Advice ", "01:16-01:49" (link), ":", " Alex uses..."
        
        # First part: "Parenting Advice " (bold)
        assert rich_text[0]["text"]["content"] == "Parenting Advice "
        assert rich_text[0]["annotations"]["bold"] is True
        assert "link" not in rich_text[0]["text"]
        
        # Second part: "01:16-01:49" (bold + link)
        assert rich_text[1]["text"]["content"] == "01:16-01:49"
        assert rich_text[1]["annotations"]["bold"] is True
        assert rich_text[1]["text"]["link"]["url"] == "https://www.youtube.com/watch?v=8fVHFt7Shf4&t=76s"
        
        # Third part: ":" (bold)
        assert rich_text[2]["text"]["content"] == ":"
        assert rich_text[2]["annotations"]["bold"] is True
        assert "link" not in rich_text[2]["text"]
        
        # Fourth part: " Alex uses..." (regular text)
        assert rich_text[3]["text"]["content"] == " Alex uses Claude to get an objective perspective."
        assert "annotations" not in rich_text[3]
        assert "link" not in rich_text[3]["text"]
    
    def test_heading_with_link_in_bold_text(self):
        """Test headings containing bold text with links."""
        markdown = "### **Section with [link](https://example.com)**"
        
        result = markdown_to_notion_blocks(markdown)
        
        # Should have 1 heading_3 block
        assert len(result) == 1
        assert result[0]["type"] == "heading_3"
        
        # Check the rich text structure
        rich_text = result[0]["heading_3"]["rich_text"]
        assert len(rich_text) == 2  # "Section with ", "link"
        
        # First part: "Section with " (bold)
        assert rich_text[0]["text"]["content"] == "Section with "
        assert rich_text[0]["annotations"]["bold"] is True
        
        # Second part: "link" (bold + link)
        assert rich_text[1]["text"]["content"] == "link"
        assert rich_text[1]["annotations"]["bold"] is True
        assert rich_text[1]["text"]["link"]["url"] == "https://example.com"

    def test_table_with_formatted_cells(self):
        """Test parsing a markdown table with formatted cells."""
        markdown = """| *Header 1* | **Header 2** |
|------------|--------------|
| `Cell 1`   | [Cell 2](https://example.com) |
| ~~Cell 3~~ | `Cell 4`     |"""
        result = markdown_to_notion_blocks(markdown)
        assert len(result) == 1
        assert result[0]['type'] == 'table'
        table = result[0]['table']
        assert table['table_width'] == 2
        assert table['has_column_header'] is True
        assert len(table['children']) == 3

        # header
        header_row = table['children'][0]
        assert header_row['table_row']['cells'][0][0]['annotations']['italic'] is True
        assert header_row['table_row']['cells'][1][0]['annotations']['bold'] is True

        # row 1
        row1 = table['children'][1]
        assert row1['table_row']['cells'][0][0]['annotations']['code'] is True
        assert 'link' in row1['table_row']['cells'][1][0]['text']

        # row 2
        row2 = table['children'][2]
        assert row2['table_row']['cells'][0][0]['annotations']['strikethrough'] is True
        assert row2['table_row']['cells'][1][0]['annotations']['code'] is True

    def test_no_formatting_in_code_blocks(self):
        """Test that markdown formatting is not processed inside code blocks."""
        markdown = """```
**This should not be bold**
*This should not be italic*
[This should not be a link](https://example.com)
```"""
        result = markdown_to_notion_blocks(markdown)
        assert len(result) == 1
        assert result[0]['type'] == 'code'
        rich_text = result[0]['code']['rich_text']
        assert len(rich_text) == 1
        assert rich_text[0]['text']['content'] == '**This should not be bold**\n*This should not be italic*\n[This should not be a link](https://example.com)'

    def test_user_table_example(self):
        """Test parsing the user's specific table example."""
        markdown = """| Question                                 | When to Use an Agent (Complex) | When to Use a Workflow (Simpler)      |
| ---------------------------------------- | ------------------------------ | ------------------------------------- |
| **Is the task complex enough?**          | Yes (Path to goal is unclear)  | No (Clear, step-by-step process)      |
| **Is the task valuable enough?**         | Yes (High value, e.g., >$1/run) | No (Low value, e.g., <$0.1/run)       |
| **Are all parts of the task doable?**    | Yes (Necessary tools exist)    | No (Required tools are unavailable)   |
| **What is the cost of error?**           | Low (Errors are cheap/reversible) | High (Errors are costly/irreversible) |"""
        result = markdown_to_notion_blocks(markdown)
        assert len(result) == 1
        assert result[0]['type'] == 'table'
        table = result[0]['table']
        assert table['table_width'] == 3
        assert table['has_column_header'] is True
        assert len(table['children']) == 5