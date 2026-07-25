#!/usr/bin/env python3
"""
same_frame.py — re-render an image you already have, with the composition intact.

Krea 2 image-to-image changes how a scene is rendered. It does not change what is
in the scene. That single sentence is the whole tool, and it is a measurement, not
an opinion: 114 generations went into the catalog this was extracted from, 5 of the
kept edits were rendering changes and every content change was cut.

So this script does two things a plain API wrapper does not:

  1. It refuses. Ask it to remove an object or to carry a character into a new
     scene and it stops before spending your money, and shows you the image where
     that already failed. Both refusals are overridable with --force, because
     being certain about someone else's use case is its own failure mode — but the
     default is the measurement.

  2. It uses recorded strengths. Every value in recipes.json is the one that
     produced the paired image in examples/, not a suggested starting point. The
     working band is 0.50-0.60 and it is narrower than it looks: below ~0.45 the
     source composition drowns the instruction, and by 0.72 the model is inventing
     a new subject.

    python3 same_frame.py --list
    python3 same_frame.py --image photo.jpg --recipe medium-gouache \
        --slot subject="these terraced fields" --slot contour="terrace contour" \
        --out out.png
    python3 same_frame.py --image photo.jpg --prompt "..." --strength 0.55 --out out.png

Every recipe has slots and the script will not run without them, so the second
line above is the short form of what actually works. --list and --dry-run need
no key and spend nothing.

FAL_KEY comes from a .env file beside this script, or from the environment.
Roughly $0.008 per megapixel — about eight tenths of a cent for 1024x1024.

Stdlib only.
"""

from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
QUEUE = "https://queue.fal.run"
MODEL = "fal-ai/krea-2/turbo/image-to-image"

# The measured band. Outside it the failure mode is predictable, so the script
# says which one you are about to hit rather than just clamping silently.
BAND = (0.50, 0.60)
BAND_HARD = (0.45, 0.65)


# --------------------------------------------------------------------------- #
# refusals — the part that makes this a skill rather than a wrapper
# --------------------------------------------------------------------------- #

def load_recipes() -> dict:
    return json.loads((HERE / "recipes.json").read_text(encoding="utf-8"))


def classify(prompt: str, refusals: list[dict]) -> dict | None:
    """Return the refusal this prompt trips, or None.

    Deliberately a phrase match rather than anything cleverer. A false positive
    costs one --force flag; a false negative costs a generation that was always
    going to come back wrong, plus the user's belief that it might work if they
    just phrase it better. It will not.
    """
    low = " " + re.sub(r"\s+", " ", prompt.lower()) + " "
    for r in refusals:
        for phrase in r["asks_like"]:
            if phrase in low:
                return {"refusal": r, "matched": phrase}
    return None


def show_refusal(hit: dict) -> None:
    r, ev = hit["refusal"], hit["refusal"]["evidence"]
    print(f"\nRefusing: {r['verdict']}", file=sys.stderr)
    print(f"  (triggered by {hit['matched']!r} — use --force if this read you wrong)\n", file=sys.stderr)
    print(f"  This was already run at strength {ev['strength']}, seed {ev['seed']}:", file=sys.stderr)
    print(f"    asked for: {ev['asked']}", file=sys.stderr)
    print(f"    got:       {ev['got']}", file=sys.stderr)
    print(f"    see:       {ev['example'][1]}", file=sys.stderr)
    for extra in r.get("also_failed", []):
        print(f"    also:      {extra}", file=sys.stderr)
    if r.get("why_no_setting_works"):
        print(f"\n  {r['why_no_setting_works']}", file=sys.stderr)
    print(f"\n  Instead: {r['instead']}\n", file=sys.stderr)


# --------------------------------------------------------------------------- #
# fal plumbing
# --------------------------------------------------------------------------- #

def load_dotenv() -> None:
    """Read KEY=value from the nearest .env, walking up from this script.

    A .env file is the right place for a key: it never enters shell history and
    never reaches a chat transcript. Values already in the environment win.
    """
    for d in [Path.cwd(), *HERE.parents[:3], HERE]:
        f = d / ".env"
        if not f.exists():
            continue
        for line in f.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip("'\""))
        return


