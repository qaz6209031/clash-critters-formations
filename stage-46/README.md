# Chapter 46 formations

The shared local website covers **46-1 through 46-80** in **23 grouped
formations**, from 24 messages in the supplied Discord reference thread.
Each card shows the stage/range, observed Tatari level and exact 5×5 grid.
The 46-10 and 46-11 through 46-14 sources have identical forms, variants and
positions, so their card is grouped as 46-10 through 46-14. Both source
records remain in the JSON.

Open `../stage-47/site/index.html`, or visit
`http://127.0.0.1:8765/#chapter-46`.

## Evidence and levels

46-1 through 46-4 show Tatari level 955; 46-5 through 46-80 show level 969.
These are observed levels read from multiple deployed inventory cards,
not established server-wide minimum clear levels. Each individual unit's
level was not separately readable.

Captions assign the cleared stages. All 24 screenshots display the next
stage, including 47-1 after clearing 46-80. All boards contain 15 deployed
Tatari; enemy portraits and undeployed inventory are excluded. Rows run
from front to rear, with columns left to right. Exact forms, glitter
variants and positions were visually matched to the supplied horde planner
catalog. The author reports the clears; they were not independently played.

All requested stages were available in the reference thread, so the fallback
Discord search was not needed. Only the existing account's Discord website
access was used, without modifying Discord content.

## Files

- `stage-46-lineups.json`: 80 stage entries and 24 high-confidence source
  submissions; no records require human review in this chapter. Includes
  message IDs, permalinks, timestamps, captions, saved-image references,
  exact form IDs, tiers, variants, grid coordinates and observed levels.
- `reviewed-formations.json`: manually reviewed boards and screenshot metadata.
- `evidence/raw-browser-sources.json`: the 24 browser observations.
- `evidence/images/`: saved original attachments outside the served web root.
- `evidence/`: board crops, review sheets, tier comparisons and
  `website-chapter-46.png`.
- `../lineups.json`: the combined chapter 44–50 dataset.

The posting display name is `nil`; the account username was not verified.
The first source uses Discord's grouped-message author header, with its
capture basis saved in the raw observation. Credited caption names are
separate from Discord identities. Confidence values are manual review
scores, not calibrated probabilities. Original attachments preserve source
evidence when remote attachment URLs expire.

## Rebuild and preview

```sh
python3 /Users/kaichinh/ClashCrittersCollection/stage-47/build_site.py
python3 -m http.server 8765 --bind 127.0.0.1 --directory /Users/kaichinh/ClashCrittersCollection/stage-47/site
```

The offline website embeds its artwork and covers all 560 stages in chapters
44–50. Browser verification confirmed chapter 46's 23 cards, all 80 stage
labels and levels. Across the 162-card site, all 2,430 images loaded, with
no console warnings/errors or horizontal overflow.
