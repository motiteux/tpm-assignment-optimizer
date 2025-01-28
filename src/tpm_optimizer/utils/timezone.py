from datetime import datetime
import pytz
from ..models import Program


def tz_to_utc_offset(tz_str: str) -> float:
    """Calculate UTC offset for a timezone

    Args:
        tz_str: Timezone string. If empty or invalid, UTC is assumed.

    Returns:
        float: UTC offset in hours
    """
    if not tz_str:
        tz_str = 'UTC'
    try:
        tz = pytz.timezone(tz_str)
        naive_dt = datetime.now().replace(tzinfo=None)
        offset = tz.utcoffset(naive_dt).total_seconds() / 3600
        return offset
    except pytz.exceptions.UnknownTimeZoneError:
        return 0.0  # Default to UTC for unknown timezones


def timezone_difference(tz1: str, tz2: str) -> float:
    """Calculate absolute hour difference between two timezones

    Args:
        tz1: First timezone string. If empty or invalid, UTC is assumed.
        tz2: Second timezone string. If empty or invalid, UTC is assumed.

    Returns:
        float: Absolute difference in hours between the timezones
    """
    # If either timezone is empty, treat it as UTC
    tz1 = tz1 if tz1 else 'UTC'
    tz2 = tz2 if tz2 else 'UTC'

    offset1 = tz_to_utc_offset(tz1)
    offset2 = tz_to_utc_offset(tz2)
    return abs(offset1 - offset2)


def calculate_timezone_score(tpm_timezone: str, program: Program) -> float:
    """Calculate timezone compatibility score for a TPM and program

    Args:
        tpm_timezone: TPM's timezone. If empty or invalid, UTC is assumed.
        program: Program object with timezone and stakeholder_timezones

    Returns:
        float: Score between 0 and 1, where:
               1.0 = perfect match (≤3 hours difference)
               0.5 = acceptable match (≤6 hours difference)
               0.0 = poor match (>6 hours difference)
    """
    # Filter out empty timezone strings and ensure we have at least one timezone
    program_timezones = [tz for tz in ([program.timezone] + list(program.stakeholder_timezones)) if tz]
    if not program_timezones:
        return 1.0  # If no timezone requirements, consider it a perfect match

    # Use UTC for empty TPM timezone
    tpm_timezone = tpm_timezone if tpm_timezone else 'UTC'

    offsets = [tz_to_utc_offset(tz) for tz in program_timezones]
    barycenter = sum(offsets) / len(offsets)
    tpm_offset = tz_to_utc_offset(tpm_timezone)
    diff = abs(tpm_offset - barycenter)

    if diff <= 3:
        return 1.0
    elif diff <= 6:
        return 0.5
    else:
        return 0.0