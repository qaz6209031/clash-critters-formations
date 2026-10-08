"""Build a local, offline page from manually reviewed Discord formations."""

from __future__ import annotations

import base64
import hashlib
import html
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CATALOG_ROOT = ROOT.parent / "2026-10-05"
CATALOG = json.loads((CATALOG_ROOT / "tatari-reference.json").read_text())
FORMS = {form["form_id"]: form for form in CATALOG["forms"]}
CHAPTERS = [
    *[{"chapter": number, "directory": ROOT.parent / f"stage-{number}", "first": 1, "last": 80,
       "source_files": ["raw-browser-sources.json"]} for number in range(20, 31)],
    {"chapter": 31, "directory": ROOT.parent / "stage-31", "first": 1, "last": 80,
     "source_files": ["raw-browser-sources.json"]},
    *[{"chapter": number, "directory": ROOT.parent / f"stage-{number}", "first": 1, "last": 80,
       "source_files": (["raw-browser-sources.json", "antzer-browser-sources.json"]
                        if number == 32 else ["raw-browser-sources.json"])}
      for number in range(32, 40)],
    {"chapter": 40, "directory": ROOT.parent / "stage-40", "first": 1, "last": 80,
     "source_files": ["raw-browser-sources.json"]},
    {"chapter": 41, "directory": ROOT.parent / "stage-41", "first": 1, "last": 80,
     "source_files": ["raw-browser-sources.json"]},
    {"chapter": 42, "directory": ROOT.parent / "stage-42", "first": 1, "last": 80,
     "source_files": ["raw-browser-sources.json", "raw-browser-sources-gap-15-19.json"]},
    {"chapter": 43, "directory": ROOT.parent / "stage-43", "first": 1, "last": 80,
     "source_files": ["raw-browser-sources.json"]},
    {"chapter": 44, "directory": ROOT.parent / "stage-44", "first": 1, "last": 80,
     "source_files": ["raw-browser-sources.json"]},
    {"chapter": 45, "directory": ROOT.parent / "stage-45", "first": 1, "last": 80,
     "source_files": ["raw-browser-sources.json"]},
    {"chapter": 46, "directory": ROOT.parent / "stage-46", "first": 1, "last": 80,
     "source_files": ["raw-browser-sources.json"]},
    {"chapter": 47, "directory": ROOT, "first": 1, "last": 80,
     "source_files": ["raw-browser-sources-1-9.json", "raw-browser-sources.json", "raw-browser-sources-31-80.json"]},
    {"chapter": 48, "directory": ROOT.parent / "stage-48", "first": 1, "last": 80,
     "source_files": ["raw-browser-sources.json"]},
    {"chapter": 49, "directory": ROOT.parent / "stage-49", "first": 1, "last": 80,
     "source_files": ["raw-browser-sources.json"]},
    {"chapter": 50, "directory": ROOT.parent / "stage-50", "first": 1, "last": 80,
     "source_files": ["raw-browser-sources.json"]},
    *[{"chapter": number, "directory": ROOT.parent / f"stage-{number}", "first": 1, "last": 80,
       "source_files": ["raw-browser-sources.json"]} for number in range(51, 60)],
]
PUBLIC_SOURCE_INDEX = ROOT.parent / "data" / "source-index.json"
SOURCES = ({source["id"]: source for source in json.loads(PUBLIC_SOURCE_INDEX.read_text())}
           if PUBLIC_SOURCE_INDEX.exists() else {})
REVIEWED = []
for chapter in CHAPTERS:
    for filename in chapter["source_files"]:
        path = chapter["directory"] / "evidence" / filename
        if path.exists():
            for source in json.loads(path.read_text()):
                SOURCES[source["id"]] = source
    REVIEWED.extend({**formation, "chapter": chapter["chapter"]}
                    for formation in json.loads((chapter["directory"] / "reviewed-formations.json").read_text()))

# Reviewed board rows run front to rear, with columns left to right.
# None marks an empty cell; evidence and levels are stored beside each board.


