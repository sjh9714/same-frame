---
name: same-frame
description: Re-render an image the user already has under new light, a new palette, or a new medium, while the composition stays exactly where it was. Use when asked to relight a photo, recolour an illustration, or convert something to gouache, cyanotype, blueprint, or another medium without changing its contents. Also use when asked to remove or add an object in an image, or to put the same character in a new scene — both are measured failures and this skill refuses them with evidence rather than burning the user's money.
---

# same-frame

Krea 2 image-to-image changes **how a scene is rendered**. It does not change **what is in the scene**. Every recipe and every refusal below comes from 114 real generations with the seeds recorded.

## Before doing anything: classify the request

Read what the user is actually asking for and put it in one of three buckets.

**Bucket 1 — rendering change. Proceed.**
Light direction, light colour, number of light sources, palette, medium, rendering style. The set of objects in the frame is identical before and after.

**Bucket 2 — content change. Refuse.**
The user wants something in the frame that is not there, or wants something gone that is. Do not run it. Do not try a higher strength. Go to *Refusals* below.

**Bucket 3 — identity carry. Refuse.**
The user wants a specific person or character to appear in a new image. Go to *Refusals* below.

If a request mixes buckets ("relight this and remove the powerline"), do the bucket-1 half, and tell the user the other half needs a different tool. Do not silently drop it.

## Running a recipe

1. Read `recipes.json`. Pick the recipe whose `changes` field matches the request.
2. Fill the `slots`. Every slot is there because leaving it vague measurably degraded the result — name the concrete thing that must not move.
3. Use the recipe's `strength` verbatim. These are not starting points, they are the values that produced the paired image in `examples/`. The working band is 0.50–0.60 and it is narrow.
4. Run it:

```bash
python3 same_frame.py --image <path-or-url> --recipe <id> --out result.png
```

Or with a prompt you wrote yourself, still inside the band:

```bash
python3 same_frame.py --image ref.png --prompt "..." --strength 0.55 --out result.png
```

`FAL_KEY` is read from a `.env` file next to the script, or from the environment. Roughly $0.008 per megapixel, so a 1024×1024 edit is about eight tenths of a cent.

## Writing your own prompt for a rendering change

Two things separate the kept edits from the cut ones.

**Name what must not move, explicitly.** Not "keep the composition" — say "every terrace contour stays in exactly the same position", "the rock placement, horizon line and framing identical", "every component in exactly the same position and spacing". The kept edits all did this. The phrasing is doing real work.

**Say the change is the only change.** "only the medium changes", "Change only the time and mood". Without it the model treats your instruction as a suggestion and drifts elsewhere.

Concrete beats atmospheric. Three named colours ("deep violet water, salmon sky, warm cream foam") hold. "Make it moodier" does not.

## Refusals

These are the whole point of this skill. Say no, show the evidence, name the tool that would work.

### Object add or remove — refuse

> Krea 2 does not add or remove objects, and turning up strength does not fix it — it just replaces your subject with a different one. I asked it to remove the steam from a mug at strength 0.5 and the steam came back (`examples/refuse-removal-after.webp`, seed 1499506316). Adding snow to a coastline returned the same coastline slightly cooler. Darkening a sky returned the same sky.
>
> This is a masking problem, not a strength problem. Use an inpainting model with a mask over the region.

### Same character in a new scene — refuse

> The same person cannot be carried into a new photograph, and there is no strength value that does it. At 0.45 the face survives but the source composition comes with it — a three-view studio reference sheet became the same three views at a harbour. At 0.72 you get a genuinely new scene and a different person; only the sweater and the palette carried over (`examples/refuse-identity-after.webp`, seed 1317515569).
>
> Train a LoRA. Prompting cannot do this.

Do not soften these into "it may be inconsistent". They were run. They failed. The user is deciding whether to spend money and time, and a hedge costs them both.

## Reproducing a result

The endpoint is deterministic. Two runs at the same seed, strength, prompt and input bytes came back differing on **0 of 1,048,576 pixels**. So if a re-run looks different, something about the input changed — and for image-to-image the input includes the source file itself.

This bites in a specific way: feeding a lossy WebP copy of the PNG an edit was originally made from moved the result by **17.0/255** mean per-pixel. The composition, the palette and the medium all came back. The brush texture did not.

Tell the user to keep the original file if they intend to re-run. For image-to-image, the seed alone does not reproduce a generation — the seed *and the exact input bytes* do.

## What is verified and what is not

Verified: the five recipes, at the stated strengths, on the paired images in `examples/`. Each ran once, no cherry-picking across seeds. Determinism was measured directly, twice.

Not verified: whether these strengths transfer to Krea 2 non-turbo, to other models, or to aspect ratios far from square. The band is a Krea 2 Turbo measurement. If you use a different model, re-measure before trusting the number — and say so rather than carrying the number over.
