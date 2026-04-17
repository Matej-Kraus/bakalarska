"""Centralized time handling. All timestamps are stored as UTC."""

from datetime import datetime, timezone


def utcnow() -> datetime:
    """Return current time in UTC. Use this for all created_at / live_started_at etc."""
    return datetime.now(timezone.utc)
