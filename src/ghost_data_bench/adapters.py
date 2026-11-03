"""Runtime adapter boundary: input is visible bytes only, never paths or labels."""

import hashlib
from typing import Protocol


class RuntimeAdapter(Protocol):
    name: str

    def predict(self, visible_bytes: bytes) -> dict: ...


class KernelAdapter:
    name = "deterministic"

    def predict(self, visible_bytes):
        # Lazy imports keep the generator/oracle independent of the kernel.
        from ghost_data.engine import audit
        from ghost_data.models import Bundle

        bundle = Bundle.model_validate_json(visible_bytes)
        return audit(bundle, hashlib.sha256(visible_bytes).hexdigest()).model_dump(
            mode="json"
        )


MODES = ("deterministic", "extraction", "agent", "agent_challenger")


def adapter_for(mode):
    if mode == "deterministic":
        return KernelAdapter()
    if mode in MODES:
        raise NotImplementedError(
            f"{mode} uses ghost_data_bench.local_agent; the general runner implements deterministic mode only"
        )
    raise ValueError("Unknown runtime mode")