def unit_record(key: str, row: int, column: int) -> dict:
    form_id, _, variant = key.partition(":")
    form = FORMS[form_id]
    return {
        "form_id": form_id,
        "name": form["name"],
        "family_id": form["family_id"],
        "tier": form["tier"],
        "variant": variant or "standard",
        "row": row,
        "column": column,
        "position": (row - 1) * 5 + column,
        "confidence": 0.98,
        "needs_review": False,
    }


def sprite_data(key: str) -> str:
    form_id, _, variant = key.partition(":")
    path = (CATALOG_ROOT / "reference-sprites" / "glitter" / f"{form_id}.png" if variant else
            CATALOG_ROOT / "reference-sprites" / f"{form_id}.png")
    return "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode()


def stage_label(numbers: list[int], chapter: int) -> str:
    """Collapse consecutive stages, while preserving gaps between ranges."""
    numbers = sorted(set(numbers))
    ranges = []
    start = previous = numbers[0]
    for number in numbers[1:] + [None]:
        if number is not None and number == previous + 1:
            previous = number
            continue
        ranges.append(f"{chapter}-{start}" if start == previous else f"{chapter}-{start} – {chapter}-{previous}")
        start = previous = number
    return ", ".join(ranges)


def stage_block(number: int) -> int:
    """Keep 1–4, 5–9 and each boss separate in the new chapters."""
    decade, offset = divmod(number, 10)
    return number if offset == 0 else decade * 10 + (1 if offset <= 4 else 5)


