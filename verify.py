#!/usr/bin/env python3
"""
verify.py — fail if the READMEs contradict recipes.json.

Why this exists: `medium-gouache` was demoted from `holds` to `partial` on
2026-07-27 after a character test. The English README and the launch copy were
updated. `README_ZH.md` was not, and for three days the repository asserted
`holds: 2` in Chinese and `holds: 1` in English, with the Chinese table pointing
at a "see below" section that did not exist. Nothing caught it because nothing
was checking.

A tier is a claim about a measurement. If two files disagree, at least one of
them is lying to a reader, and the reader cannot tell which.

    python3 verify.py          # exit 1 on any contradiction
"""

from __future__ import annotations

import json
import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parent
READMES = ["README.md", "README_ZH.md"]

# Aggregate counts written in prose go stale silently, so any surviving instance
# is an error rather than something to re-derive.
STALE_AGGREGATES = [
    (r"\b(\d+)\s+holds?\b", "English tier tally"),
    (r"(\d+)\s*个成立", "Chinese tier tally"),
]


def main() -> int:
    recipes = {r["id"]: r["tier"] for r in
               json.loads((REPO / "recipes.json").read_text(encoding="utf-8"))["recipes"]}
    fails: list[str] = []

    for name in READMES:
        path = REPO / name
        if not path.exists():
            fails.append(f"{name}: missing")
            continue
        text = path.read_text(encoding="utf-8")

        for rid, tier in recipes.items():
            m = re.search(rf"^\|\s*`{re.escape(rid)}`\s*\|\s*\*{{0,2}}(\w+)\*{{0,2}}\s*\|",
                          text, re.M)
            if not m:
                fails.append(f"{name}: `{rid}` has no table row")
            elif m.group(1) != tier:
                fails.append(f"{name}: `{rid}` table says {m.group(1)}, "
                             f"recipes.json says {tier}")

        # A prose tally duplicates the table and is what actually drifted.
        for pattern, label in STALE_AGGREGATES:
            for hit in re.finditer(pattern, text):
                n = int(hit.group(1))
                actual = sum(1 for t in recipes.values() if t == "holds")
                if n != actual:
                    fails.append(f"{name}: {label} says {n}, actual holds = {actual} "
                                 f"({hit.group(0)!r})")

        for rel in re.findall(r'src="(examples/[^"]+)"', text):
            if not (REPO / rel).exists():
                fails.append(f"{name}: references missing image {rel}")

    if fails:
        print("verify.py FAILED")
        for f in fails:
            print("  ", f)
        return 1

    tally = {t: sum(1 for v in recipes.values() if v == t) for t in sorted(set(recipes.values()))}
    print(f"verify.py OK — {len(recipes)} recipes, {tally}, "
          f"{len(READMES)} READMEs consistent")
    return 0


if __name__ == "__main__":
    sys.exit(main())
