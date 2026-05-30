from collections import defaultdict, deque
from dataclasses import dataclass
from time import monotonic
from typing import Deque

from fastapi import HTTPException, Request, status

from .settings import get_settings


@dataclass
class RateLimitBucket:
    requests: Deque[float]


class InMemoryRateLimiter:
    def __init__(self, limit_per_minute: int) -> None:
        self.limit = limit_per_minute
        self.buckets: dict[str, RateLimitBucket] = defaultdict(
            lambda: RateLimitBucket(deque())
        )

    def allow(self, key: str) -> bool:
        now = monotonic()
        bucket = self.buckets[key]
        while bucket.requests and now - bucket.requests[0] > 60:
            bucket.requests.popleft()
        if len(bucket.requests) >= self.limit:
            return False
        bucket.requests.append(now)
        return True


_rate_limiter = InMemoryRateLimiter(get_settings().rate_limit_per_minute)


async def rate_limit(request: Request) -> None:
    key = request.client.host if request.client else "anonymous"
    if not _rate_limiter.allow(key):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate limit exceeded"
        )


def validate_non_empty_text(value: str, field_name: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise ValueError(f"{field_name} cannot be empty")
    return cleaned
