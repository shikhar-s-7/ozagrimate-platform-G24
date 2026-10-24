"""Duplicate Filter component.

Gateways buffer readings while offline and replay them when the link returns
(ASR20, C5). The filter drops any reading whose (deviceId, sequenceNo) was
already accepted, so a replay never stores the same reading twice (ADR-03).
"""

from .filter import DuplicateFilter

__all__ = ["DuplicateFilter"]
