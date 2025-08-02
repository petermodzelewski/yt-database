"""
Integration test to verify the markdown converter works with EXAMPLE_DATA.
"""

from youtube_notion.utils.markdown_converter import markdown_to_notion_blocks
from youtube_notion.config.example_data import EXAMPLE_DATA


def test_example_data_conversion():
    """Test that EXAMPLE_DATA converts properly to Notion blocks."""
    summary = EXAMPLE_DATA["Summary"]
    blocks = markdown_to_notion_blocks(summary)
    
    print(f"Converted {len(blocks)} blocks from example data")
    
    # Check that we have blocks
    assert len(blocks) > 0, "Should have converted some blocks"
    
    # Check that we have different types of blocks
    block_types = {block["type"] for block in blocks}
    print(f"Block types found: {block_types}")
    
    # Should have headings, paragraphs, and lists
    expected_types = {"heading_3", "paragraph", "bulleted_list_item", "numbered_list_item"}
    assert expected_types.issubset(block_types), f"Missing expected block types. Found: {block_types}"
    
    # Check first block is a heading
    first_block = blocks[0]
    assert first_block["type"] == "heading_3", f"First block should be heading_3, got {first_block['type']}"
    
    print("✅ Integration test passed!")
    return blocks


if __name__ == "__main__":
    blocks = test_example_data_conversion()
    
    # Print first few blocks for inspection
    print("\nFirst 3 blocks:")
    for i, block in enumerate(blocks[:3]):
        print(f"{i+1}. Type: {block['type']}")
        if block['type'].startswith('heading'):
            content = block[block['type']]['rich_text'][0]['text']['content']
        else:
            content = block[block['type']]['rich_text'][0]['text']['content'][:50] + "..."
        print(f"   Content: {content}")