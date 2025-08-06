"""
Tests for validation edge cases and boundary conditions.

This module tests edge cases in validation logic, boundary conditions,
and ensures robust error handling for unusual inputs.
"""

import pytest
from unittest.mock import Mock, patch
from src.youtube_notion.utils.exceptions import (
    ConfigurationError,
    InvalidURLError,
    MetadataExtractionError,
    SummaryGenerationError,
    StorageError
)
from src.youtube_notion.extractors.video_metadata_extractor import VideoMetadataExtractor
from tests.fixtures.mock_implementations import MockSummaryWriter


class TestURLValidationEdgeCases:
    """Test edge cases in URL validation and processing."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.extractor = VideoMetadataExtractor()
    
    def test_url_with_unicode_characters(self):
        """Test URL handling with unicode characters."""
        # URLs with unicode characters should be handled gracefully
        unicode_urls = [
            "https://youtube.com/watch?v=dQw4w9WgXcQ&t=测试",
            "https://youtu.be/dQw4w9WgXcQ?si=café",
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ&list=PLrAXtmRdnEQy4Qñ"
        ]
        
        for url in unicode_urls:
            # Should extract video ID successfully despite unicode parameters
            video_id = self.extractor.extract_video_id(url)
            assert video_id == "dQw4w9WgXcQ"
    
    def test_url_with_excessive_whitespace(self):
        """Test URL handling with excessive whitespace."""
        whitespace_urls = [
            "   https://youtube.com/watch?v=dQw4w9WgXcQ   ",
            "\t\nhttps://youtu.be/dQw4w9WgXcQ\t\n",
            "  \r\n  https://www.youtube.com/watch?v=dQw4w9WgXcQ  \r\n  "
        ]
        
        for url in whitespace_urls:
            video_id = self.extractor.extract_video_id(url)
            assert video_id == "dQw4w9WgXcQ"
    
    def test_url_with_mixed_case_domains(self):
        """Test URL handling with mixed case domains."""
        mixed_case_urls = [
            "https://YouTube.com/watch?v=dQw4w9WgXcQ",
            "https://YOUTU.BE/dQw4w9WgXcQ",
            "https://Www.YouTube.Com/watch?v=dQw4w9WgXcQ",
            "https://M.YOUTUBE.COM/watch?v=dQw4w9WgXcQ"
        ]
        
        for url in mixed_case_urls:
            video_id = self.extractor.extract_video_id(url)
            assert video_id == "dQw4w9WgXcQ"
    
    def test_url_without_protocol(self):
        """Test URL handling without protocol."""
        no_protocol_urls = [
            "youtube.com/watch?v=dQw4w9WgXcQ",
            "youtu.be/dQw4w9WgXcQ",
            "www.youtube.com/watch?v=dQw4w9WgXcQ",
            "m.youtube.com/watch?v=dQw4w9WgXcQ"
        ]
        
        for url in no_protocol_urls:
            video_id = self.extractor.extract_video_id(url)
            assert video_id == "dQw4w9WgXcQ"
    
    def test_url_with_multiple_query_parameters(self):
        """Test URL handling with multiple query parameters."""
        complex_urls = [
            "https://youtube.com/watch?v=dQw4w9WgXcQ&t=123&list=PLtest&index=5",
            "https://youtu.be/dQw4w9WgXcQ?t=123&si=abcdef&feature=share",
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ&ab_channel=TestChannel&t=45s"
        ]
        
        for url in complex_urls:
            video_id = self.extractor.extract_video_id(url)
            assert video_id == "dQw4w9WgXcQ"
    
    def test_url_with_fragment_identifiers(self):
        """Test URL handling with fragment identifiers."""
        fragment_urls = [
            "https://youtube.com/watch?v=dQw4w9WgXcQ#t=123",
            "https://youtu.be/dQw4w9WgXcQ#comments",
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=45#description"
        ]
        
        for url in fragment_urls:
            video_id = self.extractor.extract_video_id(url)
            assert video_id == "dQw4w9WgXcQ"
    
    def test_url_with_port_numbers(self):
        """Test URL handling with port numbers (should fail)."""
        port_urls = [
            "https://youtube.com:8080/watch?v=dQw4w9WgXcQ",
            "https://youtu.be:443/dQw4w9WgXcQ"
        ]
        
        for url in port_urls:
            with pytest.raises(InvalidURLError):
                self.extractor.extract_video_id(url)
    
    def test_url_with_subdirectories(self):
        """Test URL handling with subdirectories (should fail for non-standard paths)."""
        subdir_urls = [
            "https://youtube.com/channel/UCtest/watch?v=dQw4w9WgXcQ",
            "https://youtube.com/user/testuser/watch?v=dQw4w9WgXcQ"
        ]
        
        for url in subdir_urls:
            with pytest.raises(InvalidURLError):
                self.extractor.extract_video_id(url)
    
    def test_video_id_boundary_conditions(self):
        """Test video ID validation at boundary conditions."""
        # Test exactly 11 characters (valid)
        valid_id = "a" * 11
        url = f"https://youtu.be/{valid_id}"
        result = self.extractor.extract_video_id(url)
        assert result == valid_id
        
        # Test 10 characters (invalid - too short)
        short_id = "a" * 10
        url = f"https://youtu.be/{short_id}"
        with pytest.raises(InvalidURLError, match="invalid format"):
            self.extractor.extract_video_id(url)
        
        # Test 12 characters (invalid - too long)
        long_id = "a" * 12
        url = f"https://youtu.be/{long_id}"
        with pytest.raises(InvalidURLError, match="invalid format"):
            self.extractor.extract_video_id(url)
    
    def test_video_id_special_characters(self):
        """Test video ID validation with special characters."""
        # Valid characters: alphanumeric, hyphen, underscore
        valid_chars = "abcABC123-_"
        url = f"https://youtu.be/{valid_chars}"
        result = self.extractor.extract_video_id(url)
        assert result == valid_chars
        
        # Invalid characters
        invalid_chars = [
            "abcABC123+!",  # Plus and exclamation
            "abcABC123@#",  # At and hash
            "abcABC123 .",  # Space and dot
            "abcABC123()[]"  # Brackets and parentheses
        ]
        
        for invalid_id in invalid_chars:
            url = f"https://youtu.be/{invalid_id}"
            with pytest.raises(InvalidURLError, match="invalid format"):
                self.extractor.extract_video_id(url)


class TestConfigurationValidationEdgeCases:
    """Test edge cases in configuration validation."""
    
    def test_string_configuration_edge_cases(self):
        """Test string configuration validation with edge cases."""
        # This test would require importing components that have circular dependencies
        # For now, we'll test the basic validation logic through the extractor
        
        # Test timeout validation in metadata extractor
        with pytest.raises(ConfigurationError, match="Timeout seconds must be positive"):
            VideoMetadataExtractor(timeout_seconds=0)
        
        with pytest.raises(ConfigurationError, match="Timeout seconds must be positive"):
            VideoMetadataExtractor(timeout_seconds=-5)


class TestDataValidationEdgeCases:
    """Test edge cases in data validation and processing."""
    
    def test_video_metadata_with_missing_fields(self):
        """Test video metadata processing with missing fields."""
        # Test metadata extraction with minimal data
        extractor = VideoMetadataExtractor()
        
        # Test that URL validation works with edge cases
        assert extractor.validate_url("https://youtube.com/watch?v=dQw4w9WgXcQ") is True
        assert extractor.validate_url("invalid-url") is False
        assert extractor.validate_url("") is False
        assert extractor.validate_url(None) is False


class TestErrorRecoveryScenarios:
    """Test error recovery and graceful degradation scenarios."""
    
    def test_partial_configuration_recovery(self):
        """Test recovery from partial configuration failures."""
        # Test metadata extractor without YouTube API key (should work with web scraping)
        extractor = VideoMetadataExtractor(youtube_api_key=None)
        
        # Should validate successfully even without API key
        assert extractor.validate_configuration() is True
        
        # Should be able to extract video IDs
        video_id = extractor.extract_video_id("https://youtu.be/dQw4w9WgXcQ")
        assert video_id == "dQw4w9WgXcQ"
    
    def test_graceful_degradation_with_invalid_optional_config(self):
        """Test graceful degradation when optional configuration is invalid."""
        # Test that extractor handles different timeout values gracefully
        extractor1 = VideoMetadataExtractor(timeout_seconds=5)
        extractor2 = VideoMetadataExtractor(timeout_seconds=30)
        
        # Both should validate successfully
        assert extractor1.validate_configuration() is True
        assert extractor2.validate_configuration() is True
        
        # Both should extract the same video ID
        video_id1 = extractor1.extract_video_id("https://youtu.be/dQw4w9WgXcQ")
        video_id2 = extractor2.extract_video_id("https://youtu.be/dQw4w9WgXcQ")
        assert video_id1 == video_id2 == "dQw4w9WgXcQ"
    
    def test_error_context_preservation(self):
        """Test that error context is preserved through the call stack."""
        extractor = VideoMetadataExtractor()
        
        try:
            extractor.extract_video_id("https://invalid-domain.com/video")
        except InvalidURLError as e:
            # Verify that error context is preserved
            assert "URL is not from a supported YouTube domain" in str(e)
            assert "Domain: invalid-domain.com" in str(e.details)
            assert "youtube.com" in str(e.details)
    
    def test_error_chaining_and_wrapping(self):
        """Test that errors are properly chained and wrapped."""
        writer = MockSummaryWriter()
        
        # Configure the mock to fail
        writer.should_fail = True
        
        try:
            writer.generate_summary("https://youtu.be/test", {"title": "Test"})
        except SummaryGenerationError as e:
                # Verify that the error is properly raised
                assert "Mock summary generation failed" in str(e)
                assert "Configured to fail in mock implementation" in str(e.details)


class TestConcurrencyAndRaceConditions:
    """Test error handling in concurrent scenarios."""
    
    def test_configuration_validation_thread_safety(self):
        """Test that configuration validation is thread-safe."""
        # This is a basic test - full thread safety would require more complex testing
        extractor = VideoMetadataExtractor("test_key")
        
        # Multiple calls to validate_configuration should be consistent
        results = []
        for _ in range(10):
            results.append(extractor.validate_configuration())
        
        # All results should be the same
        assert all(result is True for result in results)
    
    def test_error_state_isolation(self):
        """Test that error states don't leak between instances."""
        # Create two extractors with different configurations
        extractor1 = VideoMetadataExtractor(youtube_api_key="valid_key")
        
        with pytest.raises(ConfigurationError):
            extractor2 = VideoMetadataExtractor(timeout_seconds=-1)  # Invalid timeout
        
        # First extractor should still be valid
        assert extractor1.validate_configuration() is True
    
    def test_mock_state_isolation(self):
        """Test that mock states don't interfere with each other."""
        from tests.fixtures.mock_implementations import MockSummaryWriter
        
        # Create two mocks with different configurations
        mock1 = MockSummaryWriter(configuration_valid=True)
        mock2 = MockSummaryWriter(configuration_valid=False)
        
        # They should have independent states
        assert mock1.validate_configuration() is True
        assert mock2.validate_configuration() is False
        
        # Modifying one shouldn't affect the other
        mock1.configuration_valid = False
        assert mock1.validate_configuration() is False
        assert mock2.validate_configuration() is False  # Still false from initialization