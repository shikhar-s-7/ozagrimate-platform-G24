"""Authorisation Checker component.

Works out who is calling and whether they may act on a farm (ADR-05, ASR9,
ASR17). The API Gateway validates the caller's token with the Identity Provider
and forwards the user ID in the X-User-Id header; this service trusts that header
because it is reachable only through the gateway.
"""

from .checker import AuthorisationChecker

__all__ = ["AuthorisationChecker"]
