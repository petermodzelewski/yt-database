"""
End-to-end tests for timestamp enrichment and markdown conversion.
Tests the complete flow from timestamp enrichment to Notion blocks.
"""

import unittest
from youtube_notion.utils.markdown_converter import enrich_timestamps_with_links, markdown_to_notion_blocks


class TestEndToEndTimestamps(unittest.TestCase):
    """Test cases for complete timestamp processing flow."""
    
    def setUp(self):
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
        self.assertEqual(len(blocks), 2)  # Header and paragraph
        
        # Check header block
        header_block = blocks[0]
        self.assertEqual(header_block["type"], "heading_3")
        
        # Check that header has rich text with links
        header_rich_text = header_block["heading_3"]["rich_text"]
        self.assertGreater(len(header_rich_text), 1)  # Should have multiple parts
        
        # Find the link parts
        link_parts = [part for part in header_rich_text if "link" in part.get("text", {})]
        self.assertEqual(len(link_parts), 2)  # Should have 2 timestamp links
        
        # Verify first timestamp link
        first_link = link_parts[0]
        self.assertEqual(first_link["text"]["content"], "0:01-0:07")
        self.assertEqual(first_link["text"]["link"]["url"], "https://www.youtube.com/watch?v=pMSXPgAUq_k&t=1s")
        
        # Verify second timestamp link
        second_link = link_parts[1]
        self.assertEqual(second_link["text"]["content"], "0:56-1:21")
        self.assertEqual(second_link["text"]["link"]["url"], "https://www.youtube.com/watch?v=pMSXPgAUq_k&t=56s")
        
        # Check paragraph block
        paragraph_block = blocks[1]
        self.assertEqual(paragraph_block["type"], "paragraph")
        
        # Check that paragraph has rich text with link
        paragraph_rich_text = paragraph_block["paragraph"]["rich_text"]
        paragraph_link_parts = [part for part in paragraph_rich_text if "link" in part.get("text", {})]
        self.assertEqual(len(paragraph_link_parts), 1)  # Should have 1 timestamp link
        
        # Verify paragraph timestamp link
        paragraph_link = paragraph_link_parts[0]
        self.assertEqual(paragraph_link["text"]["content"], "8:05")
        self.assertEqual(paragraph_link["text"]["link"]["url"], "https://www.youtube.com/watch?v=pMSXPgAUq_k&t=485s")
    
    def test_mixed_formatting_with_timestamps(self):
        """Test timestamps with other markdown formatting."""
        markdown = "**Important**: See [8:05] for *key insights*."
        
        # Enrich and convert
        enriched = enrich_timestamps_with_links(markdown, self.video_url)
        blocks = markdown_to_notion_blocks(enriched)
        
        # Should have one paragraph block
        self.assertEqual(len(blocks), 1)
        paragraph_block = blocks[0]
        self.assertEqual(paragraph_block["type"], "paragraph")
        
        # Check rich text parts
        rich_text = paragraph_block["paragraph"]["rich_text"]
        
        # Should have: "Important" (bold), ": See ", "8:05" (link), " for ", "key insights" (italic), "."
        self.assertEqual(len(rich_text), 6)
        
        # Check bold part
        bold_part = rich_text[0]
        self.assertEqual(bold_part["text"]["content"], "Important")
        self.assertTrue(bold_part["annotations"]["bold"])
        
        # Check link part
        link_part = rich_text[2]
        self.assertEqual(link_part["text"]["content"], "8:05")
        self.assertEqual(link_part["text"]["link"]["url"], "https://www.youtube.com/watch?v=pMSXPgAUq_k&t=485s")
        
        # Check italic part
        italic_part = rich_text[4]
        self.assertEqual(italic_part["text"]["content"], "key insights")
        self.assertTrue(italic_part["annotations"]["italic"])
    
    def test_no_timestamps_unchanged(self):
        """Test that content without timestamps works normally."""
        markdown = "# Regular Header\n\nThis is **bold** and *italic* text."
        
        # Enrich (should be unchanged)
        enriched = enrich_timestamps_with_links(markdown, self.video_url)
        self.assertEqual(enriched, markdown)
        
        # Convert to blocks
        blocks = markdown_to_notion_blocks(enriched)
        
        # Should have header and paragraph
        self.assertEqual(len(blocks), 2)
        self.assertEqual(blocks[0]["type"], "heading_1")
        self.assertEqual(blocks[1]["type"], "paragraph")
        
        # Check that formatting is preserved
        paragraph_rich_text = blocks[1]["paragraph"]["rich_text"]
        bold_parts = [part for part in paragraph_rich_text if part.get("annotations", {}).get("bold")]
        italic_parts = [part for part in paragraph_rich_text if part.get("annotations", {}).get("italic")]
        
        self.assertEqual(len(bold_parts), 1)
        self.assertEqual(len(italic_parts), 1)
        self.assertEqual(bold_parts[0]["text"]["content"], "bold")
        self.assertEqual(italic_parts[0]["text"]["content"], "italic")


if __name__ == '__main__':
    unittest.main()