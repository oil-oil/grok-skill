#!/usr/bin/env python3
"""Remove a near-solid background by flood-filling from image corners."""

from collections import deque
from pathlib import Path
import sys

from PIL import Image


def cutout(source: Path, destination: Path, threshold: int = 18) -> None:
    image = Image.open(source).convert("RGBA")
    pixels = image.load()
    width, height = image.size
    visited: set[tuple[int, int]] = set()
    for corner_x, corner_y in ((0, 0), (width - 1, 0), (0, height - 1), (width - 1, height - 1)):
        background = pixels[corner_x, corner_y][:3]
        queue = deque([(corner_x, corner_y)])
        while queue:
            x, y = queue.popleft()
            if (x, y) in visited or x < 0 or y < 0 or x >= width or y >= height:
                continue
            red, green, blue, _ = pixels[x, y]
            if all(abs(value - target) < threshold for value, target in zip((red, green, blue), background)):
                visited.add((x, y))
                pixels[x, y] = (0, 0, 0, 0)
                queue.extend(((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)))
    destination.parent.mkdir(parents=True, exist_ok=True)
    image.save(destination)
    print(f"cutout: {len(visited)} px removed; {destination}")


def main() -> int:
    if len(sys.argv) not in (2, 3):
        print("usage: cutout.py <input> [output]", file=sys.stderr)
        return 2
    source = Path(sys.argv[1]).expanduser().resolve()
    destination = Path(sys.argv[2]).expanduser().resolve() if len(sys.argv) == 3 else source
    if not source.is_file():
        print(f"error: input not found: {source}", file=sys.stderr)
        return 2
    cutout(source, destination)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
