# Chapter 40 formations

All **40-1 through 40-80** are covered by **26 grouped formations** from
26 source posts. Each card shows its stage range, observed Tatari level,
exact 5×5 grid and a link to the Discord source.

[Live chapter](https://kaichin.dev/clash-critters-formations/#chapter-40)

## Evidence and levels

- 40-1–40-20: Tatari level 806.
- 40-21–40-80: Tatari level 807.

Sources are posted by `Casey | 31150710` in the Chapter 19 and onwards thread.
Opening-stage searches inspected 29 images from 23 candidates across two
Discord search pages. Casey and Maze both showed level 806; lower or hidden
levels were not inferred from screenshots without player-level text. The
selection is the lowest readable observed level among inspected candidates,
not proof of a server-wide minimum.

Captions report the cleared ranges. For 40-10–40-12, 40-30–40-34,
40-40–40-44 and 40-50–40-54, the screenshot follows the first stage in the
range; later endpoints depend on the author’s statement. Other captures show
the next stage after the complete range, including 41-1 after 40-80.
Most original creators are unspecified. The known adapted Antzer reference
for 40-20 is retained separately from posting identity.

Levels are read from multiple deployed inventory cards. They are observations,
not established minimum requirements; individual levels were not separately
readable for every deployed Tatari. Clears are author-reported and were not
independently played. Rows run front to rear; columns run left to right.
Forms, tiers, variants and exact occupied cells were visually matched to the
supplied horde planner. Enemy portraits and undeployed inventory are excluded.
No new records in this chapter require visual unit review.

## Files and verification

`reviewed-formations.json` stores the reviewed boards. Sanitized publication
metadata is in `../data/source-index.json`; original attachment URLs, raw
browser captures and screenshots stay local under `evidence/`, outside the
served root and ignored by Git. The generated local `stage-40-lineups.json`
and `../lineups.json` retain timestamps, source IDs, captions, posting display
names, credited references, screenshot stages, grid coordinates and levels.
Usernames are unverified; confidence values are manual review scores.

The shared build covers 880 stages in chapters 40–50 using 253 cards.
Verification confirmed complete stage coverage, 267 unique source records,
unchanged preceding 168 records/560 stage mappings and all 3,794 images loaded
without console errors or horizontal overflow. The fresh publication build
uses the sanitized source index when private evidence is absent.

Rebuild with `python3 stage-47/build_site.py` from the project root.
Collection used only the authenticated Discord website and did not modify
Discord content.
