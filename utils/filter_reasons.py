"""
Filter Reasons - Single Source of Truth

Centralized definitions for all stream filtering and event matching reasons.
These constants are used throughout the codebase for consistency in:
- Event matcher results
- Preview modal display
- Statistics tracking
- Logging

Usage:
    from utils.filter_reasons import FilterReason, get_display_text

    # In event_matcher.py
    result['reason'] = FilterReason.GAME_FINAL_EXCLUDED

    # In UI/templates
    display_text = get_display_text(reason)
"""


class FilterReason:
    """
    Constants for filter/match reasons.

    Categories:
    1. Stream filtering (pre-matching)
    2. Event matching (post-team-parsing)
    """

    # =========================================================================
    # Stream Filtering Reasons (before team matching)
    # =========================================================================

    # Built-in game indicator filter
    NO_GAME_INDICATOR = 'no_game_indicator'

    # User inclusion regex not matched
    INCLUDE_REGEX_NOT_MATCHED = 'include_regex_not_matched'

    # User exclusion regex matched
    EXCLUDE_REGEX_MATCHED = 'exclude_regex_matched'

    # =========================================================================
    # Event Matching Reasons (after successful team parsing)
    # =========================================================================

    # Game from previous day(s) - always excluded
    GAME_PAST = 'game_past'

    # Today's game is final - excluded by user setting
    GAME_FINAL_EXCLUDED = 'game_final_excluded'

    # No ESPN event found for the team matchup
    NO_GAME_FOUND = 'no_game_found'

    # Teams successfully parsed but outside lookahead window
    OUTSIDE_LOOKAHEAD = 'outside_lookahead'

    # =========================================================================
    # Team Parsing Reasons
    # =========================================================================

    # Could not parse team names from stream
    TEAMS_NOT_PARSED = 'teams_not_parsed'

    # Teams parsed but one or both not found in any ESPN league
    TEAMS_NOT_IN_ESPN = 'teams_not_in_espn'

    # Teams parsed but no common league found (each team in different leagues)
    NO_COMMON_LEAGUE = 'no_common_league'

    # =========================================================================
    # Unsupported Sport/League Reasons
    # =========================================================================

    # Beach soccer detected (BS/BSC suffix) - not supported by ESPN API
    UNSUPPORTED_BEACH_SOCCER = 'unsupported_beach_soccer'

    # Boxing/MMA detected (main card, undercard, prelims) - not supported
    UNSUPPORTED_BOXING_MMA = 'unsupported_boxing_mma'

    # Futsal detected (FP suffix = Futbol Playa/Futsal Playa) - not supported
    UNSUPPORTED_FUTSAL = 'unsupported_futsal'

    # =========================================================================
    # Configuration Mismatch Reasons
    # =========================================================================

    # Event found in a league that user hasn't enabled for this group
    LEAGUE_NOT_ENABLED = 'league_not_enabled'


# Display text for user-facing UI (preview modal, etc.)
DISPLAY_TEXT = {
    FilterReason.NO_GAME_INDICATOR: 'Excluded by filter',
    FilterReason.INCLUDE_REGEX_NOT_MATCHED: 'Did not match inclusion pattern',
    FilterReason.EXCLUDE_REGEX_MATCHED: 'Matched exclusion pattern',
    FilterReason.GAME_PAST: 'Event already passed',
    FilterReason.GAME_FINAL_EXCLUDED: 'Event is final (excluded)',
    FilterReason.NO_GAME_FOUND: 'No event found',
    FilterReason.OUTSIDE_LOOKAHEAD: 'Outside lookahead range',
    FilterReason.TEAMS_NOT_PARSED: 'Teams not parsed',
    FilterReason.TEAMS_NOT_IN_ESPN: 'Team(s) not in ESPN database',
    FilterReason.NO_COMMON_LEAGUE: 'No common league for teams',
    FilterReason.UNSUPPORTED_BEACH_SOCCER: 'Unsupported (Beach Soccer)',
    FilterReason.UNSUPPORTED_BOXING_MMA: 'Unsupported (Boxing/MMA)',
    FilterReason.UNSUPPORTED_FUTSAL: 'Unsupported (Futsal)',
    FilterReason.LEAGUE_NOT_ENABLED: 'League not enabled',
}

# Internal reasons (used by event_matcher.py for backwards compatibility)
# These map to the FilterReason constants
INTERNAL_REASONS = {
    'Game already completed (past)': FilterReason.GAME_PAST,
    'Game completed (excluded)': FilterReason.GAME_FINAL_EXCLUDED,
    'No game found between teams': FilterReason.NO_GAME_FOUND,
}

# Reverse mapping for converting internal reasons to display text
INTERNAL_TO_DISPLAY = {
    'Game already completed (past)': DISPLAY_TEXT[FilterReason.GAME_PAST],
    'Game completed (excluded)': DISPLAY_TEXT[FilterReason.GAME_FINAL_EXCLUDED],
    'No game found between teams': DISPLAY_TEXT[FilterReason.NO_GAME_FOUND],
}


