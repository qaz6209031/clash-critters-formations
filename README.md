# Clash of Critters formations

[Live website](https://critterformations.com/) ·
[GitHub repository](https://github.com/qaz6209031/clash-critters-formations)

A simple Main Stage reference showing stage ranges, observed Tatari levels,
posters and exact 5×5 formations. It covers **3200 stages in chapters 20–59**,
grouped into **1039 formation cards** from 964 selected source posts.
All 967 reviewed submissions are preserved; the public index contains 969
source and supporting posts.

Choose a chapter at the top to show only its formations. The selector stays
available while scrolling, supports chapter links such as `#chapter-40`, and
works on phones. Artwork loads only for the selected chapter. Level badges
show the level numbers, with the posting display name immediately below.
Stage labels and posters link to their original Discord messages, which require
the viewer's own server access. A credited creator is distinct from the poster.

Exact forms, glitter variants and positions determine whether cards can merge.
Chapters 20–30, 32–39 and 51–59 keep 1–4, 5–9 and each boss separate.
The early Pika guide changes at stage 6: where its formations differ, stage 5
and stages 6–9 remain separate instead of asserting that one lineup clears the
entire 5–9 block. Existing chapter 31 and 40–50 formations are unchanged.
Ambiguous evidence retains review notes in the saved data and level tooltips.

## Preview and build

Python 3 is the only build requirement; no packages need to be installed.

```sh
python3 stage-47/build_site.py
python3 -m http.server 8765 --bind 127.0.0.1 --directory stage-47/site
```

Open `http://127.0.0.1:8765/`. Choose a chapter or use a link such as
`#chapter-20`, `#chapter-40` or `#chapter-59`. The finished `stage-47/site/index.html` also opens offline.
All artwork is embedded, so GitHub Pages project paths work without a base-URL
setting or asset server.

## GitHub Pages

The `Deploy GitHub Pages` workflow rebuilds and publishes `stage-47/site`
on every push to `main`, and can also run manually. In the repository's
**Settings → Pages**, the publishing source is **GitHub Actions**.
The workflow follows the [GitHub Pages deployment documentation](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages).

To update formations, edit the appropriate chapter's `reviewed-formations.json`
and add source metadata to `data/source-index.json`, then build, commit and push.
The builder validates complete stage coverage and each reviewed deployed count
(15 by default; source screenshots sometimes deploy fewer units).
Expanding to another chapter also requires adding it to `CHAPTERS` in the builder.
The chapter selector is populated automatically.

## Files and source evidence

- `stage-20` through `stage-59`: reviewed formations and chapter notes.
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

Chapter 31 adds all 80 stages from 36 selected posts, grouped into 35 cards.
Selected levels are 549–604. Win’s explicitly posted level 549 is selected
for 31-5–31-9; Casey’s three level-579 alternatives remain in the data.
Casey’s explicitly posted level 596 is accepted for 31-10–31-12, while that
source remains flagged for its screenshot-stage mismatch.

Chapters 32–39 add all 640 stages from 186 selected submissions in 192 cards.
The user waived exhaustive lowest-level comparison for this addition. Antzer
is the main source, with Harsh, Unown and Casey filling missing or ambiguous
blocks. Harsh’s explicit reply supports 32-11–32-14. When screenshots show base
artwork, exact tiers come from explicit author statements and retain that
provenance; unclear exceptions use other sources. Existing formations and card
grouping for chapter 31 and chapters 40–50 are preserved.

Chapters 20–29 and 51–59 add 1520 stages from 453 reviewed posts. Pika’s
chapter guides are the main sources; Vanhhh, Vrondius and Saber fill gaps.
All newly selected levels are explicitly stated in their own source posts;
exhaustive lowest-level comparison was waived. Vrondius credits Layios for
28-75–28-79. The author’s correction for 51-10 points to the 51-11–51-15
formation, so that supporting message is retained as the board source.
The recalled formation for **26-56–26-59 needs human review**: its author
missed the original screenshot and says the replacement is from memory.

Chapter 30 adds all 80 stages from 22 source posts in 24 cards, keeping
1–4, 5–9 and each boss separate. Antzer provides 20 stage-block references;
Casey supplies boss 30-10 at level 573, crediting jacobdumbnut, and Vrondius
supplies 30-25–30-29 at level 619, crediting Layios. All selected levels are
explicitly stated in their own messages. Vrondius's screenshot deploys 14/15
Tatari and shows the range beginning; the caption supports the full range.
No fifteenth unit or missing level is inferred. Existing chapter formations
and grouping are unchanged.
