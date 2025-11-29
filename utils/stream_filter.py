"""
Stream Filtering for Event-Based EPG

Filters streams to identify actual game streams vs placeholders and non-game content.
Uses positive detection - streams must contain game indicators (vs, @, at) to be counted.

This ensures match rate calculations reflect reality:
- "10/12 matched" (game streams only)
- Not "10/20 matched" (inflated by placeholders and non-game streams)
"""

import re
from typing import Dict, List, Tuple

# Pattern to detect game indicators in stream names
# Matches: vs, vs., at (as word), v (as word), @
GAME_INDICATOR_PATTERN = re.compile(
    r'\b(vs\.?|at|v)\b|@',
    re.IGNORECASE
)


def has_game_indicator(stream_name: str) -> bool:
    """
    Check if a stream name contains a matchup indicator.

    Game indicators are patterns that suggest this is an actual game stream:
    - "vs" or "vs." (e.g., "Lakers vs Celtics")
    - "@" (e.g., "Chiefs @ Ravens")
    - "at" as a word (e.g., "Patriots at Bills")
    - "v" as a word (e.g., "Arsenal v Chelsea" - soccer style)

    Args:
        stream_name: The stream name to check

    Returns:
        True if the stream appears to be a game stream

    Examples:
        >>> has_game_indicator("NBA 01: Lakers vs Celtics")
        True
        >>> has_game_indicator("NFL 02: Chiefs @ Ravens")
        True
        >>> has_game_indicator("NFL 03 - ")
        False
        >>> has_game_indicator("RedZone")
        False
        >>> has_game_indicator("NFL Network")
        False
    """
    return bool(GAME_INDICATOR_PATTERN.search(stream_name))


def filter_game_streams(
    streams: List[Dict],
    exclude_regex: str = None
) -> Dict:
    """
    Filter streams to only those that appear to be game streams.

    Two-layer filtering:
    1. Built-in: Must have game indicator (vs/@/at/v)
    2. Optional: User exclusion regex for additional filtering

    Args:
        streams: List of stream dicts with 'name' key
        exclude_regex: Optional regex pattern to exclude additional streams

    Returns:
        Dict with:
        - 'game_streams': Streams that passed filtering
        - 'filtered_streams': All streams that were filtered out
        - 'filtered_no_indicator': Count of streams without vs/@/at
        - 'filtered_exclude_regex': Count of streams matching exclusion regex

    Example:
        >>> streams = [
        ...     {'name': 'NBA 01: Lakers vs Celtics', 'id': 1},
        ...     {'name': 'NBA 02 - ', 'id': 2},
        ...     {'name': 'RedZone', 'id': 3},
        ... ]
        >>> result = filter_game_streams(streams)
        >>> len(result['game_streams'])
        1
        >>> result['filtered_no_indicator']
        2
    """
    game_streams = []
    filtered_streams = []
    filtered_no_indicator = 0
    filtered_exclude_regex = 0

    # Compile user exclusion pattern if provided
    exclude_pattern = None
    if exclude_regex:
        try:
            exclude_pattern = re.compile(exclude_regex, re.IGNORECASE)
        except re.error:
            # Invalid regex - log and continue without it
            pass

    for stream in streams:
        name = stream.get('name', '')

        # Layer 1: Must have game indicator
        if not has_game_indicator(name):
            filtered_streams.append(stream)
            filtered_no_indicator += 1
            continue

        # Layer 2: Check user exclusion pattern
        if exclude_pattern and exclude_pattern.search(name):
            filtered_streams.append(stream)
            filtered_exclude_regex += 1
            continue

        game_streams.append(stream)

    return {
        'game_streams': game_streams,
        'filtered_streams': filtered_streams,
        'filtered_no_indicator': filtered_no_indicator,
        'filtered_exclude_regex': filtered_exclude_regex,
    }


def get_filter_summary(
    total_count: int,
    game_count: int,
    matched_count: int
) -> str:
    """
    Generate a human-readable summary of filtering results.

    Args:
        total_count: Total streams from provider
        game_count: Streams that passed game indicator filter
        matched_count: Streams that matched to ESPN events

    Returns:
        Summary string like "8/10 matched (5 non-game filtered)"
    """
    filtered_count = total_count - game_count

    if filtered_count > 0:
        return f"{matched_count}/{game_count} matched ({filtered_count} non-game filtered)"
    else:
        return f"{matched_count}/{game_count} matched"
