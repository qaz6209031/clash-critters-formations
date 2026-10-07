# Chapter 31 formations

[Live chapter](https://kaichin.dev/clash-critters-formations/#chapter-31)

All **31-1 through 31-80** have source-caption coverage in **37 grouped
formation cards from 38 source posts**. Exact forms, tiers, Glitter variants
and positions determine grouping. Cards show the stage range, observed level,
posting display name and 5×5 grid. Both stage and poster links open the source.

## Levels and selection

- 31-1–31-9: level 579, readable in the screenshots.
- 31-10–31-12: level 596 reported only in the caption; needs human review.
- 31-13–31-22: level 596, readable in the screenshots.
- 31-23–31-24: level 597, readable in the screenshots.
- 31-25–31-46: level 600, readable in the screenshots.
- 31-47–31-80: level 604, readable in the screenshots.

The posting author is `Casey | 31150710` in the `Chapter 19 and onwards`
thread. Discord username is unverified. Chapter searches with `has:image`
compared Harsh, Win, Unown, Antzer and opening-stage candidates. Harsh’s
recommended `harsh5200` chapter thread reports level 637. Other inspected
opening candidates showed Win 594, Antzer 598, Unown 600 and Dokeshi 603.
Casey’s opening screenshots show 579 and later screenshots remain below
the inspected readable alternatives. This establishes the lower observed
levels among inspected candidates, not a server-wide minimum or required level.

Win’s 31-5–31-9 caption says 549, but no readable inventory level was shown.
That unverified caption was excluded from screenshot-level comparisons;
it was neither assumed correct nor silently corrected to another number.
Original formation credits in Casey’s captions are stored separately:
jacobdumbnut, Harsh and Layios. `Posted by` identifies Casey, not the
credited reference creator.

## Evidence and review

37 source records are high confidence and one needs human review.
The 31-10–31-12 caption reports 596, while its attachment displays 31-15 and
contains no visible inventory-level text. Its exact attached board, including
Glitter Tideon, is preserved; stage attribution and level remain flagged.
The level tooltip and structured record explain this limitation without
adding text beneath the visible level number.

Other captions provide the cleared stages; screenshots normally show the
next stage. The first caption covers 30-80 through 31-1, with a screenshot
displaying 31-1, so its additional 31-1 clear relies on the author’s statement.
Captures for 31-20–31-21, 31-25–31-29, 31-30–31-31, 31-50–31-52,
31-60–31-64 and 31-70–31-74 were taken partway through the captioned range;
later endpoints also rely on the caption. Those screenshot-stage values and
assignment notes are retained. 31-80 shows 32-1 and no enemy-level number.

Rows run front to rear and columns left to right. Empty front rows are
preserved. Only deployed Tatari are transcribed; enemy portraits and inventory
cards are not counted in the board. Exact T2 forms are retained, including
Clawzor, Ospisces, Synthhog and Voltling. Clears were not independently played.

## Files and verification

`reviewed-formations.json` contains the reviewed boards. Sanitized publication
metadata is in `../data/source-index.json`, including timestamps, captions,
posting display names and message permalinks. Original attachments, raw browser
captures and screenshots remain local under ignored `evidence/`. Generated
`stage-31-lineups.json` and `../lineups.json` retain richer local evidence.

The shared builder checks complete stage coverage, unique source IDs, valid
catalog forms and expected deployed counts. Chapter 31 covers 80 unique stages;
the preceding 880 stage mappings are unchanged. GitHub Pages deploys only
`stage-47/site`. A fresh checkout can rebuild without private evidence.

Rebuild with `python3 stage-47/build_site.py` from the project root.
Collection used only the existing authenticated Discord website session,
without modifying Discord content.
