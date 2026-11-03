"""Encode actual browser capture frames as a GIF; optional Pillow dependency.

No captions, agent content or UI pixels are inserted. GIF color quantization is
lossy; original recordings remain the evidence for event contents.
"""

import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("frames", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    try:
        from PIL import Image
    except ImportError:
        raise SystemExit(
            "Optional media generation requires Pillow (tested: 11.3.0)"
        ) from None
    capture = json.loads((args.frames / "capture.json").read_text())
    images = [
        Image.open(args.frames / row["file"]).convert("RGB")
        for row in capture["frames"]
    ]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    images[0].save(
        args.output,
        save_all=True,
        append_images=images[1:],
        duration=[2500] * len(images),
        loop=0,
        optimize=False,
    )
    for image in images:
        image.close()
    print(
        f"Encoded {len(images)} actual captures; {len(images) * 2.5:.1f} seconds; {args.output.stat().st_size} bytes"
    )


if __name__ == "__main__":
    main()
