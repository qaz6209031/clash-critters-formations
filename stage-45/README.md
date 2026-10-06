# Chapter 45 formations

The shared local website covers **45-1 through 45-80** in **21 grouped
formations**, from 24 messages in the supplied Discord reference thread.
Each card shows the stage/range, observed Tatari level and exact 5×5 grid;
its stage label links to the Discord source.

Open `../stage-47/site/index.html`, or visit
`http://127.0.0.1:8765/#chapter-45`.

## Evidence and levels

45-1 through 45-44 show Tatari level 953; 45-45 through 45-80 show level 954.
These are observed levels from multiple deployed inventory cards, not
established minimum clear levels. Individual levels were not separately
readable for every deployed Tatari.

All 24 captions assign the cleared stages and all screenshots display the
next stage, including 46-1 after clearing 45-80. No reconstructed screenshots
or ambiguous caption ranges were found in this chapter. The author reports
the clears; they were not independently played. All stages were available
in the reference thread, so a fallback Discord search was not needed.

Each board contains 15 deployed Tatari. Rows run front to rear; columns run
left to right. Enemy portraits and undeployed inventory are excluded. Forms,
tiers, glitter variants and placements were visually matched to the supplied
horde planner catalog. Both Serrabloom and Voltmare use their glitter artwork
where those variants appear.

Exact matches are grouped as 45-40 through 45-44, 45-50 through 45-54 and
45-60 through 45-64. Each original source remains a separate record. The
45-70 and 45-71 through 45-74 boards remain separate because Solaflora occupies
different cells.

## Files

- `stage-45-lineups.json`: 80 stage entries, 24 high-confidence source records
  and an empty `needs_human_review` array. Includes message IDs, permalinks,
  timestamps, captions, saved-image references, forms, tiers, variants,
  grid coordinates and levels.
- `reviewed-formations.json`: manually reviewed boards and screenshot metadata.
- `evidence/raw-browser-sources.json`: the 24 browser observations.
- `evidence/images/`: original attachments outside the served web root.
- `evidence/`: board crops, six review sheets, the finished website screenshot
  and `lineups-before-chapter-45.json`, preserving the preceding combined data.
- `../lineups.json`: the combined chapter 44–50 dataset.

The posting display name is `nil`; the account username was not verified.
Credited caption names remain separate from Discord identities. Confidence
values are manual review scores, not calibrated probabilities. Saved originals
preserve evidence when remote attachment URLs expire. Collection used only
the authenticated Discord website and did not modify Discord content.

## Rebuild and preview

```sh
python3 /Users/kaichinh/ClashCrittersCollection/stage-47/build_site.py
python3 -m http.server 8765 --bind 127.0.0.1 --directory /Users/kaichinh/ClashCrittersCollection/stage-47/site
```

The offline website embeds all artwork and now covers 560 stages in chapters
44–50. Verification confirmed all 80 chapter 45 stage labels and levels,
21 cards, source traceability and unchanged preceding chapter records.
All 2,430 images across the 162-card website loaded, with no console warnings,
errors or horizontal overflow.
