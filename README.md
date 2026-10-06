# Clash of Critters formations

[Live website](https://kaichin.dev/clash-critters-formations/) ·
[GitHub repository](https://github.com/qaz6209031/clash-critters-formations)

A simple, static Main Stage reference showing stage ranges, observed Tatari
levels and exact 5×5 formations. It currently covers all **880 stages in
chapters 40–50**, grouped into **253 formation cards** from 267 source posts.
Exact forms, glitter variants and positions determine whether cards can merge.
Stage labels link to the original Discord messages, which require the viewer's
own server access. Recreated screenshots and ambiguous stage ranges are labeled.

## Preview and build

Python 3 is the only build requirement; no packages need to be installed.

```sh
python3 stage-47/build_site.py
python3 -m http.server 8765 --bind 127.0.0.1 --directory stage-47/site
```

Open `http://127.0.0.1:8765/`. Chapter links use `#chapter-40` through
`#chapter-50`. The finished `stage-47/site/index.html` also opens offline.
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
(15 by default; the source for 42-5–42-9 explicitly has 14).
Expanding to another chapter also requires adding it to `CHAPTERS` in the builder
and updating the page title/description.

## Files and source evidence

- `stage-40` through `stage-50`: reviewed formations and chapter notes.
- `stage-47/build_site.py`: static site and structured-data generator.
- `stage-47/page-template.html`: website layout and styles.
- `stage-47/site/index.html`: generated offline website.
- `data/source-index.json`: publication metadata containing captions,
  timestamps, posting display names and message permalinks, without attachment
  URLs, reply-context captures or local evidence paths.
- `2026-10-05/tatari-reference.json` and `reference-sprites`: the cached
  catalog and artwork from the [user-supplied horde planner](https://jeremycanlas.github.io/clash-of-critters-horde-planner/).

Original Discord screenshots, raw browser captures, detailed generated lineup
datasets and older sample archives are ignored by Git and remain local.
When local evidence is available, the builder includes that richer evidence in
the locally generated JSON. A fresh clone builds from the publication index
and leaves original-image fields empty. Only the site folder is deployed.

Credits follow source captions and are not independently verified. Levels are
observed screenshot levels, not established minimum clear levels. Screenshots
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
