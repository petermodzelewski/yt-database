"""
Video processing orchestrator.

This module contains the VideoProcessor class that coordinates all components
of the video processing pipeline: metadata extraction, summary generation,
and storage operations.
"""

from typing import Dict, Any, Optional
from ..interfaces.summary_writer import SummaryWriter
from ..interfaces.storage import Storage
from ..extractors.video_metadata_extractor import VideoMetadataExtractor
from ..utils.exceptions import (
    VideoProcessingError,
    ConfigurationError,
    MetadataExtractionError,
    SummaryGenerationError,
    StorageError
)


class VideoProcessor:
    """
    Main orchestrator that coordinates all video processing components.
    
    This class implements the complete video processing pipeline by coordinating
    three main components:
    1. VideoMetadataExtractor - for extracting video metadata from YouTube
    2. SummaryWriter - for generating AI-powered summaries
    3. Storage - for storing the processed results
    
    The processor ensures proper error handling, configuration validation,
    and maintains a clean separation of concerns between components.
    """
    
    def __init__(self, metadata_extractor: VideoMetadataExtractor,
                 summary_writer: SummaryWriter, storage: Storage):
        """
        Initialize the video processor with required components.
        
        Args:
            metadata_extractor: Component for extracting video metadata
            summary_writer: Component for generating summaries
            storage: Component for storing processed results
            
        Raises:
            ConfigurationError: If any component is None or invalid
        """
        if not metadata_extractor:
            raise ConfigurationError("VideoMetadataExtractor is required")
        if not summary_writer:
            raise ConfigurationError("SummaryWriter is required")
        if not storage:
            raise ConfigurationError("Storage is required")
        
        self.metadata_extractor = metadata_extractor
        self.summary_writer = summary_writer
        self.storage = storage
    
    def process_video(self, video_url: str, custom_prompt: Optional[str] = None) -> bool:
        """
        Process a video through the complete pipeline.
        
        This method orchestrates the complete video processing workflow:
        1. Extract metadata from the video URL
        2. Generate an AI summary using the metadata
        3. Store the results in the configured storage backend
        
        Args:
            video_url: YouTube URL to process
            custom_prompt: Optional custom prompt for summary generation
            
        Returns:
            bool: True if processing completed successfully, False otherwise
            
        Raises:
            VideoProcessingError: If any step in the pipeline fails
            MetadataExtractionError: If metadata extraction fails
            SummaryGenerationError: If summary generation fails
            StorageError: If storage operation fails
        """
        if not video_url or not isinstance(video_url, str):
            raise VideoProcessingError(
                "Video URL must be a non-empty string",
                details=f"Received: {type(video_url).__name__}"
            )
        
        try:
            # Step 1: Extract metadata
            metadata = self.metadata_extractor.extract_metadata(video_url)
            
            # Step 2: Generate summary
            summary = self.summary_writer.generate_summary(
                video_url, metadata, custom_prompt
            )
            
            # Step 3: Prepare data for storage
            video_data = {
                "Title": metadata.get("title", "Unknown Title"),
                "Channel": metadata.get("channel", "Unknown Channel"),
                "Video URL": video_url,
                "Cover": metadata.get("thumbnail_url", ""),
                "Summary": summary
            }
            
            # Add additional metadata if available
            if metadata.get("description"):
                video_data["Description"] = metadata["description"]
            if metadata.get("published_at"):
                video_data["Published"] = metadata["published_at"]
            if metadata.get("video_id"):
                video_data["Video ID"] = metadata["video_id"]
            
            # Step 4: Store results
            success = self.storage.store_video_summary(video_data)
            
            if not success:
                raise StorageError(
                    "Storage operation returned failure status",
                    details=f"Video: {metadata.get('title', 'Unknown')}"
                )
            
            return True
            
        except (MetadataExtractionError, SummaryGenerationError, StorageError):
            # Re-raise specific errors as-is
            raise
            
        except Exception as e:
            # Wrap unexpected errors in a general processing error
            raise VideoProcessingError(
                f"Unexpected error during video processing: {str(e)}",
                details=f"URL: {video_url}, Error type: {type(e).__name__}"
            )
    
    def validate_configuration(self) -> bool:
        """
        Validate all component configurations.
        
        This method validates that all components are properly configured
        and ready to process videos. It checks each component's configuration
        without performing actual operations.
        
        Returns:
            bool: True if all components are properly configured, False otherwise
            
        Raises:
            ConfigurationError: If configuration validation fails with details
        """
        validation_errors = []
        
        # Validate metadata extractor
        try:
            if not self.metadata_extractor.validate_configuration():
                validation_errors.append("VideoMetadataExtractor: configuration validation failed")
        except Exception as e:
            validation_errors.append(f"VideoMetadataExtractor: {str(e)}")
        
        # Validate summary writer
        try:
            if not self.summary_writer.validate_configuration():
                validation_errors.append("SummaryWriter: configuration validation failed")
        except Exception as e:
            validation_errors.append(f"SummaryWriter: {str(e)}")
        
        # Validate storage
        try:
            if not self.storage.validate_configuration():
                validation_errors.append("Storage: configuration validation failed")
        except Exception as e:
            validation_errors.append(f"Storage: {str(e)}")
        
        # If there are validation errors, raise an exception with details
        if validation_errors:
            raise ConfigurationError(
                "Component configuration validation failed",
                details="; ".join(validation_errors)
            )
        
        return True
    
    def get_component_info(self) -> Dict[str, str]:
        """
        Get information about the configured components.
        
        This method returns information about the current component configuration
        for debugging and logging purposes.
        
        Returns:
            dict: Information about each component including class names and status
        """
        info = {
            "metadata_extractor": type(self.metadata_extractor).__name__,
            "summary_writer": type(self.summary_writer).__name__,
            "storage": type(self.storage).__name__
        }
        
        # Add configuration status for each component
        try:
            self.validate_configuration()
            info["configuration_status"] = "valid"
        except ConfigurationError as e:
            info["configuration_status"] = f"invalid: {e.message}"
        except Exception as e:
            info["configuration_status"] = f"error: {str(e)}"
        
        return info