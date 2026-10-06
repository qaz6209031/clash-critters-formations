# Chapter 43 formations

All **43-1 through 43-80** are covered by **22 grouped formations** from
24 source posts. Each card shows its stage range, observed Tatari level,
exact 5×5 grid and a link to the Discord source.

[Live chapter](https://kaichin.dev/clash-critters-formations/#chapter-43)

## Evidence and levels

- 43-1–43-20: Tatari level 941.
- 43-21–43-40: Tatari level 942.
- 43-41–43-80: Tatari level 945.

All sources are posted by `nil` in the supplied Beating Zobos In Public
reference thread. Caption credits name Izzy, except 43-65–43-69 which names
Bruno. Screenshots show the next stage after the captioned clear/range,
including 44-1 after 43-80. Identical boards for 43-10/43-11–43-14 and
43-30/43-31–43-34 merge, preserving all source records.

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
served root and ignored by Git. The generated local `stage-43-lineups.json`
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
