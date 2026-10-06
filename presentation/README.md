# Presentation

The DGLRM talk deck, built from the final report on `feat/report`.

| File | What it is |
|---|---|
| `bed-rest-to-mars-talk.pptx` | The deck: 20 slides. Slides 3–10 are placeholders for Niloufar Ahmadymarzdashty's half; 11–16 are the technical half; 17–20 are backup slides |
| `bed-rest-to-mars-talk.pdf` | PDF preview of the deck |
| `hard-questions.md` | 27 critical audience questions with answers and sources, mapped to the backup slides |
| `presentation-plan.md` | Build plan with a definition of success for each phase |
| `technical-half-outline.md` | The first content outline for the technical half (superseded by the deck) |
| `build_talk.js` | Script that generates the deck with pptxgenjs |
| `dglrm_logo_schrift2_ret.png` | DGLRM conference logo, used on the title slide and in every footer |
| `example.json` | The cached LLM request and answer shown on slide 13 (the row with the median LLM error) |

Every number on the slides comes from `results/` on `feat/report`. On the slides the language model is called "the LLM", never by its product name.

To rebuild: `npm install pptxgenjs`, then `APPLY_THEME=/path/to/apply_theme.js node build_talk.js`. `apply_theme.js` writes the theme colours into the deck after pptxgenjs saves it.

## Image sources (slide 4)
`planet-earth.png`, `planet-moon.png` and `planet-mars.png` are globes rendered from texture maps: Earth from NASA Blue Marble (public domain, via the three-globe repository), the Moon from the three.js example texture `moon_1024.jpg`, and Mars from the threex.planets `marsmap1k.jpg` map (Planet Pixel Emporium, built from NASA imagery). Check the Moon and Mars licences before publishing the slides beyond the talk.