def key() -> str:
    load_dotenv()
    k = os.environ.get("FAL_KEY") or os.environ.get("FAL_API_KEY")
    if not k:
        print("FAL_KEY is not set.\n\n"
              "  1. Get a key at https://fal.ai/dashboard/keys\n"
              "  2. Write it to a .env file — do not paste it into a chat:\n\n"
              "       printf 'FAL_KEY=%s\\n' 'PASTE_KEY_HERE' > .env && chmod 600 .env\n\n"
              "  .env is gitignored here.", file=sys.stderr)
        raise SystemExit(2)
    return k


class FalError(RuntimeError):
    """Carries the response body. urllib's default message is the status line
    only, which hides the useful sentence — a 403 here reads 'Exhausted balance',
    not 'forbidden'."""

    def __init__(self, code: int, body: str):
        self.code, self.body = code, body
        low, hint = body.lower(), ""
        if "exhausted balance" in low or "top up" in low:
            hint = "\n  → Add credits at https://fal.ai/dashboard/billing. The key is fine."
        elif code == 401:
            hint = "\n  → Key rejected. Check FAL_KEY in your .env."
        elif code == 422:
            hint = "\n  → Request body rejected; check the model schema."
        super().__init__(f"HTTP {code}: {body[:400]}{hint}")


