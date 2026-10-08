# Chapter 31 formations

[Live chapter](https://critterformations.com/#chapter-31)

All **31-1 through 31-80** have source-caption coverage in **37 grouped
formation cards from 38 selected posts**. All **39 collected source records**
are preserved, including the older Win alternative. Only sources posted after
August 27, 2026 qualify for the website. Exact forms, tiers, Glitter variants
and positions determine grouping. Cards show the stage range, observed level,
posting display name and 5×5 grid. Both stage and poster links open the source.

## Levels and selection

- 31-1–31-4: level 579, readable in the screenshots.
- 31-5–31-9: Casey’s September level 579, readable in the screenshots.
- 31-10–31-12: level 596 explicitly typed by Casey; stage attribution needs review.
- 31-13–31-22: level 596, readable in the screenshots.
- 31-23–31-24: level 597, readable in the screenshots.
- 31-25–31-46: level 600, readable in the screenshots.
- 31-47–31-80: level 604, readable in the screenshots.

The posting authors are `Casey | 31150710` in the `Chapter 19 and onwards`
thread and `win | waveflutter <3` in the post-update chapter guide.
Discord usernames are unverified. Chapter searches with `has:image`
compared Harsh, Win, Unown, Antzer and opening-stage candidates. Harsh’s
recommended `harsh5200` chapter thread reports level 637. Other inspected
opening candidates showed Win 594, Antzer 598, Unown 600 and Dokeshi 603.
Casey’s opening screenshots show 579 and later screenshots remain below
the other inspected alternatives. Win’s explicit level-549 post was dated
August 17 and is excluded under the publication cutoff. Casey’s September
references replace it for 31-5–31-9.
Levels are supported observations, not a server-wide minimum or required level.

Use a formation only when its level is readable in the image or explicitly
typed in its source post. Win’s 31-5–31-9 caption says `lvl 549`, which was
accepted during the earlier collection even though no image-level number was visible.
Its original posting date now excludes it from the website.
The author’s number is preserved exactly. `tatari_level_source` distinguishes
`image` from `message_text`; typed levels retain `tatari_level_quote`.
Levels are not inferred from adjacent posts or enemy levels.
Casey’s level-579 records for this range now have
`selected_for_website: true`; Win’s archived record is unselected.
No submission was deleted or marked as author-superseded.
Original formation credits in Casey’s captions are stored separately:
jacobdumbnut, Harsh and Layios. `Posted by` identifies Casey, not the
credited reference creator; the selected 31-5–31-9 cards identify Casey.

## Evidence and review

38 source records are high confidence and one needs human review.
The 31-10–31-12 caption reports 596, while its attachment displays 31-15 and
contains no visible inventory-level text. Level 596 is accepted from the
explicit caption. Its exact attached board, including Glitter Tideon, is
preserved; only stage attribution remains flagged.
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

The shared builder checks the posting-date cutoff, unique stage mappings, valid
catalog forms and expected deployed counts. Chapter 31 covers 80 unique stages;
earlier chapter stages without newer references are hidden. GitHub Pages deploys only
`stage-47/site`. A fresh checkout can rebuild without private evidence.

Rebuild with `python3 stage-47/build_site.py` from the project root.
Collection used only the existing authenticated Discord website session,
without modifying Discord content.
