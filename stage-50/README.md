# Chapter 50

Open `http://127.0.0.1:8765/#chapter-50` in the shared website.
**50-1 through 50-80** are represented by 22 formation cards from 24 source
messages. Identical forms, variants and positions are grouped for
**50-30–50-34** and **50-60–50-64**; all original submissions remain separate
records with their own message IDs and image evidence.

Observed Tatari levels are 1056 for 50-1–50-4, 1110 for 50-5–50-39, and
1121 for 50-40–50-80. These are source screenshot levels, not verified
server-wide minimum clear levels. Each individual deployed unit's level was
not separately readable. Clear outcomes are author-reported.

The 50-40 author says the original screenshot was missed. Its screenshot
displays 50-43 and level 1121, so the card is labeled `recreated` and the
record is in `needs_human_review`. Its original clear level is unverified.
The other 23 sources are in `high_confidence`. Standard screenshots display
the next stage; the 50-80 source displays 51-1.

`stage-50-lineups.json` preserves all 80 stage entries and 24 source records,
including message IDs, permalinks, timestamps, captions, credited names,
original image paths, levels, forms, tiers, variants and coordinates.
`reviewed-formations.json` contains the manually reviewed boards.
`evidence/images/` contains original screenshots; review sheets and
`evidence/website-chapter-50.png` document the visual checks.

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
Browser verification confirmed 80 chapter 50 stage labels, 22 grouped cards
and all Tatari images loaded, without horizontal overflow or console warnings/errors.
