"""Notification Dispatcher component.

Sends each alert by push notification first and falls back to SMS through the
SMS gateway when the push is not delivered (ADR-04, ASR6, C4).
"""
