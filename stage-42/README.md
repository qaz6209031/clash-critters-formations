# Chapter 42 formations

All **42-1 through 42-80** are covered by **21 grouped formations** from
25 source posts. Each card shows its stage range, observed Tatari level,
exact 5×5 grid and a link to the Discord source.

[Live chapter](https://kaichin.dev/clash-critters-formations/#chapter-42)

## Evidence and levels

- 42-1–42-14 and 42-20–42-49: Tatari level 870.
- 42-15–42-19: Tatari level 853.
- 42-50–42-54: Tatari level 910.
- 42-55–42-80: Tatari level 939.

The supplied nil thread is missing screenshots for 42-15–42-19. A Discord
`42-15 has:image` search inspected 24 images from 16 relevant candidate posts.
Pony’s two posts in Lineups from 40-40 Onwards show level 853 and report
clearing 42-15–42-17 and 42-18–42-19. These were the lowest readable levels
among the inspected candidates; no server-wide minimum is claimed. They
credit adaptations of Kiria’s formation. Separate source thread IDs and
permalinks are retained.

The 42-5–42-9 screenshot explicitly shows 14/15 deployed Tatari. The exact
14 occupied cells are stored with deployed_count 14; no 15th unit is inferred.
Screenshots show the next stage after the captioned clear/range.
Unspecified creator credits remain null, including the tentative Esek YT
attribution for 42-50. Contextual “Same Formation” credits are labeled as
inferences. Serrabloom, Voltmare and Charflutter glitter variants are matched
separately where present.

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
served root and ignored by Git. The generated local `stage-42-lineups.json`
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
