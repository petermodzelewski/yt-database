"""
Unit tests for the MultiStorage implementation.
"""

import pytest
from unittest.mock import MagicMock

from src.youtube_notion.storage.multi_storage import MultiStorage
from src.youtube_notion.interfaces.storage import Storage
from src.youtube_notion.utils.exceptions import StorageError, ConfigurationError


@pytest.fixture
def mock_storage_one():
    """Return a mock storage backend."""
    storage = MagicMock(spec=Storage)
    storage.store_video_summary.return_value = True
    storage.validate_configuration.return_value = True
    storage.find_target_location.return_value = "/target/one"
    return storage


@pytest.fixture
def mock_storage_two():
    """Return another mock storage backend."""
    storage = MagicMock(spec=Storage)
    storage.store_video_summary.return_value = True
    storage.validate_configuration.return_value = True
    storage.find_target_location.return_value = "/target/two"
    return storage


@pytest.fixture
def video_data():
    """Return sample video data for testing."""
    return {"Title": "Test", "Summary": "Test summary"}


def test_multi_storage_initialization(mock_storage_one, mock_storage_two):
    """Test that MultiStorage initializes with a list of storages."""
    multi_storage = MultiStorage(storages=[mock_storage_one, mock_storage_two])
    assert len(multi_storage.storages) == 2
    assert multi_storage.storages[0] == mock_storage_one
    assert multi_storage.storages[1] == mock_storage_two


def test_store_video_summary_success(mock_storage_one, mock_storage_two, video_data):
    """Test that store_video_summary calls all contained storages on success."""
    multi_storage = MultiStorage(storages=[mock_storage_one, mock_storage_two])
    result = multi_storage.store_video_summary(video_data)

    assert result is True
    mock_storage_one.store_video_summary.assert_called_once_with(video_data)
    mock_storage_two.store_video_summary.assert_called_once_with(video_data)


def test_store_video_summary_one_backend_fails_raises_error(mock_storage_one, mock_storage_two, video_data):
    """Test that StorageError is raised if one of the backends fails."""
    mock_storage_two.store_video_summary.side_effect = StorageError("Test failure")

    multi_storage = MultiStorage(storages=[mock_storage_one, mock_storage_two])

    with pytest.raises(StorageError) as excinfo:
        multi_storage.store_video_summary(video_data)

    # Ensure the successful backend was still called
    mock_storage_one.store_video_summary.assert_called_once_with(video_data)
    assert "One or more storage backends failed" in str(excinfo.value)
    assert "MagicMock: Test failure" in str(excinfo.value)


def test_validate_configuration_success(mock_storage_one, mock_storage_two):
    """Test that validate_configuration calls all contained storages."""
    multi_storage = MultiStorage(storages=[mock_storage_one, mock_storage_two])
    result = multi_storage.validate_configuration()

    assert result is True
    mock_storage_one.validate_configuration.assert_called_once()
    mock_storage_two.validate_configuration.assert_called_once()


def test_validate_configuration_one_backend_fails_raises_error(mock_storage_one, mock_storage_two):
    """Test that ConfigurationError is raised if one backend's validation fails."""
    mock_storage_one.validate_configuration.side_effect = ConfigurationError("Bad config")

    multi_storage = MultiStorage(storages=[mock_storage_one, mock_storage_two])

    with pytest.raises(ConfigurationError):
        multi_storage.validate_configuration()

    # The second backend's validate should not be called if the first one fails
    mock_storage_two.validate_configuration.assert_not_called()


def test_find_target_location(mock_storage_one, mock_storage_two):
    """Test that find_target_location aggregates locations from all backends."""
    multi_storage = MultiStorage(storages=[mock_storage_one, mock_storage_two])
    locations = multi_storage.find_target_location()

    assert locations == "/target/one, /target/two"
    mock_storage_one.find_target_location.assert_called_once()
    mock_storage_two.find_target_location.assert_called_once()


def test_find_target_location_one_is_none(mock_storage_one, mock_storage_two):
    """Test that find_target_location handles one backend returning None."""
    mock_storage_two.find_target_location.return_value = None
    multi_storage = MultiStorage(storages=[mock_storage_one, mock_storage_two])
    locations = multi_storage.find_target_location()

    assert locations == "/target/one"

def test_store_video_summary_with_no_storages(video_data):
    """Test that storing with no backends does nothing and returns True."""
    multi_storage = MultiStorage(storages=[])
    assert multi_storage.store_video_summary(video_data) is True