# Clash of Critters formations

[Live website](https://critterformations.com/) ·
[GitHub repository](https://github.com/qaz6209031/clash-critters-formations)

A simple Main Stage reference showing stage ranges, observed Tatari levels,
posters and exact 5×5 formations. The published site covers **5170 stages**
(chapters 10–79), grouped into **1816 formation cards** from **1623 selected
Discord source posts** (1630 chapter-specific records). All **1889 reviewed
formation records** are preserved; the public index contains 1886 source and
supporting posts. Unsupported stages remain empty.

Only original posts **after August 27, 2026** qualify for publication, using
America/Los_Angeles time: August 28 at midnight is `2026-08-28T07:00:00Z`.
The same cutoff applies to separate board sources and supporting evidence.
Edit dates do not qualify an older post. Missing, invalid or timezone-free
timestamps are excluded. The build enforces this policy on every update.

The date audit excludes **258 older submissions**. On October 8, newer visually
reviewed references restored all **861 previously hidden stages**. Most use
Vrondius’s September guide; individual gaps use Vanhhh, jacobdumbnut and
ZERO_SUGAR. **27-80 now uses jacobdumbnut’s September 8 level-525 post.**
Casey’s September level-579 posts replace the older 31-5–31-9 reference.
All chapters 20–59 now have complete coverage. Earlier submissions remain
archived with `selected_for_website: false` and their exclusion reason.

The page opens on **chapter 31** unless its URL names a valid chapter.
Choose a chapter at the top to show only its formations. The selector stays
available while scrolling, supports chapter links such as `#chapter-40`, and
works on phones. Artwork loads only for the selected chapter. Level badges
show the level numbers, with the posting display name immediately below.
Stage labels and posters link to their original Discord messages, which require
the viewer's own server access. A credited creator is distinct from the poster.

Exact forms, glitter variants and positions determine whether cards can merge.
Chapters 10–30, 32–39 and 51–79 keep 1–4, 5–9 and each boss separate.
A block may contain different cards when the source only supports shorter ranges.
The early Pika guide changes at stage 6: where its formations differ, stage 5
and stages 6–9 remain separate instead of asserting that one lineup clears the
entire 5–9 block. Existing grouping for chapter 31 and 40–50 is preserved.
Ambiguous evidence retains review notes in the saved data and level tooltips.

## Preview and build

Python 3 is the only build requirement; no packages need to be installed.

```sh
python3 stage-47/build_site.py
python3 -m http.server 8765 --bind 127.0.0.1 --directory stage-47/site
```

Open `http://127.0.0.1:8765/`. Choose a chapter or use a link such as
`#chapter-31`, `#chapter-40` or `#chapter-69`. The finished `stage-47/site/index.html` also opens offline.
All artwork is embedded, so GitHub Pages project paths work without a base-URL
setting or asset server.

## GitHub Pages

The `Deploy GitHub Pages` workflow rebuilds and publishes `stage-47/site`
on every push to `main`, and can also run manually. In the repository's
**Settings → Pages**, the publishing source is **GitHub Actions**.
The workflow follows the [GitHub Pages deployment documentation](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages).

To update formations, edit the appropriate chapter's `reviewed-formations.json`
and add source metadata to `data/source-index.json`, then build, commit and push.
The builder validates source timestamps, unique published stage mappings,
chapter bounds, supported grouping and each reviewed deployed count
(15 by default; source screenshots sometimes deploy fewer units). Gaps are
recorded in generated `unavailable_stages`; no missing formation is invented.
Expanding to another chapter also requires adding it to `CHAPTERS` in the builder.
The chapter selector is populated automatically.

## Files and source evidence

- `stage-10` through `stage-79`: reviewed formations and chapter notes.
- `stage-47/build_site.py`: static site and structured-data generator.
- `stage-47/page-template.html`: website layout and styles.
- `stage-47/site/index.html`: generated offline website.
- `data/source-index.json`: publication metadata containing captions,
  timestamps, posting display names and message permalinks. New entries retain
  the relevant stage/level caption excerpt. It excludes attachment
  URLs, reply-context captures or local evidence paths.
- `2026-10-05/tatari-reference.json` and `reference-sprites`: the cached
  catalog and artwork from the [user-supplied horde planner](https://jeremycanlas.github.io/clash-of-critters-horde-planner/).

Original Discord screenshots, raw browser captures, detailed generated lineup
datasets and older sample archives are ignored by Git and remain local.
When local evidence is available, the builder includes that richer evidence in
the locally generated JSON. A fresh clone builds from the publication index
and leaves original-image fields empty. Only the site folder is deployed.

Credits follow source captions and are not independently verified. Use a formation
only when its level is readable in the image or explicitly typed in the post.
Typed levels are valid even without image-level text; provenance is retained as
`tatari_level_source: image | message_text`, with an exact quote for typed levels.
Never infer a missing level from nearby posts or enemy levels. Levels are source
observations or author statements, not established minimum clear levels. Screenshots
normally display the next stage after the reported clear. Some chapter 40
captures follow the first stage of a captioned range; later endpoints rely on
the author’s caption. Recreated captures
and overlapping caption endpoints retain their review notes. Collection used
only the existing account's authorized Discord website access.

Chapters 40–43 add 320 stages from 99 source posts. Chapter 40 uses Casey’s
Chapter 19 and onwards thread. The missing 42-15–42-19 range uses pony’s
level-853 posts found through Discord search; all other new chapters use the
provided nil reference thread. Search comparisons establish only the lowest
readable level among inspected candidates, not a server-wide minimum.

Chapter 31 covers all 80 stages from 38 selected posts, grouped into 37 cards.
Selected levels are 579–604. Casey’s September level-579 posts are selected
for 31-5–31-9; Win’s older level-549 alternative remains archived.
Casey’s explicitly posted level 596 is accepted for 31-10–31-12, while that
source remains flagged for its screenshot-stage mismatch.

Chapters 32–39 add all 640 stages from 186 selected submissions in 192 cards.
The user waived exhaustive lowest-level comparison for this addition. Antzer
is the main source, with Harsh, Unown and Casey filling missing or ambiguous
blocks. Harsh’s explicit reply supports 32-11–32-14. When screenshots show base
artwork, exact tiers come from explicit author statements and retain that
provenance; unclear exceptions use other sources. Existing formations and card
grouping for chapter 31 and chapters 40–50 are preserved.

The historical collection for chapters 20–29 and 51–59 contains 1520 stages
from 453 reviewed posts; the publication cutoff now excludes the older entries. Pika’s
chapter guides are the main sources; Vanhhh, Vrondius and Saber fill gaps.
All newly selected levels are explicitly stated in their own source posts;
exhaustive lowest-level comparison was waived. Vrondius credits Layios for
28-75–28-79. The author’s correction for 51-10 points to the 51-11–51-15
formation, so that supporting message is retained as the board source.
The older recalled formation for 26-56–26-59 remains archived and excluded;
a visually reviewed September Vrondius reference now covers those stages.

Chapter 30 now publishes all 80 stages from 23 selected submissions, using
Vrondius’s September posts plus the retained Casey 30-10 and Vrondius
30-25–30-29 references. Supported observed/stated levels are 573–621.
Fewer-than-15 deployments preserve the empty cells. No missing unit is inferred.

Replacement captions may list nonconsecutive stages. `caption_stage_numbers`
preserves those exact claims, and `website_stage_numbers` stores the selected
subset. The builder never fills an unlisted stage from a range’s endpoints.
A later overlapping post takes priority only for the previously hidden stages;
earlier and alternative records remain archived. One source spanning two
chapters uses chapter-qualified formation IDs and retains one source message ID.

The 26-26 reference uses level **512**, visibly shown in Vanhhh’s screenshot;
the caption’s different level 509 is retained in the data. The 28-38 reference
includes Solaflora Glitter, visually matched to the planner’s exact sprite.

Chapters 60–69 add **800 of 800 stages** from **240 reviewed posts**, grouped
into **240 cards**. Pika supplies the main guide; Saber supplies 62-45–62-49
and 63-15–63-19, Gallivant supplies 65-25–65-29, and Tiva supplies 66-5–66-9. Supported Tatari levels
are 1310–1524. Each source was posted after the publication cutoff; levels
come from the same caption or screenshot. Tiva’s second attachment supplies
**66-5–66-9 at level 1449**, confirmed by both the caption and visible
inventory cards. An ambiguous alternative was not used.

Pika's regular captions often name the screenshot's next stage as the range
endpoint. Normalized clear coverage stops before that endpoint when it matches
the displayed stage. `caption_stage_numbers_original` retains the literal
caption claims separately from normalized `caption_stage_numbers` and the
selected `website_stage_numbers`. The 67-31–67-35 reference shows 67-36 and
therefore supports its inclusive endpoint; the following formation is selected
for the overlapping stage 35. All previous 3200 stage mappings are unchanged.


Chapters 10–19 add **754 of 800 requested stages** from **244 source posts**
(249 chapter-specific reviewed records), grouped into **373 cards**. Chiaki’s
September guide is the main source; Libertas and Anthi fill chapter 13–14
references. Jessimika_x’s September 24–29 guide fills the remaining 15 chapter 13
gaps at image-documented levels 279 and 292, preserving all previous selections. Every posting display name was checked against the rendered Discord
message heading. Supported Tatari levels range from **181 to 346**. All 4000
existing chapter 20–69 stage mappings, levels, formations and 1300 cards are unchanged.

| Chapter | Available stages | Unavailable stages |
| --- | ---: | --- |
| 10 | 76/80 | 76–79 |
| 11 | 77/80 | 57–59 |
| 12 | 57/80 | 8–9, 11–19, 36–39, 66–69, 76–79 |
| 13 | 80/80 | None |
| 14 | 77/80 | 31–32, 40 |
| 15 | 75/80 | 9, 16–19 |
| 16 | 77/80 | 33–35 |
| 17 | 80/80 | None |
| 18 | 76/80 | 76–79 |
| 19 | 79/80 | 1 |

Early captions sometimes name irregular stage groups or contain a typo. Their
literal numbers are preserved alongside the selected subset; unlisted stages
are never filled from a screenshot’s next-stage label. Chapter 13’s isolated
13-15 in a 13-21–13-24 caption is not treated as 13-25. Chapter 12’s conflicting
opening-stage caption is used only for its explicitly named boss 12-10, with
unambiguous posts supplying the opening stages.

Some screenshots retain base artwork after evolution. When the same post
explicitly states the tiers, catalog forms are normalized to those stated tiers
and `tier_assignment_basis` retains the evidence. No tier or level is borrowed
from a neighboring post. The removed posting-date sentence stays absent from
the page while the source and supporting-evidence cutoff remains enforced.


Chapters 70–79 add **416 of 800 requested stages** from **146 visually reviewed
posts**, grouped into **143 cards**. All 4739 existing stage mappings and
1667 cards are unchanged. Pika supplies chapters 70–73 and the opening 74
blocks. Mw’s eligible posts and Cutey, djinnlynx, oTradeMark, Krousty, Fuenite
and Melinoë supply the remaining chapter 74 references; Mw supplies 75-1–49.
Creator credits in the new captions are retained separately from posting authors.

| Chapter | Available stages | Unavailable stages |
| --- | ---: | --- |
| 70–73 | 80/80 each | None |
| 74 | 47/80 | 11–14, 19, 21–29, 31–39, 41–49, 64 |
| 75 | 49/80 | 50–80 |
| 76–79 | 0/80 each | 1–80 |

The 75-50–70 multi-image submission has no readable level in any attachment
or its caption. The 76-30 screenshot clips the final level digits and gives
no caption level. These sources are excluded. Search results for chapters
77–79 supplied no usable reference; reversed-number lower-chapter matches
were discarded. Older chapter 74 posts and ambiguous baby-artwork references
were not used. The chapter selector includes empty chapters with a simple
“No verified formations available” message. Default chapter 31 is preserved.

Two chapter 72 captions place their screenshots in an immediately following
message from the same poster. Both original timestamps are checked, and the
separate board-source permalinks are retained. Exact catalog forms, Glitter
variants, positions, caption endpoints, screenshot stages and levels remain
traceable. Fewer-than-15 deployments retain their empty cells.
