"""UTC clock shared by the services."""

from datetime import datetime, timezone


def utc_now() -> datetime:
    """Return the current UTC time, timezone-aware and rounded to whole seconds."""
    return datetime.now(timezone.utc).replace(microsecond=0)
