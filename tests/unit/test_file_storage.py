"""
Unit tests for the FileStorage implementation.
"""

import os
import shutil
import pytest
from unittest.mock import mock_open, patch

from src.youtube_notion.storage.file_storage import FileStorage
from src.youtube_notion.utils.exceptions import ConfigurationError, StorageError


@pytest.fixture
def temp_output_dir(tmp_path):
    """Create a temporary output directory for tests."""
    return tmp_path / "output"


@pytest.fixture
def file_storage(temp_output_dir):
    """Return a FileStorage instance with a temporary output directory."""
    return FileStorage(output_dir=str(temp_output_dir))


@pytest.fixture
def video_data():
    """Return sample video data for testing."""
    return {
        "Title": "Test Video Title",
        "Channel": "Test Channel",
        "Summary": "This is a test summary."
    }


def test_file_storage_initialization(temp_output_dir):
    """Test that FileStorage initializes correctly."""
    storage = FileStorage(output_dir=str(temp_output_dir))
    assert storage.output_dir == str(temp_output_dir)
    assert storage.use_channel_subdirectory is True


def test_file_storage_initialization_with_empty_dir_raises_error():
    """Test that FileStorage raises ConfigurationError with empty output_dir."""
    with pytest.raises(ConfigurationError):
        FileStorage(output_dir="")


def test_store_video_summary_creates_file_and_subdir(file_storage, video_data, temp_output_dir):
    """Test that store_video_summary creates a file in a channel-specific subdirectory."""
    file_storage.store_video_summary(video_data)

    channel_dir = temp_output_dir / "Test Channel"
    assert channel_dir.exists()
    assert channel_dir.is_dir()

    output_file = channel_dir / "Test Video Title.md"
    assert output_file.exists()
    assert output_file.is_file()

    with open(output_file, 'r') as f:
        content = f.read()
        assert content == video_data["Summary"]


def test_store_video_summary_without_channel_subdir(temp_output_dir, video_data):
    """Test that store_video_summary creates a file directly in the output dir if specified."""
    storage = FileStorage(output_dir=str(temp_output_dir), use_channel_subdirectory=False)
    storage.store_video_summary(video_data)

    output_file = temp_output_dir / "Test Video Title.md"
    assert output_file.exists()

    channel_dir = temp_output_dir / "Test Channel"
    assert not channel_dir.exists()


def test_store_video_summary_sanitizes_filenames(file_storage, video_data, temp_output_dir):
    """Test that filenames are sanitized correctly."""
    video_data["Title"] = "Invalid:/\\?*<>:|\"Title"
    video_data["Channel"] = "Invalid/\\?*<>:|\"Channel"

    file_storage.store_video_summary(video_data)

    channel_dir = temp_output_dir / "Invalid_________Channel"
    assert channel_dir.exists()

    output_file = channel_dir / "Invalid__________Title.md"
    assert output_file.exists()


def test_store_video_summary_missing_fields_raises_error(file_storage):
    """Test that StorageError is raised if required fields are missing."""
    with pytest.raises(StorageError):
        file_storage.store_video_summary({"Title": "Test"})


def test_validate_configuration_success(file_storage):
    """Test that validate_configuration returns True for a valid configuration."""
    assert file_storage.validate_configuration() is True


def test_validate_configuration_creates_directory(temp_output_dir):
    """Test that validate_configuration creates the output directory if it doesn't exist."""
    # Ensure the directory does not exist initially
    if os.path.exists(temp_output_dir):
        shutil.rmtree(temp_output_dir)
    assert not os.path.exists(temp_output_dir)

    storage = FileStorage(output_dir=str(temp_output_dir))
    storage.validate_configuration()
    assert temp_output_dir.exists()


def test_validate_configuration_unwritable_dir_raises_error(temp_output_dir):
    """Test that ConfigurationError is raised for an unwritable directory."""
    os.makedirs(temp_output_dir, exist_ok=True)
    os.chmod(temp_output_dir, 0o444)  # Read-only
    storage = FileStorage(output_dir=str(temp_output_dir))
    with pytest.raises(ConfigurationError):
        storage.validate_configuration()
    os.chmod(temp_output_dir, 0o755)  # Restore permissions


def test_find_target_location(file_storage, temp_output_dir):
    """Test that find_target_location returns the output directory."""
    assert file_storage.find_target_location() == str(temp_output_dir)


@patch("os.makedirs")
def test_store_video_summary_os_error_raises_storage_error(mock_makedirs, file_storage, video_data):
    """Test that an OSError during directory creation is wrapped in StorageError."""
    mock_makedirs.side_effect = OSError("Test OS Error")
    with pytest.raises(StorageError):
        file_storage.store_video_summary(video_data)

@patch("builtins.open", new_callable=mock_open)
def test_store_video_summary_write_error_raises_storage_error(mock_file, file_storage, video_data):
    """Test that an error during file writing is wrapped in StorageError."""
    mock_file.side_effect = IOError("Test Write Error")
    with pytest.raises(StorageError):
        file_storage.store_video_summary(video_data)