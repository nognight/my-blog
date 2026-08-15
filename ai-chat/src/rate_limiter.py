"""Per-IP rate limiting backed by an in-memory asyncio queue.

Semantics (as requested):
  - An IP may send at most one message every ``interval`` seconds.
  - Requests that arrive *inside* the window are not dropped: they are put
    into a queue and their execution is deferred until their slot opens.
  - If more than ``max_queue`` messages are already queued for an IP, the new
    request is rejected (the caller maps this to HTTP 429).

Caveat: state lives in the Worker isolate that handled the request, so it is
consistent per-isolate, not across all 300+ Cloudflare edge locations. That is
fine for a demo / low-traffic bot. For strict global enforcement, swap this for
a Durable Object per IP (same ``acquire``/``release`` interface).
"""

from __future__ import annotations

import asyncio
import time


class RateLimiter:
    def __init__(self, interval: float = 5.0, max_queue: int = 5) -> None:
        self.interval = interval
        self.max_queue = max_queue
        self._lock = asyncio.Lock()
        self._next_slot: dict[str, float] = {}
        self._queued: dict[str, int] = {}

    async def acquire(self, ip: str) -> float | None:
        """Reserve the next available slot for ``ip``.

        Returns the number of seconds the caller must wait before it may run
        (``0.0`` = run immediately), or ``None`` when the queue is full and the
        request should be rejected with HTTP 429.
        """
        async with self._lock:
            now = time.monotonic()
            slot = max(now, self._next_slot.get(ip, 0.0))

            if slot > now and self._queued.get(ip, 0) >= self.max_queue:
                return None

            if slot > now:
                self._queued[ip] = self._queued.get(ip, 0) + 1

            # Advance the window so the next message is scheduled interval later.
            self._next_slot[ip] = slot + self.interval
            return slot - now

    async def release(self, ip: str) -> None:
        """Must be called exactly once per queued message after it runs."""
        async with self._lock:
            remaining = self._queued.get(ip, 0) - 1
            if remaining > 0:
                self._queued[ip] = remaining
            else:
                self._queued.pop(ip, None)