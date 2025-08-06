"""
Essential Gemini AI integration test for YouTube-to-Notion system.

This module contains only the essential happy path test for Gemini AI integration.
"""

import pytest
from src.youtube_notion.config.factory import ComponentFactory


@pytest.mark.integration
class TestGeminiIntegration:
    """Essential Gemini AI integration test - happy path only."""
    
    def test_gemini_summary_generation_happy_path(self, integration_config):
        """Test Gemini AI summary generation happy path with real API."""
        # Create Gemini summary writer from environment
        factory = ComponentFactory.from_environment(youtube_mode=True)
        writer = factory.create_summary_writer()
        
        # Test data
        test_video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        test_metadata = {
            "title": "Rick Astley - Never Gonna Give You Up",
            "description": "The official video for Rick Astley's 1987 hit song Never Gonna Give You Up",
            "channel": "Rick Astley",
            "video_id": "dQw4w9WgXcQ"
        }
        
        # Generate summary
        summary = writer.generate_summary(test_video_url, test_metadata)
        
        # Verify summary was generated successfully
        assert isinstance(summary, str)
        assert len(summary) > 0
        
        # Verify summary contains expected markdown formatting
        assert "#" in summary or "**" in summary or "*" in summary, "Summary should contain markdown formatting"
        
        # Verify summary is substantial (not just a short error message)
        assert len(summary) > 50, "Summary should be substantial content"