def call(url: str, payload: dict | None = None, method: str = "GET") -> dict:
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(
        url, data=data, method=method,
        headers={"Authorization": f"Key {key()}", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        raise FalError(e.code, e.read().decode("utf-8", "replace")) from None


def image_ref(src: str) -> str:
    """A URL passes through; a local file is inlined as a data URI so nothing
    has to be uploaded anywhere first."""
    if src.startswith(("http://", "https://", "data:")):
        return src
    p = Path(src)
    if not p.exists():
        raise SystemExit(f"no such image: {src}")
    mime = mimetypes.guess_type(p.name)[0] or "image/png"
    return f"data:{mime};base64," + base64.b64encode(p.read_bytes()).decode()


def run(prompt: str, image: str, strength: float, seed: int | None, timeout_s: int) -> tuple[bytes, dict]:
    body = {"prompt": prompt, "image_url": image, "strength": strength,
            # The Krea 2 Community Licence makes content filtering a mandatory
            # obligation rather than an option, so this stays on.
            "enable_safety_checker": True}
    if seed is not None:
        body["seed"] = seed

    res = call(f"{QUEUE}/{MODEL}", body, "POST")
    rid = res.get("request_id")
    if not rid:
        raise RuntimeError(f"no request_id: {res}")
    # Use the URLs fal hands back. It truncates the model path in them, and
    # rebuilding from the full slug gets a 405.
    status_url = res.get("status_url") or f"{QUEUE}/{MODEL}/requests/{rid}/status"
    response_url = res.get("response_url") or f"{QUEUE}/{MODEL}/requests/{rid}"

    deadline, delay, st = time.time() + timeout_s, 1.0, "UNKNOWN"
    while time.time() < deadline:
        s = call(status_url)
        st = s.get("status")
        if st == "COMPLETED":
            out = call(response_url)
            images = out.get("images") or []
            if not images:
                raise RuntimeError(f"no images returned: {json.dumps(out)[:300]}")
            req = urllib.request.Request(images[0]["url"], headers={"User-Agent": "same-frame"})
            with urllib.request.urlopen(req, timeout=180) as r:
                return r.read(), out
        if st in ("FAILED", "CANCELLED"):
            raise RuntimeError(f"{st}: {json.dumps(s)[:400]}")
        time.sleep(delay)
        delay = min(delay * 1.4, 8.0)
    raise TimeoutError(f"still {st} after {timeout_s}s")


# --------------------------------------------------------------------------- #

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--image", help="source image: local path or URL")
    ap.add_argument("--recipe", help="recipe id from recipes.json")
    ap.add_argument("--prompt", help="your own prompt instead of a recipe")
    ap.add_argument("--slot", action="append", default=[], metavar="K=V",
                    help="fill a recipe slot, repeatable")
    ap.add_argument("--strength", type=float, help="overrides the recipe value")
    ap.add_argument("--seed", type=int, help="reproduce a specific generation")
    ap.add_argument("--out", default="out.png")
    ap.add_argument("--timeout", type=int, default=300)
    ap.add_argument("--force", action="store_true", help="run past a refusal or outside the band")
    ap.add_argument("--dry-run", action="store_true", help="resolve everything, call nothing")
    ap.add_argument("--list", action="store_true", help="show recipes and refusals")
    args = ap.parse_args()

    data = load_recipes()
    recipes = {r["id"]: r for r in data["recipes"]}

    if args.list:
        print(f"{data['rule']['holds']}\n")
        print(f"working band {data['rule']['band']} — measured on {data['rule']['measured_on']}\n")
        for r in data["recipes"]:
            print(f"  [{r['tier']:7s}] {r['id']:22s} strength {r['strength']}  — {r['name']}")
            print(f"  {'':10s} {'':22s} slots: {', '.join(r.get('slots', {}))}")
            g = r.get("generalisation", {})
            if g.get("use_when"):
                print(f"  {'':10s} {'':22s} use when: {g['use_when']}")
            if g.get("drifted"):
                print(f"  {'':10s} {'':22s} watch for: {g['drifted']}")
        print("\ntiers: " + " · ".join(f"{k}={v}" for k, v in data["generalisation"]["tiers"].items()))
        print("\nrefused by default:")
        for r in data["refusals"]:
            print(f"  {r['id']:22s} {r['verdict']}")
            print(f"  {'':22s} instead: {r['instead']}")
        return 0

    if not args.image:
        ap.error("need --image")
    if bool(args.recipe) == bool(args.prompt):
        ap.error("need exactly one of --recipe or --prompt")

    if args.recipe:
        r = recipes.get(args.recipe)
        if not r:
            ap.error(f"unknown recipe {args.recipe!r} — try --list")
        prompt = r["prompt"]
        slots = dict(kv.split("=", 1) for kv in args.slot if "=" in kv)
        missing = [s for s in r.get("slots", {}) if s not in slots]
        if missing:
            print(f"recipe {r['id']} needs slots that were not given:", file=sys.stderr)
            for m in missing:
                print(f"  --slot {m}=...   ({r['slots'][m]})", file=sys.stderr)
            print("\nThese are not decoration. Every kept edit named the thing that must\n"
                  "not move, in the prompt, explicitly. Vague sources drifted.", file=sys.stderr)
            return 2
        for k, v in slots.items():
            prompt = prompt.replace("{" + k + "}", v)
        strength = args.strength if args.strength is not None else r["strength"]
        # Whether a given source suits a given recipe is not detectable from the
        # file, so this warns rather than blocks. It exists because every recipe
        # here was re-run against a source it was not derived from, and two of
        # the five only work on the kind of source they came from.
        g = r.get("generalisation", {})
        if r["tier"] != "holds":
            print(f"note: {r['id']} is tier '{r['tier']}' — "
                  f"{data['generalisation']['tiers'][r['tier']].lower()}", file=sys.stderr)
            if g.get("use_when"):
                print(f"      use when: {g['use_when']}", file=sys.stderr)
            if g.get("drifted"):
                print(f"      otherwise: {g['drifted']}", file=sys.stderr)
            print(f"      evidence:  {g.get('example')}", file=sys.stderr)
    else:
        prompt = args.prompt
        if args.strength is None:
            ap.error("--prompt needs an explicit --strength (the band is 0.50-0.60)")
        strength = args.strength

    hit = classify(prompt, data["refusals"])
    if hit:
        show_refusal(hit)
        if not args.force:
            return 3
        print("  --force given; running anyway.\n", file=sys.stderr)

    lo, hi = BAND_HARD
    if not (lo <= strength <= hi):
        why = ("the source composition will dominate and the instruction will barely land"
               if strength < lo else
               "the model is free enough to invent, and what it invents replaces your subject")
        print(f"strength {strength} is outside the measured band {BAND[0]}-{BAND[1]}: {why}",
              file=sys.stderr)
        if not args.force:
            print("Pass --force if you mean it.", file=sys.stderr)
            return 4

    if args.dry_run:
        print(f"would run at strength {strength}:\n  {prompt}")
        return 0

    img = image_ref(args.image)
    print(f"strength {strength} · {Path(args.image).name if not args.image.startswith('http') else args.image}")
    blob, out = run(prompt, img, strength, args.seed, args.timeout)

    if (out.get("has_nsfw_concepts") or [None])[0]:
        print("safety checker flagged this generation — not written.", file=sys.stderr)
        return 5

    dest = Path(args.out)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(blob)
    print(f"{dest}  seed={out.get('seed')}  {len(blob)//1024} KB")
    print(f"reproduce: --seed {out.get('seed')} --strength {strength}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
