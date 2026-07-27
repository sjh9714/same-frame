<h1 align="center">same-frame</h1>

<div align="center">

[![stars](https://img.shields.io/github/stars/sjh9714/same-frame?style=flat&color=1f5d4c)](https://github.com/sjh9714/same-frame/stargazers)
[![gallery](https://img.shields.io/badge/gallery-before%20%2F%20after-1f5d4c)](https://sjh9714.github.io/same-frame/)
[![license](https://img.shields.io/badge/license-MIT-1f5d4c)](LICENSE)

**Geometry is locked. Material is not.**

**5 Krea 2 image-to-image recipes · every strength and seed recorded · each re-run against a source it was not derived from, and the tier is that result**

1 holds · 1 conditional · 2 partial · 1 narrow · 2 refusals with the evidence

Run it as a one-line script, or drop it in as an agent skill for Claude Code and Codex.

[English](README.md) | [中文](README_ZH.md) · [**Before/after gallery →**](https://sjh9714.github.io/same-frame/)

</div>

<p align="center">
<img src="demo.webp" width="560" alt="Three source images crossfading into their re-rendered versions: terraced fields becoming a gouache painting, a woodblock wave recoloured to three named colours, and an exploded camera diagram rendered as a cyanotype print. In each one the composition does not move.">
</p>

<p align="center"><sub>Real output at the strength and seed printed under each frame.<br>
<a href="https://sjh9714.github.io/same-frame/">See every pair edge to edge →</a></sub></p>

Every strength value is the one that produced the paired image, not a suggested starting point. The working band is **0.50–0.60** and it is narrower than it looks.

The reason this repo exists in this shape: a recipe that only works on the pair it was derived from is a screenshot of one result, not a recipe. So each of the five was run again against an unrelated source, and **the tier column below is that result rather than an estimate**.

---

## The five

| Recipe | Tier | Changes | Strength | Holds up on |
|---|---|---|---|---|
| `medium-gouache` | partial | photograph → gouache, contours in place | 0.60 | subjects, not people — see below |
| `palette-shift` | **holds** | recolour to three named colours | 0.55 | anything, characters included; drop the "flat colour field" clause on photos |
| `relight-hard-sun` | **conditional** | overcast → hard low sun with cast shadows | 0.55 | hard dry materials — tested twice |
| `relight-single-source` | narrow | one warm source, everything else into shadow | 0.50 | enclosures with no live window |
| `medium-cyanotype` | partial | → cyanotype, blueprint or print form | 0.60 | line art and flat photographic subjects |

```bash
python3 same_frame.py --image photo.jpg --recipe medium-gouache \
  --slot subject="these terraced fields" --slot contour="terrace contour" \
  --out out.png
```

The slots are not decoration. Every kept edit named the thing that must not move, in the prompt, explicitly — *"every terrace contour stays in exactly the same position"*, *"the rock placement, horizon line and framing identical"*. Vague sources drifted, so the script will not run a recipe with an unfilled slot. It also warns you before spending a request on a `partial` or `narrow` recipe.

## What "material is not locked" means

<table>
<tr><td width="33%" align="center"><img src="examples/03-before.webp" width="200"><br><sub>wet rice terraces</sub></td>
<td width="33%" align="center"><img src="examples/limit-relight-material-drift.webp" width="200"><br><sub><b>after relight-hard-sun</b></sub></td>
<td width="34%">

`relight-hard-sun` on wet rice terraces, strength 0.55, seed 232270180. Every contour stayed in position and the hard low sun and long shadows arrived exactly as asked.

And the paddies became **dry stone amphitheatre steps**. The water is gone. The vegetation is gone.

Hard light forces the model to re-derive how every surface responds, and a surface that reads as wet under flat light gets re-rendered as dry under hard light. It was invisible on the coastline this recipe came from, because basalt is dry either way.

**Check what things are made of in the output, not just where they are.**

</td></tr>
</table>

## The two it refuses outright

Most prompt collections tell you everything works. These two were run, they failed, and the failures are in this repo.

<table>
<tr><td width="50%">

**Remove or add an object → refused**

<img src="examples/refuse-removal-before.webp" width="150"> <img src="examples/refuse-removal-after.webp" width="150">

Asked at strength 0.5 to remove the steam and let the surface go mirror-flat. The steam came back. Adding snow to a coastline returned the same coastline slightly cooler; darkening a sky returned the same sky.

Turning strength up does not fix this — it replaces your subject instead. **Use inpainting with a mask.**

</td><td width="50%">

**Same character in a new scene → refused**

<img src="examples/refuse-identity-before.webp" width="150"> <img src="examples/refuse-identity-after.webp" width="150">

At 0.72 the scene is genuinely new and the person is not the same; only the sweater and the palette carried over. At 0.45 the face survives but the source composition comes with it — a three-view studio sheet became the same three views at a harbour.

There is no value between them that gives one without the other. **Train a LoRA.**

</td></tr>
</table>

```
$ python3 same_frame.py --image mug.png --prompt "Remove the steam entirely." --strength 0.5

Refusing: Krea 2 does not add or remove objects. Refuse and say why.
  (triggered by 'remove the' — use --force if this read you wrong)

  This was already run at strength 0.5, seed 1499506316:
    asked for: Remove the steam entirely and let the coffee surface go still and mirror-flat.
    got:       The steam came back.
    see:       examples/refuse-removal-after.webp

  Instead: Use an inpainting model with a mask. This is a segmentation problem,
           not a strength problem.
```

Both refusals are overridable with `--force`. The default is the measurement.

## The other limits, with the images

**Gouache holds on a subject and not on a person, and I only found that because I went looking.** This recipe was tiered `holds` on the strength of two out-of-pair runs: a photograph of terraced fields and a line-art camera diagram. Neither of those is *someone*.

<img src="examples/test-anime.webp" width="200"> <img src="examples/limit-gouache-on-character.webp" width="200"> <img src="examples/ok-palette-on-character.webp" width="200">

Run on a cel-shaded illustration of a character (seed 1604078924, strength 0.60) it returns real gouache — chalky paint, visible brush marks, a painted sky — and keeps the pose, the rooftop and the skyline. It also turns dark brown hair blonde, removes the red scarf, replaces the long coat with a different garment and changes the boots. The medium change is correct and **the person is not the same person**.

That is consistent with the refusal two sections up: identity does not survive image-to-image here. On terraces and a camera diagram there is no identity to lose, so the recipe looked unconditional. It is not.

`palette-shift` run on the same source (seed 382435430, strength 0.55) keeps the face, the pose, the coat and the scarf and recolours exactly as asked, so this is specific to re-rendering the marks rather than to characters in general.

Practical rule: gouache on a still life, a landscape, a diagram — fine. Gouache on a character you want to stay recognisable — no.


**`medium-cyanotype` converts photographs too, and the line-art rule that stood here is withdrawn.** That rule rested on a single failure: a coastline photograph (seed 2065751023) held every rock position, went Prussian blue, and produced no line work — a blue-toned photograph, not a blueprint ([`limit-cyanotype-on-photo.webp`](examples/limit-cyanotype-on-photo.webp)).

Two more runs disprove it. On a line-art mandala (seed 1507257657) it produced a proper blueprint-form cyanotype with every petal in place ([`ok-cyanotype-on-lineart.webp`](examples/ok-cyanotype-on-lineart.webp), from [this source](examples/test-lineart.webp)). On a flat, high-contrast **photograph** (seed 2026012845) it produced a proper *photographic* cyanotype print — paper fibre, uneven chemical staining, wash at the edges — with the face exactly preserved ([`ok-cyanotype-on-portrait.webp`](examples/ok-cyanotype-on-portrait.webp), from [this source](examples/test-highcontrast.webp)). A photograph converts fine.

What is **not** established is why the coastline did not. Contrast was the obvious candidate and it runs the wrong way — the coastline source measures a higher standard deviation (74.7) than the portrait (60.4). The visible difference is that the coastline is a deep atmospheric scene and both successes are flat subjects, but that is one image per side, which is a hypothesis and not a finding.

Gouache still runs cleanly in both directions, including onto line art — that part was never in doubt.

**Relighting adds light; it does not take light away.** `relight-single-source` outdoors (seed 1114110846) held the composition and *"everything nearer falling into shadow"* did not happen at all ([`limit-single-source-outdoors.webp`](examples/limit-single-source-outdoors.webp)). Run again on an attic workshop with a skylight (seed 1269377144, [source](examples/test-attic.webp)), it got half way: the work lamps came on and the corners went dark, and **the skylight stayed exactly as bright as before** ([`limit-single-source-daylight.webp`](examples/limit-single-source-daylight.webp)). It also produced two lamps where the prompt said one.

So "interiors only" was too generous, and the real rule is sharper: an existing light source is *content*, switching it off is *removal*, and removal is the thing this model will not do — the same wall as the object-removal refusal, one level down. Use it on corridors, tunnels and windowless rooms. A room with a live window keeps its window.

**And the material caveat is now a tested precondition, not a guess.** `relight-hard-sun` was marked partial off a single failure. Run on a board-formed concrete stairwell (seed 561284942, [source](examples/test-concrete.webp)) it held completely — same treads, same handrail, same skylight, a hard low sun with a clean diagonal shadow down the right wall, and concrete that stayed concrete ([`ok-relight-on-concrete.webp`](examples/ok-relight-on-concrete.webp)). The wet-terrace drift was about the material, not the recipe.

## Install

**As an agent skill**

```bash
npx skills add sjh9714/same-frame
```

Installs for Claude Code, Codex, Cursor, Gemini CLI and a dozen other agents in one go. Or clone it into the skills directory yourself:

```bash
git clone https://github.com/sjh9714/same-frame ~/.claude/skills/same-frame   # or ~/.codex/skills/
```

**Standalone** — no dependencies beyond the standard library:

```bash
git clone https://github.com/sjh9714/same-frame && cd same-frame
printf 'FAL_KEY=%s\n' 'YOUR_KEY' > .env && chmod 600 .env   # do not paste keys into a chat
python3 same_frame.py --list
```

Get a key at [fal.ai](https://fal.ai/dashboard/keys). About **$0.008 per megapixel** — roughly eight tenths of a cent for a 1024×1024 edit. `.env` is gitignored.

**`--list` and `--dry-run` need no key and spend nothing.** The first prints every recipe with its tier, its precondition and its known failure mode; the second prints the assembled prompt.

### Using these without fal.ai

The script is a convenience. **The recipe is the prompt and the strength**, and both are plain text in `recipes.json` — so any Krea 2 image-to-image workflow can run them, local ComfyUI included:

```bash
python3 same_frame.py --recipe medium-gouache --slot subject="these terraced fields" \
    --slot contour="terrace contour" --dry-run
# prints the exact prompt; set denoise/strength to the recipe's value and run it locally
```

Two things to know before you carry a number over. `strength` here is the fal.ai image-to-image parameter; in a ComfyUI graph the equivalent is the KSampler **denoise** value, and while both are nominally "how much of the source survives", **I have not measured that they are the same scale.** And the whole band was measured on Krea 2 **Turbo**. Treat 0.50–0.60 as the place to start looking for your own band, not as a value to copy.

The parts that do transfer without qualification are the prompt phrasing findings — name what must not move, say the change is the only change, and check the source can make the marks you are asking for. Those are about the model, not the endpoint.

## Reproducing a result

The endpoint is deterministic: two runs at the same seed, strength, prompt and input bytes came back differing on **0 of 1,048,576 pixels**.

So if a re-run looks different, the input changed. This bites in one specific way — feeding a lossy WebP copy of the PNG an edit was originally made from moved the result by **17.0/255** mean per-pixel. Composition, palette and medium all returned; brush texture did not. Keep the original file. For image-to-image, the seed alone does not reproduce a generation; the seed *and the exact input bytes* do.

## Where these numbers stop

The band is a **Krea 2 Turbo** measurement on roughly square images. Whether 0.55 means the same thing on Krea 2 non-turbo, on another model, or at 16:9 is untested — re-measure before carrying the number over.

Each recipe was generalisation-tested against exactly **one** unrelated source. That is enough to separate "works" from "only works on what it came from"; it is not enough to map where a `partial` recipe stops.

## Where this came from

Extracted from [awesome-krea-2](https://github.com/sjh9714/awesome-krea-2) — 114 generations, 85 kept, 29 cut, every seed recorded. The two refusals are two of the cuts.

MIT for the code and the prompts. The example images are Krea 2 Turbo output, produced under the Krea 2 Community License, presented as model output rather than as photographs or artwork. The safety checker was enabled on every request.
