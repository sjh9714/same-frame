#!/usr/bin/env python3
"""
build_pages.py — a before/after gallery for GitHub Pages, from recipes.json.

This repo's entire claim is a comparison: the composition is identical and
something else changed. A README renders those pairs as two images the reader
has to mentally align. A page can put them edge to edge at the same size, which
is the only presentation where "every terrace contour stayed in position" is
checkable rather than asserted.

No JavaScript. The measured Show HN pattern is that 67% of posts above 300
points point at a hosted page rather than a repository, and the cheapest way to
have one that never breaks is a single HTML file served from /docs.

    python3 build_pages.py            # writes docs/index.html
"""

from __future__ import annotations

import argparse
import html
import json
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent

CSS = """
:root{--bg:#faf9f7;--fg:#17191a;--mut:#6a6f70;--line:#e0dedb;--acc:#1f5d4c;--bad:#9e2b25;--card:#fff}
@media(prefers-color-scheme:dark){:root{--bg:#111312;--fg:#e9ebe6;--mut:#8b918c;--line:#2a2e2b;--acc:#62bfa1;--bad:#e0776c;--card:#181b19}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.65 -apple-system,BlinkMacSystemFont,"Segoe UI","Apple SD Gothic Neo",Roboto,sans-serif}
.wrap{max-width:1120px;margin:0 auto;padding:0 20px 96px}
header{border-bottom:2px solid var(--fg);padding:56px 0 22px;margin-bottom:40px}
h1{font-size:clamp(1.8rem,4vw,2.5rem);margin:0 0 10px;letter-spacing:-.02em}
.sub{color:var(--mut);max-width:64ch;margin:0}
.meta{margin-top:18px;font:13px/1.7 ui-monospace,SFMono-Regular,Menlo,monospace;color:var(--mut)}
.meta b{color:var(--fg)}
h2{font-size:1.3rem;margin:56px 0 4px;letter-spacing:-.01em}
h2:first-of-type{margin-top:0}
.lede{color:var(--mut);margin:0 0 24px;max-width:72ch;font-size:.94rem}
.pair{background:var(--card);border:1px solid var(--line);border-radius:7px;overflow:hidden;margin:0 0 26px}
.pair .imgs{display:grid;grid-template-columns:1fr 1fr;gap:1px;background:var(--line)}
.pair figure{margin:0;position:relative;background:var(--bg)}
.pair img{width:100%;display:block;aspect-ratio:1;object-fit:cover}
.tag{position:absolute;top:8px;left:8px;background:rgba(0,0,0,.72);color:#fff;font:11px/1 ui-monospace,monospace;padding:5px 7px;border-radius:3px;letter-spacing:.04em}
.body{padding:16px 18px 18px}
.name{font-weight:660;font-size:1rem;margin-bottom:2px}
.tier{display:inline-block;font:11px ui-monospace,monospace;padding:2px 7px;border-radius:99px;border:1px solid var(--line);color:var(--mut);margin-left:8px;vertical-align:2px}
.tier.holds{color:var(--acc);border-color:var(--acc)}
.tier.narrow,.tier.partial{color:var(--bad);border-color:var(--bad)}
pre{margin:10px 0 0;background:transparent;color:var(--mut);font:11.5px/1.55 ui-monospace,SFMono-Regular,Menlo,monospace;white-space:pre-wrap;word-break:break-word}
.k{margin-top:10px;font:11.5px/1.7 ui-monospace,monospace;color:var(--mut)}
.k b{color:var(--fg);font-weight:600}
.note{margin-top:10px;padding-left:12px;border-left:2px solid var(--line);color:var(--mut);font-size:.9rem}
.note.warn{border-color:var(--bad)}
.pair.bad{border-color:var(--bad)}
.pair.bad .name{color:var(--bad)}
a{color:var(--acc)}
footer{margin-top:76px;padding-top:22px;border-top:1px solid var(--line);color:var(--mut);font-size:.9rem;max-width:74ch}
@media(max-width:640px){.pair .imgs{grid-template-columns:1fr}}
"""


