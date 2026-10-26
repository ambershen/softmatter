# Soft Matter

Four material typefaces drawn from everyday objects, in five weights each (Light 300, Regular 400, Medium 500, Bold 700, Black 900).

| Face | Material | Idea |
| --- | --- | --- |
| **Purl** | Knitting | Lettering knitted into a sweater, worked stitch by stitch on the knitting grid. |
| **Ganache** | Piped chocolate | Writing with a piping bag on a plate: separate squeezes, tails and drips. |
| **Tangle** | Wired earphones | One loopy cable that can't make a sharp corner, from the earbuds to the plug. |
| **Picot** | Lace ribbon | A lace ribbon pinned into letters, opening into tulle and eyelets where the stroke is thick. |

The site has three views:

- **Typefaces**: live specimens with weight, colorway, custom colours and material controls.
- **Download**: export the font family (.otf), transparent PNG lettering, a per-glyph PNG pack, and @font-face code.
- **Soft Matter (demo)**: a fictional winter market site set entirely in the four faces.

The material renders are procedural (Canvas 2D). The `.otf` files are monochrome outline versions generated from the same skeletons with [opentype.js](https://github.com/opentypejs/opentype.js).

## Fonts

Ready-made files are in [`fonts/`](fonts/): `SoftMatter{Purl,Ganache,Tangle,Picot}-{Light,Regular,Medium,Bold,Black}.otf`.

Tangle is a lowercase joined script; `[` draws a pair of earbuds and `]` the plug, so type `[soft matter]`.

```css
@font-face {
  font-family: "Soft Matter Ganache";
  src: url("fonts/SoftMatterGanache-Bold.otf") format("opentype");
  font-weight: 700;
}
```

## Run locally

It's a static site with no build step:

```sh
npx serve .
```

## Deploy

Import the repo in Vercel (Framework preset: **Other**, no build command, output directory `.`). Every push to `main` redeploys.
