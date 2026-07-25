#!/usr/bin/env python3
"""
build_demo.py — the crossfade that is the claim.

The one verified cold-start case in this whole category — a repository that went
from twenty followers to 1,711 stars in seven days — leads its README with a
video of the skill doing its own job. This repository's claim is "geometry is
locked, material is not", and a still pair makes a reader compare two images to
check it. A crossfade makes the geometry hold still while the material moves,
which is the same evidence with none of the work.

Nothing here is a new claim. Every frame is one of the paired images already in
examples/, at the strength recorded in recipes.json, blended.

    python3 build_demo.py            # writes demo.webp

Animated WebP rather than MP4: GitHub renders it from a plain <img> in the
README with no <video> tag, no raw-URL games, and at roughly a fifth the bytes.
"""

from __future__ import annotations

import argparse
import json
import pathlib

from PIL import Image, ImageDraw, ImageFont

HERE = pathlib.Path(__file__).resolve().parent

# Order is deliberate: the two recipes that hold on any source come first,
# because the first two seconds decide whether the rest is watched, and the
# panels descend by how much actually changes on screen.
#
# `relight-single-source` is not here despite being the most legible image in
# the set. Mean per-pixel change across the five pairs runs gouache 43.9,
# palette 37.8, cyanotype 19.4, hard-sun 17.7, single-source 6.4 — the corridor
# barely moves, which is the honest result for a `narrow` recipe and a bad
# closing shot for a demo whose whole point is that the material changes.
PANELS = [
    ("medium-gouache", "photograph to gouache", "every terrace contour holds"),
    ("palette-shift", "recolour to three named colours", "not a line moves"),
    ("medium-cyanotype", "render to a cyanotype print",
     "every component in position - needs a source that makes line marks"),
]
# `relight-hard-sun` is not the third panel either. Its pair changes the light
# direction and warms the rock, but the long cast shadows the recipe names are
# not visible in it at demo size; the evidence for those is the concrete
# stairwell second-source run, which is not a before/after pair.

# Milliseconds, not repeated frames. Writing a hold as N identical frames and a
# scalar duration produced a file with 39 frames and duration 0 on every one of
# them — Pillow collapses identical consecutive frames and drops the timing with
# them. One frame per distinct image with its own duration is both correct and
# a third of the bytes.
MS_BEFORE, MS_FADE, MS_AFTER = 550, 50, 850
FADE_STEPS = 11


def font(size: int, bold: bool = False):
    names = ["Arial Bold.ttf", "Helvetica.ttc"] if bold else ["Arial.ttf", "Helvetica.ttc"]
    for n in names:
        for d in ("/System/Library/Fonts/Supplemental/", "/System/Library/Fonts/"):
            p = pathlib.Path(d + n)
            if p.exists():
                try:
                    return ImageFont.truetype(str(p), size)
                except Exception:
                    pass
    return ImageFont.load_default()


def square(path: pathlib.Path, size: int) -> Image.Image:
    im = Image.open(path).convert("RGB")
    s = min(im.size)
    im = im.crop(((im.width - s) // 2, (im.height - s) // 2,
                  (im.width + s) // 2, (im.height + s) // 2))
    return im.resize((size, size), Image.LANCZOS)


def probe(path: pathlib.Path) -> tuple[int, int, int]:
    """Read frame count, total duration in ms, and loop count out of the file's
    own RIFF chunks.

    Not from Pillow. Pillow's WebP *reader* returns None for `info["duration"]`
    on a file whose ANMF chunks carry perfectly good durations, so checking the
    output through the same library that wrote it reported a broken animation
    that was not broken. The bytes are the artifact; the library is not.
    """
    data = path.read_bytes()
    off, frames, total, loops = 12, 0, 0, -1
    while off + 8 <= len(data):
        cid = data[off:off + 4].decode("ascii", "replace")
        size = int.from_bytes(data[off + 4:off + 8], "little")
        body = data[off + 8:off + 8 + size]
        if cid == "ANMF":
            frames += 1
            total += int.from_bytes(body[12:15], "little")  # 3-byte frame duration
        elif cid == "ANIM":
            loops = int.from_bytes(body[4:6], "little")
        off += 8 + size + (size & 1)
    return frames, total, loops


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default="demo.webp")
    ap.add_argument("--size", type=int, default=640)
    ap.add_argument("--quality", type=int, default=72)
    args = ap.parse_args()

    recipes = {r["id"]: r for r in json.loads(
        (HERE / "recipes.json").read_text(encoding="utf-8"))["recipes"]}
    S, bar = args.size, 54
    ftitle, fnote = font(19, bold=True), font(15)

    frames: list[Image.Image] = []
    durations: list[int] = []
    for rid, title, note in PANELS:
        r = recipes[rid]
        before = square(HERE / r["example"][0], S)
        after = square(HERE / r["example"][1], S)
        label = f"{rid}  ·  strength {r['strength']}  ·  seed {r['seed']}"

        def frame(img: Image.Image, show_after: bool) -> Image.Image:
            canvas = Image.new("RGB", (S, S + bar), (255, 255, 255))
            canvas.paste(img, (0, 0))
            d = ImageDraw.Draw(canvas)
            d.text((12, S + 8), title if show_after else "source",
                   fill=(17, 17, 17), font=ftitle)
            d.text((12, S + 31), note if show_after else label,
                   fill=(110, 110, 110), font=fnote)
            return canvas

        frames.append(frame(before, False)); durations.append(MS_BEFORE)
        for i in range(1, FADE_STEPS + 1):
            t = i / (FADE_STEPS + 1)
            frames.append(frame(Image.blend(before, after, t), t > 0.5))
            durations.append(MS_FADE)
        frames.append(frame(after, True)); durations.append(MS_AFTER)

    # Pillow writes animated WebP itself. Homebrew's ffmpeg 8 ships with the
    # webp encoder disabled, and a build step that depends on which ffmpeg the
    # reader happens to have is a build step that breaks for them.
    out = HERE / args.out
    frames[0].save(out, "WEBP", save_all=True, append_images=frames[1:],
                   duration=durations, loop=0, quality=args.quality, method=4)

    n, total, loops = probe(out)
    assert n == len(frames), f"wrote {len(frames)} frames, file has {n}"
    assert total == sum(durations), \
        f"timing lost: wanted {sum(durations)}ms, file has {total}ms"
    assert loops == 0, f"loop count is {loops}, wanted 0 (forever)"

    kb = out.stat().st_size // 1024
    print(f"wrote {out.name}  {n} frames  {total/1000:.2f}s  "
          f"{frames[0].size[0]}x{frames[0].size[1]}  {kb} KB  loop=forever")
    if kb > 4000:
        print("  over 4 MB — GitHub will still serve it but the README will feel slow")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
