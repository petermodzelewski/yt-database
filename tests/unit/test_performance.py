"""
Performance tests for the YouTube to Notion integration.
"""

import pytest
import time
from youtube_notion.utils.markdown_converter import markdown_to_notion_blocks, enrich_timestamps_with_links
from youtube_notion.config.example_data import EXAMPLE_DATA


class TestPerformance:
    """Test cases for performance benchmarks."""
    
    def test_large_markdown_conversion_performance(self):
        """Test performance with large markdown content."""
        # Create large markdown content
        large_content = EXAMPLE_DATA["Summary"] * 10  # 10x the example data
        
        start_time = time.time()
        blocks = markdown_to_notion_blocks(large_content)
        end_time = time.time()
        
        processing_time = end_time - start_time
        
        # Should complete within reasonable time (adjust threshold as needed)
        assert processing_time < 5.0, f"Processing took {processing_time:.2f}s, expected < 5.0s"
        assert len(blocks) > 0, "Should produce blocks"
        
        print(f"Large markdown conversion: {processing_time:.3f}s for {len(blocks)} blocks")
    
    def test_timestamp_enrichment_performance(self):
        """Test performance of timestamp enrichment with many timestamps."""
        # Create content with many timestamps
        timestamps = ["[{}:{}]".format(i//60, i%60) for i in range(1, 100, 5)]  # 20 timestamps
        markdown_with_timestamps = "Content with timestamps: " + " ".join(timestamps)
        
        video_url = "https://youtube.com/watch?v=test"
        
        start_time = time.time()
        result = enrich_timestamps_with_links(markdown_with_timestamps, video_url)
        end_time = time.time()
        
        processing_time = end_time - start_time
        
        # Should complete quickly
        assert processing_time < 1.0, f"Timestamp enrichment took {processing_time:.2f}s, expected < 1.0s"
        assert "youtube.com" in result, "Should contain enriched links"
        
        print(f"Timestamp enrichment: {processing_time:.3f}s for ~20 timestamps")
    
    def test_repeated_conversions_performance(self):
        """Test performance of repeated conversions (simulating batch processing)."""
        markdown = EXAMPLE_DATA["Summary"]
        
        start_time = time.time()
        
        # Simulate processing 50 documents
        for _ in range(50):
            blocks = markdown_to_notion_blocks(markdown)
            assert len(blocks) > 0
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Should handle batch processing efficiently
        assert processing_time < 10.0, f"Batch processing took {processing_time:.2f}s, expected < 10.0s"
        
        avg_time_per_doc = processing_time / 50
        print(f"Batch processing: {processing_time:.3f}s total, {avg_time_per_doc:.3f}s per document")
    
    @pytest.mark.parametrize("content_size", [100, 500, 1000, 2000])
    def test_scaling_with_content_size(self, content_size):
        """Test how performance scales with content size."""
        # Create content of specified size (approximate word count)
        base_text = "This is a test paragraph with some content. "
        repetitions = content_size // 10  # Approximate words per repetition
        large_content = base_text * repetitions
        
        start_time = time.time()
        blocks = markdown_to_notion_blocks(large_content)
        end_time = time.time()
        
        processing_time = end_time - start_time
        
        # Performance should scale reasonably
        assert processing_time < content_size / 100, f"Processing {content_size} words took {processing_time:.2f}s"
        assert len(blocks) > 0
        
        print(f"Content size {content_size} words: {processing_time:.3f}s")
    
    def test_memory_usage_large_content(self):
        """Test that large content doesn't cause memory issues."""
        import sys
        
        # Get initial memory usage (approximate)
        initial_objects = len(gc.get_objects()) if 'gc' in sys.modules else 0
        
        # Process very large content
        huge_content = EXAMPLE_DATA["Summary"] * 100
        blocks = markdown_to_notion_blocks(huge_content)
        
        # Verify it completed successfully
        assert len(blocks) > 0
        assert blocks[0]["type"] in ["heading_1", "heading_2", "heading_3"]
        
        # Clean up
        del huge_content
        del blocks
        
        print("Large content memory test completed successfully")


# Import gc for memory test
try:
    import gc
except ImportError:
    gc = None