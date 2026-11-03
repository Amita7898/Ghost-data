"""Shared web execution states; audit conclusions are a separate contract."""

from typing import Literal

RunStatus = Literal[
    "queued",
    "running",
    "cancelling",
    "completed",
    "cancelled",
    "failed",
    "interrupted",
    "verification_failed",
]
TERMINAL_STATUSES = frozenset(
    {"completed", "cancelled", "failed", "interrupted", "verification_failed"}
)
