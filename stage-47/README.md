# Stage 44–50 formations

Open `site/index.html` in a browser. This is a standalone offline website;
no installation or server is required. It shows stage names/ranges,
observed Tatari levels and 5×5 formations. Exact forms, variants and cell
positions determine which stages share a card. Hover over a Tatari for its
name and tier; click the stage label for the Discord reference.

The page covers all 80 stages in each of chapters **44, 45, 46, 47, 48, 49 and 50**:
**560 stages in 162 formation cards**, from 168 source messages. Chapter 45
has 21 cards, chapter 46 has 23; chapters 44, 47, 48 and 49 each have 24 cards;
chapter 50 has 22.
Source captions assign the
cleared stage or range. Standard screenshots show the next stage, including
48-1 after clearing 47-80. The enemy portrait panel and the undeployed
inventory are excluded from the formation grids.

## Levels and recreated screenshots

The badges show the player's Tatari level read from multiple deployed
inventory cards, not the enemy's level above the enemy portraits. These
are observed screenshot levels, not a guaranteed minimum level required
to clear a stage. Every unit's individual level was not separately visible.

Chapter 44 shows level 945 for 44-1 through 44-4, 946 for 44-5 through 44-44
and 947 for 44-45 through 44-80. Chapter 45 shows level 953 for 45-1 through 45-44 and 954 for 45-45 through
45-80. Chapter 46 shows level 955 for 46-1 through 46-4 and 969 for 46-5 through
46-80. Chapter 47 shows 969 for 47-1 through 47-9, 983 for 47-10 through
47-14, 984 for 47-15 through
47-50, 994 for 47-51 through 47-74 and 47-80, and 996 in the recreated
47-75 through 47-79 screenshot.

Two captions explicitly say the author forgot the original screenshot and
reconstructed the formation later. Their badges are labeled `recreated`,
and their records are in `needs_human_review`:

- 47-31 through 47-34: screenshot displays 47-40, Tatari level 984.
- 47-75 through 47-79: screenshot displays 48-5, Tatari level 996. The author
  also says the toad is unnecessary; the photographed formation is preserved
  without deleting a unit.

The original clear levels for those two ranges are unverified. All exact
Tatari forms and placements were visually matched to the supplied planner
catalog. Glitter Voltmare T3 and glitter Serrabloom T3 were matched to their
respective glitter sprites. Chapter 47's earlier standard Serrabloom artwork
was corrected during the chapter 48 review. The previous dataset is preserved
at `evidence/stage-47-lineups-before-serrabloom-correction.json`.
No clear was
independently tested in the game.

The first chapter 47 caption says `47-1 to 47-5`, but its screenshot displays
47-5 and the next source begins at 47-5. The first record is conservatively
assigned 47-1 through 47-4 and labeled `check range`; the original caption
endpoint is retained in `caption_stage_range`, and the record requires review.
The pre-extension chapter 47 dataset is preserved at
`evidence/stage-47-lineups-before-1-9-extension.json`.

## Data and evidence

- `stage-47-lineups.json`: 80 stage entries and 24 source records, with
  message IDs, permalinks, timestamps, captions, image references, levels,
  form tiers/variants and grid coordinates. Twenty-one source records have high
  extraction confidence; three require review of the reconstructed clear context
  or opening caption range.
- `reviewed-formations.json`: the manually reviewed source boards and level
  observations used to rebuild the website.
- `../stage-44/stage-44-lineups.json`: 80 stage entries and 24 source records.
- `../stage-45/stage-45-lineups.json`: 80 stage entries and 24 source records.
- `../stage-46/stage-46-lineups.json`: 80 stage entries and 24 source records.
- `../stage-48/stage-48-lineups.json`: 80 stage entries and 24 source records.
- `../stage-49/stage-49-lineups.json`: 80 stage entries and 24 source records.
- `../stage-50/stage-50-lineups.json`: 80 stage entries and 24 source records.
- `../lineups.json`: the combined chapter 44–50 structured dataset, with 163
  high-confidence source records and five requiring human review.
- `evidence/`: original attachments, raw browser observations, board crops,
  level contact sheets and preview screenshots.

The posting display name is `nil`; an account username was not verified.
Credited names come from the captions and are not Discord account identities.
Confidence scores are manual review scores, not calibrated probabilities.

Permalinks use the observed server/thread route and rendered message IDs.
Attachment URLs can expire; saved originals and message IDs preserve
traceability. Source snapshots remain separate from the website. Artwork
is referenced to the user-provided horde planner catalog in the JSON.

## Run or rebuild

```sh
python3 /Users/kaichinh/ClashCrittersCollection/stage-47/build_site.py
```

For an HTTP preview, serve only the finished site folder:

```sh
python3 -m http.server 8765 --bind 127.0.0.1 --directory /Users/kaichinh/ClashCrittersCollection/stage-47/site
```

Visit `http://127.0.0.1:8765/`, or use `/#chapter-44`, `/#chapter-45`, `/#chapter-46`, `/#chapter-47`,
`/#chapter-48`, `/#chapter-49` or `/#chapter-50` to jump to a chapter.
Keep raw evidence outside the served root.
The grouped stage/formation data can later feed a Next.js presentation layer.

Browser verification confirmed all 560 stages across 162 cards, 4,050 grid cells,
162 level badges and 2,430 successfully loaded Tatari images. There was no
horizontal overflow or browser console warning/error. Three recreated
screenshots are labeled, including 50-40. The first chapter 47 and chapter 49
references are labeled `check range`; their caption endpoints conflict with the screenshot
and the following source. The final card is 50-80 at observed Tatari level 1121.
Preview screenshots are saved in each chapter's evidence folder.
