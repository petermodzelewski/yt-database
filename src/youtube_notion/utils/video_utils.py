import re
from typing import List, Tuple
from datetime import timedelta

def parse_iso8601_duration(duration: str) -> int:
    """
    Parse an ISO 8601 duration string (e.g., PT1H2M3S) into seconds.
    Args:
        duration: ISO 8601 duration string.
    Returns:
        The duration in seconds.
    """
    if not duration or duration.startswith("-"):
        return 0

    match = re.match(
        r"P(?:(?P<years>\d+)Y)?(?:(?P<months>\d+)M)?(?:(?P<weeks>\d+)W)?(?:(?P<days>\d+)D)?"
        r"T?(?:(?P<hours>\d+)H)?(?:(?P<minutes>\d+)M)?(?:(?P<seconds>\d+)S)?",
        duration,
    )
    if not match:
        return 0

    parts = match.groupdict()
    time_params = {}
    for name, param in parts.items():
        if param:
            time_params[name] = int(param)

    total_seconds = timedelta(
        days=(time_params.get("years", 0) * 365)
        + (time_params.get("months", 0) * 30)
        + (time_params.get("weeks", 0) * 7)
        + time_params.get("days", 0),
        hours=time_params.get("hours", 0),
        minutes=time_params.get("minutes", 0),
        seconds=time_params.get("seconds", 0),
    ).total_seconds()

    return int(total_seconds)


def calculate_video_splits(
    duration_seconds: int,
    max_chunk_duration: int = 2700,  # 45 minutes
    min_chunk_duration: int = 1200,  # 20 minutes
    overlap_duration: int = 300,  # 5 minutes
) -> List[Tuple[int, int]]:
    """
    Calculate video splits for a long video.

    Args:
        duration_seconds: The total duration of the video in seconds.
        max_chunk_duration: The maximum duration of a single chunk in seconds.
        min_chunk_duration: The minimum duration of a single chunk in seconds.
        overlap_duration: The duration of the overlap between chunks in seconds.

    Returns:
        A list of tuples, where each tuple contains the start and end time
        of a video chunk in seconds.
    """
    if duration_seconds <= max_chunk_duration:
        return [(0, duration_seconds)]

    splits = []
    start_time = 0
    while True:
        end_time = start_time + max_chunk_duration
        if end_time >= duration_seconds:
            splits.append((start_time, duration_seconds))
            break

        next_start_time = end_time - overlap_duration
        remaining_duration = duration_seconds - next_start_time
        if remaining_duration < min_chunk_duration:
            splits.append((start_time, duration_seconds))
            break

        splits.append((start_time, end_time))
        start_time = next_start_time

    return splits
