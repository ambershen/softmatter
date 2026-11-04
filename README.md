# Soft Matter

Four material typefaces drawn from everyday objects, in five weights each (Light 300, Regular 400, Medium 500, Bold 700, Black 900).

| Face | Material | Idea |
| --- | --- | --- |
| **Purl** | Knitting | Freehand letters knitted into a sweater, one even strand of yarn, stitch by stitch. |
| **Ganache** | Piped chocolate | One continuous squeeze from a piping bag, thick where you press and thin where you let go. |
| **Nacre** | Pearls | Pearls knotted on silk in a joined French hand: big pearls on the downstrokes, seed pearls on the hairlines. |
| **Picot** | Lace ribbon | A lace ribbon pinned into letters, opening into tulle and eyelets where the stroke is thick. |

The site has three views:

- **Typefaces**: live specimens with weight, colorway, custom colours and material controls, plus downloads (font family, PNG lettering, glyph pack, @font-face code) on every card.
- **Soft Matter (demo)**: a fictional winter market site set in the four faces.
- **Laundromat**: pick one of four washing machines (cocoa, wool, pearl, lace); each wash turns out a one-off object lettered in that face, which you can hang on the line or download.

The material renders are procedural (Canvas 2D, plus Three.js for the 3D pieces). The Laundromat's door swings, empty drums and pearl heap are Blender renders registered to the room photo; `tools/laundromat.py` regenerates them into `assets/laundry/` (usage is at the top of the script). The `.otf` files are monochrome outline versions generated from the same data with [opentype.js](https://github.com/opentypejs/opentype.js).

## Fonts

Ready-made files are in [`fonts/`](fonts/): `SoftMatter{Purl,Ganache,Nacre,Picot}-{Light,Regular,Medium,Bold,Black}.otf`.

Purl, Ganache and Picot set in capitals. Nacre keeps upper and lower case and joins like handwriting.

Nacre is traced from [Parisienne](https://fonts.google.com/specimen/Parisienne) by Astigmatic and is released under the SIL Open Font License 1.1; see [`fonts/OFL-Nacre.txt`](fonts/OFL-Nacre.txt).

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