def pair_block(before: str, after: str, name: str, tier: str | None,
               prompt: str | None, kv: list[tuple[str, str]],
               notes: list[tuple[str, str]], bad: bool = False,
               before_label: str = "source", after_label: str = "result") -> str:
    L = [f'<div class="pair{" bad" if bad else ""}">', '<div class=imgs>']
    for src, lab in ((before, before_label), (after, after_label)):
        L.append(f'<figure><img loading=lazy src="{html.escape(src)}" alt="{html.escape(lab)}">'
                 f'<span class=tag>{html.escape(lab)}</span></figure>')
    L.append("</div><div class=body>")
    tierhtml = f'<span class="tier {tier}">{tier}</span>' if tier else ""
    L.append(f'<div class=name>{html.escape(name)}{tierhtml}</div>')
    if prompt:
        L.append(f"<pre>{html.escape(prompt)}</pre>")
    if kv:
        L.append('<div class=k>' + " · ".join(f"<b>{html.escape(k)}</b> {html.escape(v)}"
                                              for k, v in kv) + "</div>")
    for cls, text in notes:
        L.append(f'<div class="note {cls}">{html.escape(text)}</div>')
    L.append("</div></div>")
    return "\n".join(L)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default="docs/index.html")
    args = ap.parse_args()

    d = json.loads((HERE / "recipes.json").read_text(encoding="utf-8"))
    out = HERE / args.out
    out.parent.mkdir(parents=True, exist_ok=True)

    # Pages serves /docs AS THE SITE ROOT, so "../examples/x.webp" escapes the
    # served tree and every image 404s. Copy them in instead.
    src_dir = HERE / "examples"
    dst_dir = out.parent / "examples"
    dst_dir.mkdir(parents=True, exist_ok=True)
    for f in src_dir.glob("*.webp"):
        shutil.copy2(f, dst_dir / f.name)

    n_hold = sum(1 for r in d["recipes"] if r["tier"] == "holds")
    L = ['<!doctype html><html lang="en"><head><meta charset="utf-8">',
         '<meta name="viewport" content="width=device-width,initial-scale=1">',
         "<title>same-frame — five Krea 2 re-render recipes, and where each one stops</title>",
         '<meta name="description" content="Five image-to-image recipes with recorded strengths and seeds, '
         'each re-tested against a source it was not derived from, two of them twice.">',
         f"<style>{CSS}</style></head><body><div class=wrap>"]

    L.append("<header>")
    L.append("<h1>Geometry is locked. Material is not.</h1>")
    L.append('<p class=sub>Five Krea 2 image-to-image recipes, side by side with their sources at the '
             'same size, so "every contour stayed in position" is something you can check rather than '
             'something I assert. Each one was then re-run against an image it was <em>not</em> derived '
             'from — that is the tier badge.</p>')
    n_second = sum(1 for r in d["recipes"] if r.get("generalisation", {}).get("second_test"))
    L.append(f'<p class=meta>{len(d["recipes"])} recipes · <b>{n_hold} hold outside their own pair</b> · '
             f'{n_second} tested on a third source · {len(d["refusals"])} refusals · '
             f'{len(d["limits"])} documented limits · every strength and seed recorded'
             f' · <a href="https://github.com/sjh9714/same-frame">github.com/sjh9714/same-frame</a></p>')
    L.append("</header>")

    L.append("<h2>The recipes</h2>")
    L.append(f'<p class=lede>{html.escape(d["generalisation"]["_what"])}</p>')
    for r in d["recipes"]:
        g = r.get("generalisation", {})
        notes = []
        if g.get("held"):
            notes.append(("", f"Outside its own pair, on {g['tested_on']}: {g['held']}"))
        if g.get("drifted"):
            notes.append(("warn", g["drifted"]))
        # Show the prompt that actually made this pair, not the slotted template.
        # A reader looking at two images wants the text that produced the one on
        # the right; {subject} is for the tool, not for them.
        L.append(pair_block(r["example"][0], r["example"][1], r["name"], r["tier"],
                            r.get("example_prompt") or r["prompt"],
                            [("strength", str(r["strength"])), ("seed", str(r["seed"]))],
                            notes))

    L.append("<h2>What the tier means, in images</h2>")
    L.append('<p class=lede>The composition is right in all three of these. That is the trap — a result '
             'can be geometrically perfect and still not be what was asked for.</p>')
    for r in d["recipes"]:
        g = r.get("generalisation", {})
        if r["tier"] == "holds" or not g.get("example"):
            continue
        # fall through to the pair block below
        L.append(pair_block(r["example"][0], g["example"],
                            f"{r['name']} — run on {g['tested_on']}", None, None,
                            [("strength", str(g["strength"])), ("seed", str(g["seed"]))],
                            [("warn", g["drifted"]), ("", g["why"])],
                            bad=True, before_label="recipe was built on this",
                            after_label="run on something else"))

    L.append("<h2>The two it refuses</h2>")
    L.append('<p class=lede>Both were run. Both failed. The skill blocks these before the request is '
             'spent and shows you the image below.</p>')
    for rf in d["refusals"]:
        ev = rf["evidence"]
        notes = [("warn", f"got: {ev['got']}"), ("", f"instead: {rf['instead']}")]
        if rf.get("why_no_setting_works"):
            notes.insert(1, ("", rf["why_no_setting_works"]))
        L.append(pair_block(ev["example"][0], ev["example"][1], rf["verdict"], None,
                            f"asked for: {ev['asked']}",
                            [("strength", str(ev["strength"])), ("seed", str(ev["seed"]))],
                            notes, bad=True, after_label="what came back"))

    seconds = [(r, r["generalisation"]["second_test"]) for r in d["recipes"]
               if r.get("generalisation", {}).get("second_test")]
    if seconds:
        L.append("<h2>Tested twice</h2>")
        L.append('<p class=lede>A "use when" drawn from a single failure is a guess wearing the '
                 'clothes of a measurement. These two were run again on another unrelated source. '
                 'One held and got sharper; the other turned out to be stated too generously.</p>')
        for r, t in seconds:
            L.append(pair_block(r["example"][0], t["example"],
                                f"{r['name']} — {t['tested_on']}", r["tier"], None,
                                [("strength", str(t["strength"])), ("seed", str(t["seed"]))],
                                [("", t["result"]), ("", t["means"])],
                                bad=(r["tier"] != "conditional"),
                                before_label="recipe was built on this",
                                after_label="second unrelated source"))

    det = d["determinism"]
    L.append("<h2>Reproducing any of this</h2>")
    L.append(f'<p class=lede>{html.escape(det["measured"])} {html.escape(det["so"])} '
             f'{html.escape(det["practical"])}</p>')

    L.append('<footer>Prompts and code are MIT. The images are Krea 2 Turbo output, produced by the '
             'repository owner under the Krea 2 Community License and presented as model output rather '
             'than as photographs or human artwork. The safety checker was enabled on every request. '
             'Extracted from <a href="https://github.com/sjh9714/awesome-krea-2">awesome-krea-2</a>, '
             'where the same generations are catalogued with their failures.</footer>')
    L.append("</div></body></html>")

    out.write_text("\n".join(L), encoding="utf-8")
    print(f"wrote {out} ({out.stat().st_size // 1024} KB)")
    print("Enable Pages: Settings -> Pages -> Deploy from branch -> main / docs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
