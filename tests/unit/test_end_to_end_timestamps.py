"""
End-to-end tests for timestamp enrichment and markdown conversion.
Tests the complete flow from timestamp enrichment to Notion blocks.
"""

from youtube_notion.utils.markdown_converter import enrich_timestamps_with_links, markdown_to_notion_blocks


class TestEndToEndTimestamps:
    """Test cases for complete timestamp processing flow."""
    
    def setup_method(self):
        self.video_url = "https://www.youtube.com/watch?v=pMSXPgAUq_k"
    
    def test_timestamp_enrichment_to_notion_blocks(self):
        """Test complete flow from timestamp enrichment to Notion blocks."""
        # Original markdown with timestamps
        markdown = "#### The High Cost of Bad Chunking [0:01-0:07, 0:56-1:21]\n\nThis section covers important concepts at [8:05]."
        
        # Step 1: Enrich timestamps
        enriched = enrich_timestamps_with_links(markdown, self.video_url)
        
        # Step 2: Convert to Notion blocks
        blocks = markdown_to_notion_blocks(enriched)
        
        # Verify we have the expected blocks
        assert len(blocks) == 2  # Header and paragraph
        
        # Check header block
        header_block = blocks[0]
        assert header_block["type"] == "heading_3"
        
        # Check that header has rich text with links
        header_rich_text = header_block["heading_3"]["rich_text"]
        assert len(header_rich_text) > 1  # Should have multiple parts
        
        # Find the link parts
        link_parts = [part for part in header_rich_text if "link" in part.get("text", {})]
        assert len(link_parts) == 2  # Should have 2 timestamp links
        
        # Verify first timestamp link
        first_link = link_parts[0]
        assert first_link["text"]["content"] == "0:01-0:07"
        assert first_link["text"]["link"]["url"] == "https://www.youtube.com/watch?v=pMSXPgAUq_k&t=1s"
        
        # Verify second timestamp link
        second_link = link_parts[1]
        assert second_link["text"]["content"] == "0:56-1:21"
        assert second_link["text"]["link"]["url"] == "https://www.youtube.com/watch?v=pMSXPgAUq_k&t=56s"
        
        # Check paragraph block
        paragraph_block = blocks[1]
        assert paragraph_block["type"] == "paragraph"
        
        # Check that paragraph has rich text with link
        paragraph_rich_text = paragraph_block["paragraph"]["rich_text"]
        paragraph_link_parts = [part for part in paragraph_rich_text if "link" in part.get("text", {})]
        assert len(paragraph_link_parts) == 1  # Should have 1 timestamp link
        
        # Verify paragraph timestamp link
        paragraph_link = paragraph_link_parts[0]
        assert paragraph_link["text"]["content"] == "8:05"
        assert paragraph_link["text"]["link"]["url"] == "https://www.youtube.com/watch?v=pMSXPgAUq_k&t=485s"
    
    def test_mixed_formatting_with_timestamps(self):
        """Test timestamps with other markdown formatting."""
        markdown = "**Important**: See [8:05] for *key insights*."
        
        # Enrich and convert
        enriched = enrich_timestamps_with_links(markdown, self.video_url)
        blocks = markdown_to_notion_blocks(enriched)
        
        # Should have one paragraph block
        assert len(blocks) == 1
        paragraph_block = blocks[0]
        assert paragraph_block["type"] == "paragraph"
        
        # Check rich text parts
        rich_text = paragraph_block["paragraph"]["rich_text"]
        
        # Should have: "Important" (bold), ": See ", "8:05" (link), " for ", "key insights" (italic), "."
        assert len(rich_text) == 6
        
        # Check bold part
        bold_part = rich_text[0]
        assert bold_part["text"]["content"] == "Important"
        assert bold_part["annotations"]["bold"] is True
        
        # Check link part
        link_part = rich_text[2]
        assert link_part["text"]["content"] == "8:05"
        assert link_part["text"]["link"]["url"] == "https://www.youtube.com/watch?v=pMSXPgAUq_k&t=485s"
        
        # Check italic part
        italic_part = rich_text[4]
        assert italic_part["text"]["content"] == "key insights"
        assert italic_part["annotations"]["italic"] is True
    
    def test_no_timestamps_unchanged(self):
        """Test that content without timestamps works normally."""
        markdown = "# Regular Header\n\nThis is **bold** and *italic* text."
        
        # Enrich (should be unchanged)
        enriched = enrich_timestamps_with_links(markdown, self.video_url)
        assert enriched == markdown
        
        # Convert to blocks
        blocks = markdown_to_notion_blocks(enriched)
        
        # Should have header and paragraph
        assert len(blocks) == 2
        assert blocks[0]["type"] == "heading_1"
        assert blocks[1]["type"] == "paragraph"
        
        # Check that formatting is preserved
        paragraph_rich_text = blocks[1]["paragraph"]["rich_text"]
        bold_parts = [part for part in paragraph_rich_text if part.get("annotations", {}).get("bold")]
        italic_parts = [part for part in paragraph_rich_text if part.get("annotations", {}).get("italic")]
        
        assert len(bold_parts) == 1
        assert len(italic_parts) == 1
        assert bold_parts[0]["text"]["content"] == "bold"
        assert italic_parts[0]["text"]["content"] == "italic"