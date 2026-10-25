"""Farm Access Cache component.

This service's own copy of the farms (owner, crop, region) and the access grants
held by the Farm & Access Service. It is kept up to date by consuming
AccessGranted and AccessRevoked events, so a revoked agronomist stops seeing a
farm's alerts without a call per request (ADR-05, ASR7, ASR9). The Threshold
Evaluator also reads each farm's crop and region from it.
"""

from .cache import READ_ALERTS, FarmAccessCache, FarmRecord, GrantRecord, seeded_farm_access_cache

__all__ = ["READ_ALERTS", "FarmAccessCache", "FarmRecord", "GrantRecord", "seeded_farm_access_cache"]
