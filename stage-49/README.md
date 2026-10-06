# Chapter 49

Open `http://127.0.0.1:8765/#chapter-49` in the shared website.
**49-1 through 49-80** are represented by 24 formation cards from 24 source
messages. Each card preserves the exact 5×5 positions, forms and variants;
the stage label links to the Discord reference.

Observed Tatari levels are 1001 for 49-1–49-4, 1010 for 49-5–49-9,
1019 for 49-10–49-59, 1053 for 49-60, and 1056 for 49-61–49-80.
These levels were read from multiple deployed inventory cards and are not
verified server-wide minimum clear levels. Each individual deployed unit's
level was not separately readable. Clear outcomes are author-reported.

The first caption says **49-1 to 49-5**, but its screenshot displays 49-5
and the following source covers 49-5 through 49-9. Using the established
next-stage screenshot convention, the first formation is conservatively
assigned to 49-1 through 49-4 and flagged `check range`. The original caption
and its endpoint are preserved in `caption_stage_range`, `message_text` and
the raw browser observations. This source remains in `needs_human_review`.
The other 23 sources are in `high_confidence`.

`stage-49-lineups.json` preserves all 80 stage entries and 24 source records,
including message IDs, permalinks, timestamps, captions, credited names,
original image paths, levels, forms, tiers, variants and coordinates.
`reviewed-formations.json` contains the manually reviewed boards.
`evidence/images/` contains original screenshots; review sheets and
`evidence/website-chapter-49.png` document the visual checks.

All requested stages were found in the supplied thread, so no fallback
Discord search was needed. Collection used existing account permissions via
the read-only Discord website workflow. Posting display name is `nil`;
account usernames were not verified. Saved originals preserve traceability
when attachment URLs expire. Raw evidence remains outside the served root.

Rebuild all chapters with:

```sh
python3 /Users/kaichinh/ClashCrittersCollection/stage-47/build_site.py
```

The website is also available offline at `../stage-47/site/index.html`.
Browser verification confirmed 80 chapter 49 stage labels, 24 cards and all
Tatari images loaded, without horizontal overflow or console warnings/errors.
