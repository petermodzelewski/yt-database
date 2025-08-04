"""
Unit tests for abstract interfaces.

This module tests the interface contracts to ensure they define the expected
methods and behavior for implementations.
"""

import pytest
from abc import ABC
from typing import Dict, Any, Optional

from src.youtube_notion.interfaces import SummaryWriter, Storage


class TestSummaryWriterInterface:
    """Test the SummaryWriter abstract interface."""
    
    def test_is_abstract_base_class(self):
        """Test that SummaryWriter is an abstract base class."""
        assert issubclass(SummaryWriter, ABC)
        
        # Should not be able to instantiate directly
        with pytest.raises(TypeError):
            SummaryWriter()
    
    def test_has_required_methods(self):
        """Test that SummaryWriter defines required abstract methods."""
        # Check that abstract methods are defined
        abstract_methods = SummaryWriter.__abstractmethods__
        expected_methods = {'generate_summary', 'validate_configuration'}
        assert abstract_methods == expected_methods
    
    def test_generate_summary_signature(self):
        """Test that generate_summary has the correct signature."""
        method = SummaryWriter.generate_summary
        
        # Check method exists and is abstract
        assert hasattr(SummaryWriter, 'generate_summary')
        assert method.__isabstractmethod__
    
    def test_validate_configuration_signature(self):
        """Test that validate_configuration has the correct signature."""
        method = SummaryWriter.validate_configuration
        
        # Check method exists and is abstract
        assert hasattr(SummaryWriter, 'validate_configuration')
        assert method.__isabstractmethod__


class TestStorageInterface:
    """Test the Storage abstract interface."""
    
    def test_is_abstract_base_class(self):
        """Test that Storage is an abstract base class."""
        assert issubclass(Storage, ABC)
        
        # Should not be able to instantiate directly
        with pytest.raises(TypeError):
            Storage()
    
    def test_has_required_methods(self):
        """Test that Storage defines required abstract methods."""
        # Check that abstract methods are defined
        abstract_methods = Storage.__abstractmethods__
        expected_methods = {'store_video_summary', 'validate_configuration', 'find_target_location'}
        assert abstract_methods == expected_methods
    
    def test_store_video_summary_signature(self):
        """Test that store_video_summary has the correct signature."""
        method = Storage.store_video_summary
        
        # Check method exists and is abstract
        assert hasattr(Storage, 'store_video_summary')
        assert method.__isabstractmethod__
    
    def test_validate_configuration_signature(self):
        """Test that validate_configuration has the correct signature."""
        method = Storage.validate_configuration
        
        # Check method exists and is abstract
        assert hasattr(Storage, 'validate_configuration')
        assert method.__isabstractmethod__
    
    def test_find_target_location_signature(self):
        """Test that find_target_location has the correct signature."""
        method = Storage.find_target_location
        
        # Check method exists and is abstract
        assert hasattr(Storage, 'find_target_location')
        assert method.__isabstractmethod__


class MockSummaryWriter(SummaryWriter):
    """Mock implementation for testing interface compliance."""
    
    def generate_summary(self, video_url: str, video_metadata: Dict[str, Any], 
                        custom_prompt: Optional[str] = None) -> str:
        return "Mock summary"
    
    def validate_configuration(self) -> bool:
        return True


class MockStorage(Storage):
    """Mock implementation for testing interface compliance."""
    
    def store_video_summary(self, video_data: Dict[str, Any]) -> bool:
        return True
    
    def validate_configuration(self) -> bool:
        return True
    
    def find_target_location(self) -> Optional[str]:
        return "mock-location"


class TestInterfaceImplementations:
    """Test that interfaces can be properly implemented."""
    
    def test_summary_writer_implementation(self):
        """Test that SummaryWriter can be implemented."""
        writer = MockSummaryWriter()
        
        # Test method calls
        summary = writer.generate_summary("https://youtube.com/watch?v=test", {"title": "Test"})
        assert summary == "Mock summary"
        
        config_valid = writer.validate_configuration()
        assert config_valid is True
    
    def test_storage_implementation(self):
        """Test that Storage can be implemented."""
        storage = MockStorage()
        
        # Test method calls
        stored = storage.store_video_summary({"title": "Test Video"})
        assert stored is True
        
        config_valid = storage.validate_configuration()
        assert config_valid is True
        
        location = storage.find_target_location()
        assert location == "mock-location"