def build() -> None:
    formations = []
    stages = []
    cards = []
    sprites = {}
    groups = {}
    for reviewed in REVIEWED:
        source = SOURCES[reviewed["source_message_id"]]
        board_source = SOURCES[reviewed.get("board_source_message_id", source["id"])]
        chapter = reviewed["chapter"]
        start, end = reviewed["stage_start"], reviewed["stage_end"]
        displayed = reviewed["screenshot_displayed_stage"]
        credit, board = reviewed["credited_player_name"], reviewed["board"]
        level = reviewed["tatari_level"]
        level_source = reviewed.get("tatari_level_source", "image")
        assert isinstance(level, int) and not isinstance(level, bool) and level > 0, source["id"]
        assert level_source in {"image", "message_text"}, source["id"]
        if level_source == "message_text":
            quote = reviewed["tatari_level_quote"]
            assert quote in source["text"] and str(level) in quote, source["id"]
        recreated = reviewed["capture_type"] == "reconstructed"
        needs_review = recreated or reviewed.get("needs_review", False)
        range_check = bool(reviewed.get("caption_stage_range"))
        assert len(board) == 5 and all(len(row) == 5 for row in board)
        lineup = [unit_record(key, r, c)
                  for r, row in enumerate(board, 1)
                  for c, key in enumerate(row, 1) if key]
        if "unit_confidence" in reviewed:
            for unit in lineup:
                unit["confidence"] = reviewed["unit_confidence"]
                unit["tier_assignment_basis"] = reviewed["tier_assignment_basis"]
        assert len(lineup) == reviewed.get("deployed_count", 15), source["id"]
        signature = json.dumps([(u["position"], u["form_id"], u["variant"])
                                for u in lineup], separators=(",", ":"))
        formations.append({
            "formation_id": source["id"],
            "chapter": chapter,
            "extraction_revision": reviewed.get("extraction_revision", 2 if chapter == 47 and any("serrabloom:glitter" in row for row in board) else 1),
            "source_message_id": source["id"],
            "source_message_url": source["source_message_url"],
            "permalink_method": source["permalink_method"],
            "source_server": "Clash of Critters",
            "source_server_id": "1343763804349267989",
            "source_thread_id": source.get("channel_id") or source["source_message_url"].split("/")[-2],
            "source_thread": source.get("source_thread", "Beating Zobos In Public (F2P Journey). Chapter: 41 42 43 44 45 46 47 48 49 50"),
            "source_type": "mixed",
            "discord_display_name": source["display_name"],
            "discord_username": source.get("discord_username"),
            "credited_player_name": credit,
            "credit_basis": reviewed.get("credit_basis", "Name in the message caption; not a verified Discord username."),
            "posted_at": source["posted_at"],
            "message_text": source["text"],
            "reply_context_text": source.get("reply_context"),
            "image_urls": [attachment["url"] for attachment in board_source["attachments"]],
            "local_image_path": board_source["local_image_path"],
            "screenshot_displayed_stage": displayed,
            "screenshot_enemy_level": reviewed["screenshot_enemy_level"],
            "screenshot_capture_type": reviewed["capture_type"],
            "tatari_level": level,
            "tatari_level_source": level_source,
            "tatari_level_quote": reviewed.get("tatari_level_quote"),
            "tatari_level_basis": reviewed.get("tatari_level_basis", "Visible level text on multiple deployed inventory cards. This is the observed player level in the screenshot; individual levels were not readable for every deployed unit."),
            "level_from_original_post_clear_screenshot": reviewed.get("level_from_original_post_clear_screenshot", not recreated),
            "cleared_stages": [f"{chapter}-{n}" for n in range(start, end + 1)],
            "caption_stage_range": reviewed.get("caption_stage_range"),
            "stage_assignment": reviewed.get("stage_assignment_basis") or ("Author's caption; reconstructed later because the original screenshot was missed." if recreated else "Author's caption; screenshot shows the next stage after the reported clear/range, including the next chapter's stage 1 after stage 80."),
            "grid": {"rows": 5, "columns": 5, "orientation": "Rows front to rear (top to bottom); columns left to right."},
            "lineup": lineup,
            "formation_hash": hashlib.sha256(signature.encode()).hexdigest(),
            "supersedes_message_id": None,
            "selected_for_website": reviewed.get("selected_for_website", True),
            "selection_reason": reviewed.get("selection_reason"),
            "needs_review": needs_review,
            "review_notes": reviewed["notes"] or "Exact forms and occupied cells visually matched to the supplied planner catalog. Glitter variants matched separately where present.",
            "outcome_basis": "Author-reported clear; not independently tested in game.",
        })
        if "deployed_count" in reviewed:
            formations[-1]["deployed_count"] = reviewed["deployed_count"]
        if "board_source_message_id" in reviewed:
            formations[-1]["board_source_message_id"] = board_source["id"]
            formations[-1]["board_source_message_url"] = board_source["source_message_url"]
        if "tier_assignment_basis" in reviewed:
            formations[-1]["tier_assignment_basis"] = reviewed["tier_assignment_basis"]
        if "supporting_message_ids" in reviewed:
            formations[-1]["supporting_messages"] = [
                {key: SOURCES[message_id][key]
                 for key in ("id", "source_message_url", "text", "posted_at")}
                for message_id in reviewed["supporting_message_ids"]]
        if not formations[-1]["selected_for_website"]:
            continue
        for n in range(start, end + 1):
            stage = f"{chapter}-{n}"
            stages.append({"stage": stage, "formation_id": source["id"], "tatari_level": level, "level_from_reconstruction": recreated})
        blocks = {}
        for number in range(start, end + 1):
            block = stage_block(number) if chapter <= 30 or 32 <= chapter <= 39 or chapter >= 51 else None
            blocks.setdefault(block, []).append(number)
        level_observation = (" in a recreated screenshot; original clear level unverified" if recreated else
                             "; " + reviewed["tatari_level_basis"] if "tatari_level_basis" in reviewed else
                             " in the post-clear screenshot")
        for block, numbers in blocks.items():
            group = groups.setdefault((chapter, block, formations[-1]["formation_hash"]), {
                "chapter": chapter,
                "board": board, "numbers": [], "source": source, "levels": set(),
                "posters": {}, "level_notes": [],
            })
            group["numbers"].extend(numbers)
            group["levels"].add(level)
            group["posters"].setdefault(source["display_name"], source["source_message_url"])
            group["level_notes"].append(f"{stage_label(numbers, chapter)}: Tatari Lv.{level}" + level_observation)
            if needs_review or range_check:
                group["level_notes"].append(reviewed["notes"])

    for chapter in [30, *range(32, 40), *range(51, 60)]:
        chapter_groups = [group for group in groups.values() if group["chapter"] == chapter]
        expected_blocks = [numbers for decade in range(0, 80, 10)
                           for numbers in (list(range(decade + 1, decade + 5)),
                                           list(range(decade + 5, decade + 10)), [decade + 10])]
        assert [sorted(set(group["numbers"])) for group in chapter_groups] == expected_blocks, chapter

    previous_chapter = None
    for group in groups.values():
        chapter = group["chapter"]
        if chapter != previous_chapter:
            cards.append(f'<h2 class="chapter-title" id="chapter-{chapter}">Chapter {chapter}</h2>')
            previous_chapter = chapter
        stage = stage_label(group["numbers"], chapter)
        source = group["source"]
        cells = []
        for r, row in enumerate(group["board"], 1):
            for c, key in enumerate(row, 1):
                if key:
                    unit = unit_record(key, r, c)
                    label = f'{unit["name"]} · T{unit["tier"]}'
                    if unit["variant"] == "glitter":
                        label += " · Glitter"
                    label += f" · row {r}, column {c}"
                    sprite_id = key.replace(":", "-")
                    sprites.setdefault(sprite_id, sprite_data(key))
                    cells.append(f'<div class="cell occupied" title="{html.escape(label)}"><img data-sprite="{sprite_id}" alt="{html.escape(label)}" width="200" height="200" draggable="false"></div>')
                else:
                    cells.append(f'<div class="cell" aria-label="Empty · row {r}, column {c}"></div>')
        stage_numbers = ",".join(f"{chapter}-{n}" for n in sorted(set(group["numbers"])))
        level_text = "Lv." + "/".join(str(level) for level in sorted(group["levels"]))
        level_title = html.escape("; ".join(group["level_notes"]))
        poster_links = ", ".join(f'<a href="{html.escape(url, quote=True)}" target="_blank" rel="noopener noreferrer">{html.escape(name)}</a>' for name, url in group["posters"].items())
        cards.append(f'<article class="stage" data-chapter="{chapter}" data-stages="{stage_numbers}" data-formation-id="{source["id"]}"><h2><a href="{source["source_message_url"]}" target="_blank" rel="noopener noreferrer" title="Open the original Discord reference">{stage}</a><span class="level" title="{level_title}" aria-label="{level_title}">{level_text}</span></h2><p class="poster">Posted by {poster_links}</p><div class="board" role="group" aria-label="Stages {stage}: 5 by 5 formation, top row is the front">{"".join(cells)}</div></article>')

    assert [s["stage"] for s in stages] == [f"{c['chapter']}-{n}" for c in CHAPTERS for n in range(c["first"], c["last"] + 1)]
    dataset = {
        "schema_version": "1.6",
        "collected_at": "2026-10-08",
        "collection_method": "Authenticated Discord website, read-only browser inspection and attachment downloads.",
        "catalog_reference": {
            "url": CATALOG["source_url"],
            "version": CATALOG["source_version"],
            "data_date": CATALOG["source_data_date"],
            "catalog_sha256": CATALOG["catalog_sha256"],
        },
        "stage_ranges": [{key: c[key] for key in ("chapter", "first", "last")} for c in CHAPTERS],
        "stages": stages,
        "high_confidence": [formation for formation in formations if not formation["needs_review"]],
        "needs_human_review": [formation for formation in formations if formation["needs_review"]],
        "deduplication": "Source message ID identifies each submission. Stage entries reference their source formation; shared captions are not counted as extra submissions. Cards group exact forms, variants and positions by formation hash. Chapters 20–30, 32–39 and 51–59 keep each 1–4 block, 5–9 block and multiple-of-10 boss separate. Early guide boundaries at stage 6 additionally split a 5–9 block when its formations differ. Existing chapter grouping is preserved. New messages are preserved separately; supersedes_message_id remains null without explicit evidence of replacement.",
        "level_selection_policy": "Use a formation only when its Tatari level is readable in the image or explicitly stated in the source message. A stated level is valid without image-level text; preserve whether its source is image or message_text. Do not infer an absent level from adjacent posts or enemy levels. Prefer the lowest supported level among inspected clear candidates, preserving unselected alternatives. For chapters 20–30, 32–39 and 51–59, the user waived exhaustive minimum-level comparison; choose a supported clear covering each required block.",
        "selection_scope": "Chapters 41–50 use the supplied reference thread, except 42-15 through 42-19 found through Discord stage-name searches with has:image. Chapters 31 and 40 use Casey's Chapter 19 and onwards thread; chapter 31 uses Win's explicitly stated level 549 formation for 31-5 through 31-9. Other chapter 31 selections use Casey after comparisons with Harsh, Win, Unown, Antzer and opening-stage candidates. Casey's explicitly stated 596 for 31-10 through 31-12 is accepted as a message-text level; the record remains flagged only because the screenshot displays 31-15. Three higher-level Casey alternatives for 31-5 through 31-9 are retained with selected_for_website=false. Chapters 32–39 primarily use Antzer’s guide, with Harsh’s chapter 32 opening blocks and chapter 33 gap, Unown’s missing or ambiguous-tier blocks, and Casey’s explicitly stated level 771 for 39-1 through 39-4. Complete caption-supported blocks are kept together and each boss is separate. Chapters 20–29 and 51–59 primarily use Pika’s guides, with Vanhhh filling 22-16–22-19 and 23-6–23-9, Vrondius (crediting Layios) filling 28-75–28-79, and Saber filling 58-11–58-14 and 59-1–59-4. All new levels are stated in their own source captions. Early guide formations change at stage 6 rather than stage 5; those verified changes are preserved. The recalled 26-56–26-59 range remains flagged for human review. No server-wide minimum has been established. Chapter 30 uses Antzer’s explicit stage-block captions, Casey’s level-573 boss 30-10 post (crediting jacobdumbnut), and Vrondius’s level-619 30-25–30-29 post (crediting Layios). Vrondius deploys 14/15 units and the screenshot shows the range beginning; its full coverage relies on the caption. Levels are source observations or author statements, not independently tested requirements.",
    }
    for record in dataset["high_confidence"] + dataset["needs_human_review"]:
        record["local_image"] = (os.path.relpath(record["local_image_path"], ROOT.parent)
                                 if record["local_image_path"] else None)
    (ROOT.parent / "lineups.json").write_text(json.dumps(dataset, ensure_ascii=False, indent=2) + "\n")
    for chapter in CHAPTERS:
        number = chapter["chapter"]
        chapter_dataset = {**dataset,
            "stage_range": {key: chapter[key] for key in ("chapter", "first", "last")},
            "stage_ranges": [{key: chapter[key] for key in ("chapter", "first", "last")}],
            "stages": [stage for stage in stages if stage["stage"].startswith(f"{number}-")],
            "high_confidence": [{**record, "local_image": os.path.relpath(record["local_image_path"], chapter["directory"]) if record["local_image_path"] else None} for record in formations if record["chapter"] == number and not record["needs_review"]],
            "needs_human_review": [{**record, "local_image": os.path.relpath(record["local_image_path"], chapter["directory"]) if record["local_image_path"] else None} for record in formations if record["chapter"] == number and record["needs_review"]],
        }
        (chapter["directory"] / f"stage-{number}-lineups.json").write_text(json.dumps(chapter_dataset, ensure_ascii=False, indent=2) + "\n")
    template = (ROOT / "page-template.html").read_text()
    options = "".join(f'<option value="{chapter["chapter"]}">Chapter {chapter["chapter"]}</option>' for chapter in CHAPTERS)
    page = template.replace("<!-- STAGE_CARDS -->", "\n".join(cards)).replace("<!-- CHAPTER_OPTIONS -->", options).replace("/* SPRITE_DATA */ {}", json.dumps(sprites, separators=(",", ":")))
    site = ROOT / "site"
    site.mkdir(exist_ok=True)
    (site / "index.html").write_text(page)
    print(f"Built {len(stages)} stages in {len(groups)} grouped formation cards; {len(sprites)} exact sprite variants. Offline page: {site / 'index.html'}")


if __name__ == "__main__":
    build()
