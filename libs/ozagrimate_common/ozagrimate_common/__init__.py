"""Shared library used by every OzAgriMate service.

It holds cross-cutting plumbing only (the agreed error body and a UTC clock),
never business logic, so each service stays independently deployable.
This is the "shared library" form of code reuse from the Week 6 lectorial.
"""

from .errors import ApiError, ErrorBody, error_body, register_error_handlers
from .timeutil import utc_now

__all__ = ["ApiError", "ErrorBody", "error_body", "register_error_handlers", "utc_now"]
