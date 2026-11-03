"""Write separate runtime inputs and evaluator-only truth with integrity hashes."""

import argparse
import hashlib
import json
from pathlib import Path

from .oracle import expected
from .world import FAMILIES, generate_world, project

SIZES = {"small": 32, "medium": 128, "large": 512}


def encoded(value):
    return (json.dumps(value, sort_keys=True, indent=2) + "\n").encode()


def generate(destination, seed=42, count=32):
    destination = Path(destination)
    if destination.exists():
        raise ValueError("Destination exists; refusing to overwrite a suite")
    if not 1 <= count <= 10000:
        raise ValueError("count must be between 1 and 10000")
    (destination / "visible").mkdir(parents=True)
    (destination / "evaluator_only").mkdir()
    manifest = []
    for index in range(count):
        family = FAMILIES[index % len(FAMILIES)]
        world = generate_world(seed, index, family)
        visible, quality = project(world)
        # Independent random-looking scenario identifiers reveal no family/answer.
        sid = hashlib.sha256(f"ghost-data-v1:{seed}:{index}".encode()).hexdigest()[:16]
        data = encoded(visible)
        digest = hashlib.sha256(data).hexdigest()
        (destination / "visible" / f"{sid}.json").write_bytes(data)
        hidden = dict(
            world=world,
            evidence_quality=quality,
            expected=expected(world, visible, quality),
            input_sha256=digest,
        )
        (destination / "evaluator_only" / f"{sid}.json").write_bytes(encoded(hidden))
        manifest.append(dict(id=sid, sha256=digest))
    (destination / "manifest.json").write_bytes(
        encoded(dict(generator_version=1, seed=seed, count=count, cases=manifest))
    )
    return manifest


def main():
    parser = argparse.ArgumentParser(
        description="Generate independent synthetic audit worlds"
    )
    parser.add_argument("destination", type=Path)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--size", choices=SIZES, default="small")
    parser.add_argument("--count", type=int)
    args = parser.parse_args()
    generate(
        args.destination,
        args.seed,
        args.count if args.count is not None else SIZES[args.size],
    )


if __name__ == "__main__":
    main()
