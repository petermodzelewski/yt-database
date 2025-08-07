import pytest
from src.youtube_notion.utils.video_utils import parse_iso8601_duration, calculate_video_splits

@pytest.mark.parametrize(
    "duration_str, expected_seconds",
    [
        ("PT1H2M3S", 3723),
        ("PT1M", 60),
        ("PT1S", 1),
        ("P1DT12H", 129600),
        ("PT0S", 0),
        ("", 0),
        (None, 0),
        ("P1Y", 31536000),
        ("P1M", 2592000),
        ("P1W", 604800),
        ("P1D", 86400),
    ],
)
def test_parse_iso8601_duration(duration_str, expected_seconds):
    assert parse_iso8601_duration(duration_str) == expected_seconds

@pytest.mark.parametrize(
    "duration_seconds, max_chunk_duration, min_chunk_duration, overlap_duration, expected_splits",
    [
        # Video shorter than max_chunk_duration
        (2000, 2700, 1200, 300, [(0, 2000)]),
        # Video equal to max_chunk_duration
        (2700, 2700, 1200, 300, [(0, 2700)]),
        # Video slightly longer than max_chunk_duration, but the remainder is less than min_chunk_duration
        (3000, 2700, 1200, 300, [(0, 3000)]),
        # Video that needs to be split into two parts
        (4000, 2700, 1200, 300, [(0, 2700), (2400, 4000)]),
        # Video that needs to be split into three parts
        (7000, 2700, 1200, 300, [(0, 2700), (2400, 5100), (4800, 7000)]),
        # Edge case: last chunk is exactly min_chunk_duration
        (3900, 2700, 1200, 300, [(0, 2700), (2400, 3900)]),
        # Edge case: last chunk is shorter than min_chunk_duration, should be merged
        (3899, 2700, 1200, 300, [(0, 2700), (2400, 3899)]),
    ],
)
def test_calculate_video_splits(
    duration_seconds, max_chunk_duration, min_chunk_duration, overlap_duration, expected_splits
):
    splits = calculate_video_splits(
        duration_seconds, max_chunk_duration, min_chunk_duration, overlap_duration
    )
    assert splits == expected_splits
