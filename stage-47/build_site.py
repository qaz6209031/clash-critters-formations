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


def build() -> None:
    formations = []
    stages = []
    cards = []
    sprites = {}
    groups = {}
    for reviewed in REVIEWED:
        source = SOURCES[reviewed["source_message_id"]]
        chapter = reviewed["chapter"]
        start, end = reviewed["stage_start"], reviewed["stage_end"]
        displayed = reviewed["screenshot_displayed_stage"]
        credit, board = reviewed["credited_player_name"], reviewed["board"]
        level = reviewed["tatari_level"]
        recreated = reviewed["capture_type"] == "reconstructed"
        needs_review = recreated or reviewed.get("needs_review", False)
        range_check = bool(reviewed.get("caption_stage_range"))
        assert len(board) == 5 and all(len(row) == 5 for row in board)
        lineup = [unit_record(key, r, c)
                  for r, row in enumerate(board, 1)
                  for c, key in enumerate(row, 1) if key]
        assert len(lineup) == 15, source["id"]
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
            "source_thread_id": "1545053459869339698",
            "source_thread": "Beating Zobos In Public (F2P Journey). Chapter: 41 42 43 44 45 46 47 48 49 50",
            "source_type": "mixed",
            "discord_display_name": source["display_name"],
            "discord_username": None,
            "credited_player_name": credit,
            "credit_basis": "Name in the message caption; not a verified Discord username.",
            "posted_at": source["posted_at"],
            "message_text": source["text"],
            "reply_context_text": source.get("reply_context"),
            "image_urls": [attachment["url"] for attachment in source["attachments"]],
            "local_image_path": source["local_image_path"],
            "screenshot_displayed_stage": displayed,
            "screenshot_enemy_level": reviewed["screenshot_enemy_level"],
            "screenshot_capture_type": reviewed["capture_type"],
            "tatari_level": level,
            "tatari_level_basis": "Visible level text on multiple deployed inventory cards. This is the observed player level in the screenshot; individual levels were not readable for every deployed unit.",
            "level_from_original_post_clear_screenshot": not recreated,
            "cleared_stages": [f"{chapter}-{n}" for n in range(start, end + 1)],
            "caption_stage_range": reviewed.get("caption_stage_range"),
            "stage_assignment": reviewed.get("stage_assignment_basis") or ("Author's caption; reconstructed later because the original screenshot was missed." if recreated else "Author's caption; screenshot shows the next stage after the reported clear/range, including the next chapter's stage 1 after stage 80."),
            "grid": {"rows": 5, "columns": 5, "orientation": "Rows front to rear (top to bottom); columns left to right."},
            "lineup": lineup,
            "formation_hash": hashlib.sha256(signature.encode()).hexdigest(),
            "supersedes_message_id": None,
            "needs_review": needs_review,
            "review_notes": reviewed["notes"] or "Exact forms and occupied cells visually matched to the supplied planner catalog. Glitter variants matched separately where present.",
            "outcome_basis": "Author-reported clear; not independently tested in game.",
        })
        for n in range(start, end + 1):
            stage = f"{chapter}-{n}"
            stages.append({"stage": stage, "formation_id": source["id"], "tatari_level": level, "level_from_reconstruction": recreated})
        group = groups.setdefault((chapter, formations[-1]["formation_hash"]), {
            "chapter": chapter,
            "board": board, "numbers": [], "source": source, "levels": set(),
            "recreated": False, "range_check": False, "level_notes": [],
        })
        group["numbers"].extend(range(start, end + 1))
        group["levels"].add(level)
        group["recreated"] |= recreated
        group["range_check"] |= range_check
        group["level_notes"].append(f"{stage_label(list(range(start, end + 1)), chapter)}: Tatari Lv.{level}" + (" in a recreated screenshot; original clear level unverified" if recreated else " in the post-clear screenshot"))
        if range_check:
            group["level_notes"].append(reviewed["notes"])

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
        recreated_note = '<small>recreated</small>' if group["recreated"] else ('<small>check range</small>' if group["range_check"] else "")
        cards.append(f'<article class="stage" data-chapter="{chapter}" data-stages="{stage_numbers}" data-formation-id="{source["id"]}"><h2><a href="{source["source_message_url"]}" target="_blank" rel="noopener noreferrer" title="Open the original Discord reference">{stage}</a><span class="level" title="{level_title}" aria-label="{level_title}">{level_text}{recreated_note}</span></h2><div class="board" role="group" aria-label="Stages {stage}: 5 by 5 formation, top row is the front">{"".join(cells)}</div></article>')

    assert [s["stage"] for s in stages] == [f"{c['chapter']}-{n}" for c in CHAPTERS for n in range(c["first"], c["last"] + 1)]
    dataset = {
        "schema_version": "1.3",
        "collected_at": "2026-10-05",
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
        "deduplication": "Source message ID identifies each submission. Stage entries reference their source formation; shared captions are not counted as extra submissions. Cards group exact forms, variants and positions by formation hash. New messages are preserved separately; supersedes_message_id remains null without explicit evidence of replacement.",
        "selection_scope": "All requested stages were present in the user-provided reference thread. Levels are observed in those source screenshots; no server-wide minimum level has been established. Missing stages should be searched with the stage name and has:image, then compared among author-reported clears with readable player levels.",
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
    page = template.replace("<!-- STAGE_CARDS -->", "\n".join(cards)).replace("/* SPRITE_DATA */ {}", json.dumps(sprites, separators=(",", ":")))
    site = ROOT / "site"
    site.mkdir(exist_ok=True)
    (site / "index.html").write_text(page)
    print(f"Built {len(stages)} stages in {len(groups)} grouped formation cards; {len(sprites)} exact sprite variants. Offline page: {site / 'index.html'}")


if __name__ == "__main__":
    build()
