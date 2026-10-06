# Chapter 48 formations

The shared local website contains **48-1 through 48-80**, grouped into
**24 exact formations** from 24 messages in the supplied Discord reference
thread. Each card shows the cleared stage/range, observed Tatari level and
5×5 formation. Clicking the stage opens its source Discord message.

Open `../stage-47/site/index.html` directly, or visit the running preview at
`http://127.0.0.1:8765/#chapter-48`.

## Evidence and levels

All 80 stages were present in the reference thread, so the fallback Discord
search with the stage name and `has:image` was not needed. These are observed
source levels; a server-wide lowest-level clear has not been established.
48-1 through 48-10 show Tatari level 996, and 48-11 through 48-80 show level
997. Levels were read from multiple deployed inventory cards; each individual
deployed Tatari's level was not separately readable.

The captions assign the cleared stages. Each screenshot displays the following
stage, including 49-1 after clearing 48-80. All 24 captures are post-clear
references, with no recreated screenshots in this chapter. The clear outcome
is reported by the author and has not been independently tested in game.

Exact unit forms and positions were visually reviewed against the supplied
horde planner catalog. Serrabloom and Voltmare glitter variants use their
matching glitter artwork. Every board contains 15 deployed Tatari; the enemy
portraits and undeployed inventory are excluded. Rows run from front to rear,
with columns left to right.

## Files

- `stage-48-lineups.json`: 80 stage entries, 24 source submissions in
  `high_confidence`, and an empty `needs_human_review` array. Includes source
  message IDs, permalinks, timestamps, captions, image references, unit tiers,
  variants, grid coordinates and levels.
- `reviewed-formations.json`: manually reviewed boards and screenshot metadata.
- `evidence/raw-browser-sources.json`: browser observations for all 24 messages.
- `evidence/images/`: saved original attachments, retained outside the web root.
- `evidence/`: visual review sheets and the finished website screenshot.
- `../lineups.json`: the combined chapter 44–50 dataset.

The observed posting display name is `nil`; an account username was not
verified. Credited names come from captions. Confidence values are manual
review scores, not calibrated probabilities. Saved originals remain traceable
by message ID when attachment URLs expire. Only existing account access via
the Discord website was used; collection did not modify Discord content.

## Rebuild and preview

```sh
python3 /Users/kaichinh/ClashCrittersCollection/stage-47/build_site.py
python3 -m http.server 8765 --bind 127.0.0.1 --directory /Users/kaichinh/ClashCrittersCollection/stage-47/site
```

The build includes chapters 44–50 and embeds all sprite artwork in the offline
HTML page. Browser verification confirmed 24 chapter 48 cards, all 80 stage
labels, level badges and successfully loaded images, within the combined
162-card website. There were no console warnings/errors or horizontal overflow.
