# Chapter 44 formations

The shared local website covers **44-1 through 44-80** in **24 distinct
formations**, from 24 messages in the supplied Discord reference thread.
No exact boards repeat within this chapter. Each card shows its stage/range,
observed Tatari level and exact 5×5 grid, with a link to the Discord source.

Open `../stage-47/site/index.html`, or visit
`http://127.0.0.1:8765/#chapter-44`.

## Evidence and levels

- 44-1 through 44-4: Tatari level 945.
- 44-5 through 44-44: Tatari level 946.
- 44-45 through 44-80: Tatari level 947.

Levels were read from multiple deployed inventory cards. They are observed
source levels, not established minimum clear levels; individual levels were
not separately readable for every deployed Tatari.

All 24 captions assign the cleared stages and all screenshots show the next
stage, including 45-1 after clearing 44-80. No reconstructed screenshots or
ambiguous caption ranges were found. The author reports the clears; they
were not independently played. All stages were available in the reference
thread, so a fallback Discord search was not needed.

Each board contains 15 deployed Tatari. Rows run front to rear and columns
run left to right. Enemy portraits and undeployed inventory are excluded.
Exact forms, tiers, variants and placements were visually matched to the
supplied horde planner catalog. Serrabloom and Voltmare use their glitter
artwork where those variants appear.

The author later says some formations were adjusted without identifying
which. Caption credits are retained as written, separate from Discord
identities. The following comment is saved in `evidence/following-context.txt`,
with its permalink retained in the final source record's notes.

## Files

- `stage-44-lineups.json`: 80 stage entries and 24 high-confidence source
  records; no records need human review in this chapter. Includes message IDs,
  permalinks, timestamps, captions, saved-image references, exact forms,
  tiers, variants, grid coordinates and observed levels.
- `reviewed-formations.json`: manually reviewed boards and screenshot metadata.
- `evidence/raw-browser-sources.json`: the 24 browser observations.
- `evidence/images/`: original attachments outside the served web root.
- `evidence/`: board crops, six review sheets, `website-chapter-44.png` and
  `lineups-before-chapter-44.json`, preserving the preceding combined dataset.
- `../lineups.json`: the combined chapter 44–50 dataset.

The posting display name is `nil`; the account username was not verified.
Confidence values are manual review scores, not calibrated probabilities.
Saved originals preserve evidence when remote attachment URLs expire.
Collection used only the authenticated Discord website and did not modify
Discord content.

## Rebuild and preview

```sh
python3 /Users/kaichinh/ClashCrittersCollection/stage-47/build_site.py
python3 -m http.server 8765 --bind 127.0.0.1 --directory /Users/kaichinh/ClashCrittersCollection/stage-47/site
```

The offline website embeds all artwork and covers 560 stages in chapters
44–50. Verification confirmed all 80 chapter 44 stage labels and levels,
24 cards, source traceability and unchanged preceding chapter records.
All 2,430 images across the 162-card website loaded, with no console warnings,
errors or horizontal overflow.