def get_display_text(reason: str, lookahead_days: int = None, league_name: str = None) -> str:
    """
    Get user-friendly display text for a filter reason.

    Args:
        reason: The filter reason constant or internal reason string
        lookahead_days: Optional lookahead days for NO_GAME_FOUND reason
        league_name: Optional league name for LEAGUE_NOT_ENABLED reason

    Returns:
        Human-readable display text
    """
    # Check if it's a FilterReason constant
    if reason in DISPLAY_TEXT:
        text = DISPLAY_TEXT[reason]
        if reason == FilterReason.NO_GAME_FOUND and lookahead_days:
            return f'No event in lookahead range ({lookahead_days} days)'
        if reason == FilterReason.LEAGUE_NOT_ENABLED and league_name:
            return f'Found in {league_name} (not enabled)'
        return text

    # Check if it's an internal reason string (backwards compatibility)
    if reason in INTERNAL_TO_DISPLAY:
        return INTERNAL_TO_DISPLAY[reason]

    # Return as-is if not recognized
    return reason


def normalize_reason(reason: str) -> str:
    """
    Normalize an internal reason string to a FilterReason constant.

    Args:
        reason: Internal reason string from event_matcher

    Returns:
        FilterReason constant, or original string if not recognized
    """
    return INTERNAL_REASONS.get(reason, reason)


def is_excluded_from_count(reason: str) -> bool:
    """
    Check if a reason should exclude the stream from the match rate denominator.

    Streams that match this criteria are not "failures to match" - they're
    streams where matching isn't applicable (past games, finals when excluded,
    no event in lookahead, or event in a non-enabled league).

    Args:
        reason: Filter reason constant or internal reason string

    Returns:
        True if stream should be excluded from match rate calculation
    """
    normalized = normalize_reason(reason)
    return normalized in (
        FilterReason.GAME_PAST,
        FilterReason.GAME_FINAL_EXCLUDED,
        FilterReason.NO_GAME_FOUND,  # No event in lookahead range
        FilterReason.LEAGUE_NOT_ENABLED,  # Event in non-enabled league
    )


# Database column mapping for statistics
DB_COLUMN_MAPPING = {
    FilterReason.NO_GAME_INDICATOR: 'filtered_no_indicator',
    FilterReason.INCLUDE_REGEX_NOT_MATCHED: 'filtered_include_regex',
    FilterReason.EXCLUDE_REGEX_MATCHED: 'filtered_exclude_regex',
    FilterReason.GAME_PAST: 'filtered_outside_lookahead',
    FilterReason.GAME_FINAL_EXCLUDED: 'filtered_final',
    FilterReason.NO_GAME_FOUND: 'filtered_outside_lookahead',  # Combined with GAME_PAST
}


def is_boxing_mma(stream_name: str) -> bool:
    """
    Detect if stream is likely boxing/MMA based on card terminology.

    Boxing/MMA events commonly use:
    - "Main Card", "Maincard"
    - "Under Card", "Undercard"
    - "Prelims", "Preliminary Card"
    - "Early Prelims"

    Args:
        stream_name: Full stream name to check

    Returns:
        True if stream appears to be a boxing/MMA event
    """
    import re

    if not stream_name:
        return False

    # Pattern: main card, maincard, under card, undercard, prelims, preliminary
    boxing_pattern = re.compile(
        r'\b(main\s*card|under\s*card|prelims|preliminary\s*card|early\s*prelims)\b',
        re.IGNORECASE
    )

    return bool(boxing_pattern.search(stream_name))


def is_beach_soccer(team1: str, team2: str) -> bool:
    """
    Detect if teams are likely beach soccer based on BS/BSC suffix.

    Beach soccer clubs commonly use:
    - BS = Beach Soccer (e.g., "Zarcero BS", "Sao Pedro BS")
    - BSC = Beach Soccer Club (e.g., "Nassau BSC", "Cali BSC")

    Args:
        team1: First team name
        team2: Second team name

    Returns:
        True if either team appears to be a beach soccer team
    """
    import re

    if not team1 and not team2:
        return False

    # Pattern: team name ending with BS or BSC (case-insensitive)
    # Must be at end of string, optionally followed by closing paren
    beach_pattern = re.compile(r'\b(BS|BSC)\s*\)?$', re.IGNORECASE)

    for team in [team1, team2]:
        if team and beach_pattern.search(team.strip()):
            return True

    return False


def is_futsal(team1: str, team2: str) -> bool:
    """
    Detect if teams are likely futsal based on FP suffix.

    Futsal teams commonly use:
    - FP = Futbol Playa / Futsal Playa (e.g., "USAC FP", "FP Riviera Maya")

    Args:
        team1: First team name
        team2: Second team name

    Returns:
        True if either team appears to be a futsal team
    """
    import re

    if not team1 and not team2:
        return False

    # Pattern: team name ending with FP or starting with FP
    # e.g., "USAC FP", "FP Riviera Maya", "Dimas Escazú FP"
    futsal_pattern = re.compile(r'(\bFP\s*$|^FP\s+)', re.IGNORECASE)

    for team in [team1, team2]:
        if team and futsal_pattern.search(team.strip()):
            return True

    return False
