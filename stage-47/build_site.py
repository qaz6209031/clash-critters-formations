"""Build a local, offline page from manually reviewed Discord formations."""

from __future__ import annotations

import hashlib
import html
import json
import os
import re
import shutil
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
SITE_URL = "https://critterformations.com"
LANGS = ("en", "vi")
# After August 27 in the owner's America/Los_Angeles time zone (PDT).
PUBLICATION_CUTOFF = datetime(2026, 8, 28, 7, tzinfo=timezone.utc)
# The October 21 update changed enemy formations in these chapters.
# The owner requires references posted after October 21 in Los Angeles.
CHAPTER_PUBLICATION_CUTOFFS = {
    chapter: datetime(2026, 10, 22, 7, tzinfo=timezone.utc)
    for chapter in range(24, 29)
}
CATALOG_ROOT = ROOT.parent / "2026-10-05"
CATALOG = json.loads((CATALOG_ROOT / "tatari-reference.json").read_text())
FORMS = {form["form_id"]: form for form in CATALOG["forms"]}
CHAPTERS = [
    *[{"chapter": number, "directory": ROOT.parent / f"stage-{number}", "first": 1, "last": 80,
       "source_files": ["raw-browser-sources.json"]} for number in range(1, 20)],
    *[{"chapter": number, "directory": ROOT.parent / f"stage-{number}", "first": 1, "last": 80,
       "source_files": ["raw-browser-sources.json", "newer-browser-sources.json"]} for number in range(20, 31)],
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
       "source_files": ["raw-browser-sources.json"]} for number in range(51, 80)],
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
SOURCE_RECORD_COUNTS = Counter(record["source_message_id"] for record in REVIEWED)

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


def sprite_path(key: str) -> Path:
    form_id, _, variant = key.partition(":")
    return (CATALOG_ROOT / "reference-sprites" / "glitter" / f"{form_id}.png" if variant else
            CATALOG_ROOT / "reference-sprites" / f"{form_id}.png")


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


def source_date_eligible(source: dict, chapter: int | None = None) -> bool:
    """Missing or ambiguous timestamps never qualify for publication."""
    try:
        posted_at = datetime.fromisoformat(source["posted_at"].replace("Z", "+00:00"))
    except (KeyError, AttributeError, TypeError, ValueError):
        return False
    cutoff = CHAPTER_PUBLICATION_CUTOFFS.get(chapter, PUBLICATION_CUTOFF)
    return posted_at.tzinfo is not None and posted_at >= cutoff


# --- Presentation: static chapter pages, i18n strings and page assembly ---------------

STRINGS = {
    "en": {
        "lang_name_en": "EN",
        "lang_name_vi": "Tiếng Việt",
        "site_title": "Critter Formations",
        "chapter_label": "Chapter",
        "chapter_option_label": "Chapter {n}",
        "home_title": "Clash of Critters Formations by Chapter | Critter Formations",
        "home_description": "Browse Clash of Critters Main Stage formations by chapter, with Tatari levels and links to the original player posts.",
        "home_h1": "Clash of Critters Formations",
        "home_intro": [
            "Critter Formations is a fan-made reference for Clash of Critters' Main Stage, collecting 5×5 critter lineups that players have posted in the game's Discord after clearing each stage.",
            "Levels shown are the poster's own reported Tatari level at the time of their clear — not a required minimum. Every card links back to the original Discord post so you can verify the source yourself.",
        ],
        "home_chapters_heading": "Chapters",
        "chapter_count": "{cards} cards · {stages} stages",
        "chapter_count_empty": "No formations yet",
        "chapter_title": "Clash of Critters Chapter {n} Formations (Stages {n}-1–{n}-80) | Critter Formations",
        "chapter_description": "{cards} verified formation cards covering {stages} stages in Chapter {n} (stages {n}-1–{n}-80){level_clause}, with Tatari levels and links to the original Discord posts.",
        "chapter_level_clause": ", observed Tatari levels {lo}–{hi}",
        "chapter_description_empty": "No verified formations are available yet for Chapter {n} (stages {n}-1–{n}-80).",
        "chapter_h1": "Chapter {n} Formations",
        "chapter_nav_aria": "Chapter navigation",
        "prev_chapter": "← Previous chapter",
        "next_chapter": "Next chapter →",
        "empty_chapter_message": "No verified formations available for this chapter yet.",
        "search_label": "Jump to stage",
        "search_placeholder": "e.g. 31-45",
        "search_button": "Go",
        "search_invalid": "Enter a chapter and stage, like 31-45.",
        "search_not_found": "No verified formation for stage {chapter}-{stage} yet.",
        "donation_label": "Finding these formations helpful?",
        "donation_desktop": "Buy me a coffee ☕",
        "donation_mobile": "☕ Donate",
        "donation_aria": "Buy me a coffee via PayPal (opens in a new tab)",
        "posted_by": "Posted by",
        "discord_link_title": "Open the original Discord reference",
        "row_col": "row {row}, column {column}",
        "empty_cell": "Empty · row {row}, column {column}",
        "board_aria": "Stages {stage}: 5 by 5 formation, top row is the front",
        "footer_unofficial": "Unofficial Fan-Created Work, not affiliated with or endorsed by Farlight.",
        "footer_trademark": "Clash of Critters is a trademark of its respective owners.",
        "footer_privacy_label": "Privacy",
        "breadcrumb_home": "Home",
        "og_alt_home": "Critter Formations: Clash of Critters formations by chapter",
        "og_alt_chapter": "Chapter {n} Clash of Critters formations preview",
        "privacy_title": "Privacy Policy | Critter Formations",
        "privacy_description": "How Critter Formations handles visitor data: GitHub Pages hosting, Google Analytics 4, and PayPal donations.",
        "privacy_h1": "Privacy Policy",
        "privacy_sections": [
            ("Overview",
             "<p>Critter Formations is a static website with no accounts, forms, or server-side code of its own. "
             "This page explains what limited data is collected when you visit.</p>"),
            ("Hosting (GitHub Pages)",
             '<p>This site is hosted on GitHub Pages. GitHub may log visitor IP addresses and request data for '
             'security purposes. See GitHub’s <a href="https://docs.github.com/en/site-policy/privacy-policies/github-general-privacy-statement" '
             'target="_blank" rel="noopener noreferrer">General Privacy Statement</a>.</p>'),
            ("Analytics (Google Analytics 4)",
             '<p>This site uses Google Analytics 4 to understand traffic and improve the content. GA4 sets cookies '
             'such as <code>_ga</code> and collects usage data including pages viewed, approximate location, and '
             'device/browser information. See Google’s <a href="https://policies.google.com/technologies/partner-sites" '
             'target="_blank" rel="noopener noreferrer">policy on partner sites</a>. You can opt out using the '
             '<a href="https://tools.google.com/dlpage/gaoptout" target="_blank" rel="noopener noreferrer">Google Analytics '
             'Opt-out Browser Add-on</a>.</p>'),
            ("Donations (PayPal)",
             '<p>The donate button links to PayPal, which processes payments under its own '
             '<a href="https://www.paypal.com/myaccount/privacy/privacyStatementFull" target="_blank" rel="noopener noreferrer">'
             'privacy policy</a>. This site never sees your card or payment details.</p>'),
            ("Discord links",
             "<p>Card titles and poster names link to the original Discord posts used as sources. Visiting those "
             "links is subject to Discord’s own privacy practices.</p>"),
            ("No accounts, no forms, no data sold",
             "<p>This site does not require an account, does not include any forms, does not sell data, and does "
             "not itself store any personal data.</p>"),
            ("Contact",
             '<p>Questions about this policy can be filed as a '
             '<a href="https://github.com/qaz6209031/clash-critters-formations/issues" target="_blank" rel="noopener noreferrer">'
             'GitHub issue</a>.</p>'),
            ("Effective date", "<p>October 27, 2026.</p>"),
        ],
    },
    "vi": {
        "lang_name_en": "EN",
        "lang_name_vi": "Tiếng Việt",
        "site_title": "Critter Formations",
        "chapter_label": "Chương",
        "chapter_option_label": "Chương {n}",
        "home_title": "Đội Hình Chiến Thú Hỗn Chiến Theo Chương | Critter Formations",
        "home_description": "Xem đội hình Main Stage của Chiến Thú Hỗn Chiến (Clash of Critters) theo từng chương, kèm cấp Tatari và liên kết đến bài đăng gốc của người chơi.",
        "home_h1": "Đội Hình Chiến Thú Hỗn Chiến",
        "home_intro": [
            "Critter Formations là trang tổng hợp không chính thức dành cho Main Stage của Chiến Thú Hỗn Chiến (Clash of Critters), thu thập các đội hình 5×5 mà người chơi đã đăng trên Discord của game sau khi vượt qua từng màn.",
            "Cấp độ hiển thị là cấp Tatari do người đăng tự báo cáo tại thời điểm họ vượt màn — không phải mức tối thiểu bắt buộc. Mỗi thẻ đều có liên kết trực tiếp đến bài đăng Discord gốc để bạn có thể tự kiểm chứng.",
        ],
        "home_chapters_heading": "Các chương",
        "chapter_count": "{cards} đội hình · {stages} màn",
        "chapter_count_empty": "Chưa có đội hình",
        "chapter_title": "Đội hình Chiến Thú Hỗn Chiến Chương {n} (Clash of Critters) | Critter Formations",
        "chapter_description": "{cards} đội hình đã được xác minh, bao phủ {stages} màn trong Chương {n} (màn {n}-1–{n}-80){level_clause}, kèm cấp Tatari và liên kết đến bài đăng Discord gốc.",
        "chapter_level_clause": ", cấp Tatari quan sát được {lo}–{hi}",
        "chapter_description_empty": "Chưa có đội hình nào được xác minh cho Chương {n} (màn {n}-1–{n}-80).",
        "chapter_h1": "Đội hình Chương {n}",
        "chapter_nav_aria": "Điều hướng chương",
        "prev_chapter": "← Chương trước",
        "next_chapter": "Chương sau →",
        "empty_chapter_message": "Chưa có đội hình nào được xác minh cho chương này.",
        "search_label": "Đi đến màn",
        "search_placeholder": "ví dụ: 31-45",
        "search_button": "Đi",
        "search_invalid": "Nhập chương và màn, ví dụ 31-45.",
        "search_not_found": "Chưa có đội hình nào được xác minh cho màn {chapter}-{stage}.",
        "donation_label": "Thấy các đội hình này hữu ích?",
        "donation_desktop": "Mời tôi một ly cà phê ☕",
        "donation_mobile": "☕ Ủng hộ",
        "donation_aria": "Mời một ly cà phê qua PayPal (mở tab mới)",
        "posted_by": "Đăng bởi",
        "discord_link_title": "Mở bài đăng Discord gốc",
        "row_col": "hàng {row}, cột {column}",
        "empty_cell": "Trống · hàng {row}, cột {column}",
        "board_aria": "Các màn {stage}: đội hình 5x5, hàng trên cùng là hàng đầu",
        "footer_unofficial": "Nội dung do người hâm mộ tạo (không chính thức), không liên kết hoặc được Farlight xác nhận.",
        "footer_trademark": "Clash of Critters là nhãn hiệu thuộc về chủ sở hữu tương ứng.",
        "footer_privacy_label": "Quyền riêng tư",
        "breadcrumb_home": "Trang chủ",
        "og_alt_home": "Critter Formations: đội hình Clash of Critters theo chương",
        "og_alt_chapter": "Hình xem trước đội hình Clash of Critters Chương {n}",
        "privacy_title": "Chính Sách Quyền Riêng Tư | Critter Formations",
        "privacy_description": "Cách Critter Formations xử lý dữ liệu khách truy cập: lưu trữ trên GitHub Pages, Google Analytics 4, và quyên góp qua PayPal.",
        "privacy_h1": "Chính Sách Quyền Riêng Tư",
        "privacy_sections": [
            ("Tổng quan",
             "<p>Critter Formations là một trang web tĩnh, không có tài khoản, không có biểu mẫu và không có mã "
             "phía máy chủ riêng. Trang này giải thích dữ liệu hạn chế nào được thu thập khi bạn truy cập.</p>"),
            ("Lưu trữ (GitHub Pages)",
             '<p>Trang này được lưu trữ trên GitHub Pages. GitHub có thể ghi lại địa chỉ IP của khách truy cập và '
             'dữ liệu yêu cầu vì mục đích an ninh. Xem <a href="https://docs.github.com/en/site-policy/privacy-policies/github-general-privacy-statement" '
             'target="_blank" rel="noopener noreferrer">Tuyên bố Quyền riêng tư chung của GitHub</a>.</p>'),
            ("Phân tích (Google Analytics 4)",
             '<p>Trang này sử dụng Google Analytics 4 để hiểu lưu lượng truy cập và cải thiện nội dung. GA4 đặt '
             'cookie như <code>_ga</code> và thu thập dữ liệu sử dụng bao gồm số trang đã xem, vị trí gần đúng và '
             'thông tin thiết bị/trình duyệt. Xem <a href="https://policies.google.com/technologies/partner-sites" '
             'target="_blank" rel="noopener noreferrer">chính sách của Google về trang đối tác</a>. Bạn có thể từ '
             'chối bằng <a href="https://tools.google.com/dlpage/gaoptout" target="_blank" rel="noopener noreferrer">'
             'Tiện ích từ chối Google Analytics</a>.</p>'),
            ("Quyên góp (PayPal)",
             '<p>Nút quyên góp liên kết đến PayPal, xử lý thanh toán theo '
             '<a href="https://www.paypal.com/myaccount/privacy/privacyStatementFull" target="_blank" rel="noopener noreferrer">'
             'chính sách quyền riêng tư</a> riêng của họ. Trang này không bao giờ thấy thông tin thẻ hoặc thanh toán của bạn.</p>'),
            ("Liên kết Discord",
             "<p>Tên màn và tên người đăng liên kết đến bài đăng Discord gốc được dùng làm nguồn. Việc truy cập "
             "các liên kết đó tuân theo chính sách quyền riêng tư riêng của Discord.</p>"),
            ("Không tài khoản, không biểu mẫu, không bán dữ liệu",
             "<p>Trang này không yêu cầu tài khoản, không có biểu mẫu, không bán dữ liệu, và không tự lưu trữ bất "
             "kỳ dữ liệu cá nhân nào.</p>"),
            ("Liên hệ",
             '<p>Thắc mắc về chính sách này có thể gửi qua '
             '<a href="https://github.com/qaz6209031/clash-critters-formations/issues" target="_blank" rel="noopener noreferrer">'
             'GitHub issue</a>.</p>'),
            ("Ngày có hiệu lực", "<p>27 tháng 10, 2026.</p>"),
        ],
    },
}


def lang_prefix(lang: str) -> str:
    return "" if lang == "en" else "/vi"


def page_path(lang: str, page_type: str, chapter: int | None = None) -> str:
    prefix = lang_prefix(lang)
    if page_type == "home":
        return f"{prefix}/" if prefix else "/"
    if page_type == "chapter":
        return f"{prefix}/chapter/{chapter}/"
    if page_type == "privacy":
        return f"{prefix}/privacy.html"
    raise ValueError(page_type)


def hreflang_links(page_type: str, chapter: int | None = None) -> str:
    links = [f'<link rel="alternate" hreflang="{lang}" href="{SITE_URL + page_path(lang, page_type, chapter)}">'
             for lang in LANGS]
    links.append(f'<link rel="alternate" hreflang="x-default" href="{SITE_URL + page_path("en", page_type, chapter)}">')
    return "\n  ".join(links)


def og_meta(lang: str, page_type: str, title: str, description: str, image_path: str, image_alt: str,
            chapter: int | None = None) -> str:
    url = SITE_URL + page_path(lang, page_type, chapter)
    image_url = f"{SITE_URL}/{image_path}"
    locale = "en_US" if lang == "en" else "vi_VN"
    alt_locale = "vi_VN" if lang == "en" else "en_US"
    return "\n  ".join([
        '<meta property="og:type" content="website">',
        f'<meta property="og:site_name" content="{html.escape(STRINGS[lang]["site_title"], quote=True)}">',
        f'<meta property="og:title" content="{html.escape(title, quote=True)}">',
        f'<meta property="og:description" content="{html.escape(description, quote=True)}">',
        f'<meta property="og:url" content="{url}">',
        f'<meta property="og:image" content="{image_url}">',
        '<meta property="og:image:width" content="1200">',
        '<meta property="og:image:height" content="630">',
        f'<meta property="og:image:alt" content="{html.escape(image_alt, quote=True)}">',
        f'<meta property="og:locale" content="{locale}">',
        f'<meta property="og:locale:alternate" content="{alt_locale}">',
    ])


def twitter_meta(title: str, description: str, image_path: str) -> str:
    image_url = f"{SITE_URL}/{image_path}"
    return "\n  ".join([
        '<meta name="twitter:card" content="summary_large_image">',
        f'<meta name="twitter:title" content="{html.escape(title, quote=True)}">',
        f'<meta name="twitter:description" content="{html.escape(description, quote=True)}">',
        f'<meta name="twitter:image" content="{image_url}">',
    ])


def jsonld_script(data: dict) -> str:
    encoded = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    return f'<script type="application/ld+json">{encoded}</script>'


def website_jsonld(lang: str) -> str:
    url = SITE_URL + page_path(lang, "home")
    data = {
        "@context": "https://schema.org",
        "@type": "WebSite",
        "name": STRINGS[lang]["site_title"],
        "url": url,
        "inLanguage": "en-US" if lang == "en" else "vi-VN",
        "potentialAction": {
            "@type": "SearchAction",
            "target": {"@type": "EntryPoint", "urlTemplate": f"{url}?stage={{search_term_string}}"},
            "query-input": "required name=search_term_string",
        },
    }
    return jsonld_script(data)


def breadcrumb_jsonld(lang: str, chapter: int) -> str:
    S = STRINGS[lang]
    data = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": S["breadcrumb_home"], "item": SITE_URL + page_path(lang, "home")},
            {"@type": "ListItem", "position": 2, "name": S["chapter_option_label"].format(n=chapter),
             "item": SITE_URL + page_path(lang, "chapter", chapter)},
        ],
    }
    return jsonld_script(data)


def itemlist_jsonld(lang: str, chapter: int, group_list: list[dict]) -> str:
    url = SITE_URL + page_path(lang, "chapter", chapter)
    items = [{"@type": "ListItem", "position": i + 1, "name": group["stage_label"], "url": f'{url}#{group["card_id"]}'}
              for i, group in enumerate(group_list)]
    data = {"@context": "https://schema.org", "@type": "ItemList", "itemListElement": items}
    return jsonld_script(data)


def chapter_options(lang: str, selected: int | None = None) -> str:
    label = STRINGS[lang]["chapter_option_label"]
    return "".join(
        f'<option value="{c["chapter"]}"' + (' selected' if c["chapter"] == selected else '')
        + f'>{html.escape(label.format(n=c["chapter"]))}</option>'
        for c in CHAPTERS)


_TEMPLATE_MARKER = re.compile(r"<!--\s*[A-Z][A-Z_]*\s*-->")


def render_shell(template: str, lang: str, page_type: str, *, title: str, description: str, canonical_path: str,
                  h1: str, main_content: str, og_image_path: str, og_image_alt: str, jsonld_scripts: list[str],
                  chapter: int | None = None, robots_noindex: bool = False) -> str:
    S = STRINGS[lang]
    other_lang = "vi" if lang == "en" else "en"
    lang_switch_nav = "\n        ".join(
        f'<a href="{page_path(l, page_type, chapter)}"' + (' aria-current="page"' if l == lang else '')
        + f'>{html.escape(S["lang_name_" + l])}</a>'
        for l in LANGS)
    mapping = {
        "HTML_LANG": lang,
        "DESCRIPTION": html.escape(description, quote=True),
        "TITLE": html.escape(title),
        "CANONICAL_URL": SITE_URL + canonical_path,
        "ROBOTS_META": '<meta name="robots" content="noindex,follow">' if robots_noindex else "",
        "HREFLANG_LINKS": hreflang_links(page_type, chapter),
        "OG_META": og_meta(lang, page_type, title, description, og_image_path, og_image_alt, chapter),
        "TWITTER_META": twitter_meta(title, description, og_image_path),
        "JSONLD_SCRIPTS": "\n  ".join(jsonld_scripts),
        "HOME_HREF": page_path(lang, "home"),
        "SITE_TITLE_TEXT": html.escape(S["site_title"]),
        "LANG_SWITCH_NAV": lang_switch_nav,
        "CHAPTER_LABEL_TEXT": html.escape(S["chapter_label"]),
        "CHAPTER_OPTIONS": chapter_options(lang, chapter),
        "SEARCH_LABEL_TEXT": html.escape(S["search_label"]),
        "SEARCH_PLACEHOLDER_TEXT": html.escape(S["search_placeholder"], quote=True),
        "SEARCH_BUTTON_TEXT": html.escape(S["search_button"]),
        "DONATION_LABEL_TEXT": html.escape(S["donation_label"]),
        "DONATION_ARIA_TEXT": html.escape(S["donation_aria"], quote=True),
        "DONATION_DESKTOP_TEXT": html.escape(S["donation_desktop"]),
        "DONATION_MOBILE_TEXT": html.escape(S["donation_mobile"]),
        "H1_TEXT": html.escape(h1),
        "MAIN_CONTENT": main_content,
        "FOOTER_UNOFFICIAL_TEXT": html.escape(S["footer_unofficial"]),
        "FOOTER_TRADEMARK_TEXT": html.escape(S["footer_trademark"]),
        "FOOTER_PRIVACY_HREF": page_path(lang, "privacy"),
        "FOOTER_PRIVACY_LABEL_TEXT": html.escape(S["footer_privacy_label"]),
        "FOOTER_LANG_HREF": page_path(other_lang, page_type, chapter),
        "FOOTER_LANG_LABEL_TEXT": html.escape(S["lang_name_" + other_lang]),
        "JS_CONFIG_JSON": json.dumps({
            "lang": lang,
            "langPrefix": lang_prefix(lang),
            "siteUrl": SITE_URL,
            "pageType": page_type,
            "chapter": chapter,
            "strings": {
                "searchInvalid": S["search_invalid"],
                "searchNotFound": S["search_not_found"],
            },
        }, ensure_ascii=False).replace("</", "<\\/"),
    }
    page = template
    for key, value in mapping.items():
        token = f"<!-- {key} -->"
        assert token in page, f"Missing template marker {token}"
        page = page.replace(token, value)
    assert not _TEMPLATE_MARKER.search(page), "Unfilled template marker remains"
    return page


def render_card(group: dict, lang: str, is_first: bool) -> str:
    S = STRINGS[lang]
    chapter = group["chapter"]
    cells_html = []
    for r, c, key, sprite_id in group["cell_sprites"]:
        if key:
            unit = unit_record(key, r, c)
            label = f'{unit["name"]} · T{unit["tier"]}'
            if unit["variant"] == "glitter":
                label += " · Glitter"
            label += " · " + S["row_col"].format(row=r, column=c)
            loading_attr = "" if is_first else ' loading="lazy"'
            cells_html.append(
                f'<div class="cell occupied" title="{html.escape(label)}">'
                f'<img src="/sprites/{sprite_id}.png" alt="{html.escape(label)}" width="200" height="200" '
                f'decoding="async" draggable="false"{loading_attr}></div>')
        else:
            empty_label = S["empty_cell"].format(row=r, column=c)
            cells_html.append(f'<div class="cell" aria-label="{html.escape(empty_label)}"></div>')
    stage = group["stage_label"]
    card_id = group["card_id"]
    source = group["source"]
    board_aria = html.escape(S["board_aria"].format(stage=stage), quote=True)
    return (
        f'<article class="stage" id="{card_id}" data-chapter="{chapter}" data-stages="{group["stage_numbers_attr"]}" '
        f'data-formation-id="{group["formation_id"]}" data-source-message-ids="{group["source_ids_attr"]}" '
        f'data-posted-at="{html.escape(group["posted_at_min"], quote=True)}">'
        f'<h2 class="stage-title"><a href="{source["source_message_url"]}" target="_blank" rel="noopener noreferrer" '
        f'title="{html.escape(S["discord_link_title"], quote=True)}">{stage}</a>'
        f'<span class="level" title="{group["level_title"]}" aria-label="{group["level_title"]}">{group["level_text"]}</span>'
        f'</h2>'
        f'<p class="poster">{S["posted_by"]} {group["poster_links"]}</p>'
        f'<div class="board" role="group" aria-label="{board_aria}">{"".join(cells_html)}</div></article>')


def render_home_main(lang: str, chapter_stats: dict) -> str:
    S = STRINGS[lang]
    intro = "".join(f"<p>{html.escape(p)}</p>" for p in S["home_intro"])
    items = []
    for c in CHAPTERS:
        n = c["chapter"]
        stats = chapter_stats[n]
        empty = stats["cards"] == 0
        count_text = (S["chapter_count_empty"] if empty else
                      S["chapter_count"].format(cards=stats["cards"], stages=stats["stages"]))
        items.append(
            f'<li><a class="{"is-empty" if empty else ""}" href="{page_path(lang, "chapter", n)}">'
            f'<span class="chapter-name">{html.escape(S["chapter_option_label"].format(n=n))}</span>'
            f'<span class="chapter-count">{html.escape(count_text)}</span></a></li>')
    heading = html.escape(S["home_chapters_heading"])
    return (f'<section class="intro">{intro}</section>'
            f'<h2 class="section-heading">{heading}</h2>'
            f'<ul class="chapter-grid" aria-label="{heading}">{"".join(items)}</ul>')


def render_chapter_main(lang: str, chapter_number: int, cards_html: list[str]) -> str:
    S = STRINGS[lang]
    numbers = [c["chapter"] for c in CHAPTERS]
    idx = numbers.index(chapter_number)
    prev_n = numbers[idx - 1] if idx > 0 else None
    next_n = numbers[idx + 1] if idx < len(numbers) - 1 else None

    def nav_link(n, label):
        if n is None:
            return f'<span class="disabled">{html.escape(label)}</span>'
        return f'<a href="{page_path(lang, "chapter", n)}">{html.escape(label)}</a>'

    pagination = (
        f'<nav class="chapter-pagination" aria-label="{html.escape(S["chapter_nav_aria"], quote=True)}">'
        f'{nav_link(prev_n, S["prev_chapter"])}'
        f'<span>{html.escape(S["chapter_option_label"].format(n=chapter_number))}</span>'
        f'{nav_link(next_n, S["next_chapter"])}</nav>')
    if cards_html:
        body = f'<div class="cards-grid" id="chapter-cards">{"".join(cards_html)}</div>'
    else:
        body = f'<p class="empty-chapter">{html.escape(S["empty_chapter_message"])}</p>'
    not_found = '<p id="stage-not-found" class="stage-not-found" hidden></p>'
    return pagination + body + not_found


def render_privacy_main(lang: str) -> str:
    S = STRINGS[lang]
    sections = "".join(f'<section><h2>{html.escape(heading)}</h2>{body}</section>'
                        for heading, body in S["privacy_sections"])
    return f'<div class="privacy-content">{sections}</div>'


def og_font(size: int, bold: bool = True) -> ImageFont.FreeTypeFont:
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/dejavu/DejaVuSans.ttf",
        "/Library/Fonts/Arial Bold.ttf" if bold else "/Library/Fonts/Arial.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def render_og_image(path: Path, heading: str, subtitle: str, caption: str) -> None:
    size = (1200, 630)
    background = (245, 247, 240)
    accent = (71, 124, 56)
    text_color = (36, 59, 43)
    muted_color = (83, 107, 73)
    image = Image.new("RGB", size, background)
    draw = ImageDraw.Draw(image)
    draw.rectangle([0, 0, size[0], 16], fill=accent)
    draw.rectangle([0, size[1] - 16, size[0], size[1]], fill=accent)
    icon_path = ROOT / "site" / "favicon-tatari.png"
    if icon_path.exists():
        icon = Image.open(icon_path).convert("RGB").resize((150, 150))
        image.paste(icon, (60, 90))
    text_x = 250
    draw.text((text_x, 170), heading, font=og_font(66), fill=text_color)
    draw.text((text_x, 270), subtitle, font=og_font(34, bold=False), fill=muted_color)
    if caption:
        draw.text((text_x, 320), caption, font=og_font(28, bold=False), fill=muted_color)
    palette_image = image.convert("P", palette=Image.ADAPTIVE, colors=64)
    path.parent.mkdir(parents=True, exist_ok=True)
    palette_image.save(path, format="PNG", optimize=True)


def build() -> None:
    formations = []
    stages = []
    sprites = {}
    groups = {}
    for reviewed in REVIEWED:
        source = SOURCES[reviewed["source_message_id"]]
        board_source = SOURCES[reviewed.get("board_source_message_id", source["id"])]
        reference_ids = list(dict.fromkeys([
            source["id"], board_source["id"], *reviewed.get("supporting_message_ids", [])]))
        excluded_reference_ids = [message_id for message_id in reference_ids
                                  if not source_date_eligible(SOURCES[message_id], reviewed["chapter"])]
        selected = reviewed.get("selected_for_website", True) and not excluded_reference_ids
        chapter = reviewed["chapter"]
        start, end = reviewed["stage_start"], reviewed["stage_end"]
        caption_numbers = reviewed.get("caption_stage_numbers", list(range(start, end + 1)))
        website_numbers = reviewed.get("website_stage_numbers", caption_numbers)
        assert caption_numbers and len(set(caption_numbers)) == len(caption_numbers), source["id"]
        assert all(isinstance(n, int) and not isinstance(n, bool) and 1 <= n <= 80
                   for n in caption_numbers), source["id"]
        assert (min(caption_numbers), max(caption_numbers)) == (start, end), source["id"]
        assert len(set(website_numbers)) == len(website_numbers), source["id"]
        assert set(website_numbers) <= set(caption_numbers), source["id"]
        selected = selected and bool(website_numbers)
        formation_id = (f'{source["id"]}:chapter-{chapter}'
                        if SOURCE_RECORD_COUNTS[source["id"]] > 1 else source["id"])
        displayed = reviewed["screenshot_displayed_stage"]
        credit, board = reviewed["credited_player_name"], reviewed["board"]
        level = reviewed["tatari_level"]
        level_source = reviewed.get("tatari_level_source", "image")
        if level is None:
            assert 1 <= chapter <= 10 and level_source == "unknown", source["id"]
        else:
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
        if selected:
            family_counts = Counter(unit["family_id"] for unit in lineup)
            duplicate_families = [family for family, count in family_counts.items() if count > 1]
            assert not duplicate_families, (
                f'{source["id"]}: chapter {chapter} repeats Tatari families: {duplicate_families}. '
                "Recheck the original image before publishing.")
        signature = json.dumps([(u["position"], u["form_id"], u["variant"])
                                for u in lineup], separators=(",", ":"))
        formations.append({
            "formation_id": formation_id,
            "chapter": chapter,
            "extraction_revision": reviewed.get("extraction_revision", 2 if chapter == 47 and any("serrabloom:glitter" in row for row in board) else 1),
            "source_message_id": source["id"],
            "source_message_url": source["source_message_url"],
            "permalink_method": source["permalink_method"],
            "source_server": "Clash of Critters",
            "source_server_id": "1343763804349267989",
            "source_thread_id": source.get("channel_id") or source["source_message_url"].split("/")[-2],
            "source_thread": source.get("source_thread", "Beating Zobos In Public (F2P Journey). Chapter: 41 42 43 44 45 46 47 48 49 50"),
            "source_type": reviewed.get("source_type", "mixed"),
            "discord_display_name": source["display_name"],
            "discord_username": source.get("discord_username"),
            "credited_player_name": credit,
            "credit_basis": reviewed.get("credit_basis", "Name in the message caption; not a verified Discord username."),
            "posted_at": source.get("posted_at"),
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
            "cleared_stages": [f"{chapter}-{n}" for n in caption_numbers],
            "website_stages": [f"{chapter}-{n}" for n in website_numbers] if selected else [],
            "caption_stage_range": reviewed.get("caption_stage_range"),
            "stage_assignment": reviewed.get("stage_assignment_basis") or ("Author's caption; reconstructed later because the original screenshot was missed." if recreated else "Author's caption; screenshot shows the next stage after the reported clear/range, including the next chapter's stage 1 after stage 80."),
            "grid": {"rows": 5, "columns": 5, "orientation": "Rows front to rear (top to bottom); columns left to right."},
            "lineup": lineup,
            "formation_hash": hashlib.sha256(signature.encode()).hexdigest(),
            "supersedes_message_id": None,
            "selected_for_website": selected,
            "source_date_eligible": not excluded_reference_ids,
            "excluded_reference_message_ids": excluded_reference_ids,
            "publication_exclusion_reason": (("Source or supporting evidence was posted on/before October 21, 2026, or has no verified timestamp."
                                               if chapter in CHAPTER_PUBLICATION_CUTOFFS else
                                               "Source or supporting evidence was posted on/before August 27, 2026, or has no verified timestamp.")
                                              if excluded_reference_ids else None),
            "selection_reason": reviewed.get("selection_reason"),
            "needs_review": needs_review,
            "review_notes": reviewed["notes"] or "Exact forms and occupied cells visually matched to the supplied planner catalog. Glitter variants matched separately where present.",
            "outcome_basis": "Author-reported clear; not independently tested in game.",
        })
        if "deployed_count" in reviewed:
            formations[-1]["deployed_count"] = reviewed["deployed_count"]
        if "caption_stage_numbers_original" in reviewed:
            formations[-1]["caption_stage_numbers_original"] = reviewed["caption_stage_numbers_original"]
        if "source_image_number" in reviewed:
            formations[-1]["source_image_number"] = reviewed["source_image_number"]
        if "extraction_corrections" in reviewed:
            formations[-1]["extraction_corrections"] = reviewed["extraction_corrections"]
        for relationship in ("replaces_website_source_message_ids", "replaced_by_website_source_message_ids"):
            if relationship in reviewed:
                formations[-1][relationship] = reviewed[relationship]
        if "board_source_message_id" in reviewed:
            formations[-1]["board_source_message_id"] = board_source["id"]
            formations[-1]["board_source_message_url"] = board_source["source_message_url"]
        if "tier_assignment_basis" in reviewed:
            formations[-1]["tier_assignment_basis"] = reviewed["tier_assignment_basis"]
        if "supporting_message_ids" in reviewed:
            formations[-1]["supporting_messages"] = [
                {key: SOURCES[message_id].get(key)
                 for key in ("id", "source_message_url", "text", "posted_at")}
                for message_id in reviewed["supporting_message_ids"]]
        if not formations[-1]["selected_for_website"]:
            continue
        for n in website_numbers:
            stage = f"{chapter}-{n}"
            stages.append({"stage": stage, "formation_id": formation_id, "tatari_level": level, "level_from_reconstruction": recreated})
        blocks = {}
        for number in website_numbers:
            block = stage_block(number) if chapter <= 30 or 32 <= chapter <= 39 or chapter >= 50 else None
            blocks.setdefault(block, []).append(number)
        level_observation = (" in a recreated screenshot; original clear level unverified" if recreated else
                             "; " + reviewed["tatari_level_basis"] if "tatari_level_basis" in reviewed else
                             " in the post-clear screenshot")
        for block, numbers in blocks.items():
            group = groups.setdefault((chapter, block, formations[-1]["formation_hash"]), {
                "chapter": chapter, "formation_id": formation_id,
                "board": board, "numbers": [], "source": source, "levels": set(),
                "posters": {}, "level_notes": [], "source_ids": [], "posted_at": [],
            })
            group["numbers"].extend(numbers)
            group["source_ids"].append(source["id"])
            group["posted_at"].append(source["posted_at"])
            group["levels"].add(level)
            group["posters"].setdefault(source["display_name"], source["source_message_url"])
            group["level_notes"].append(f"{stage_label(numbers, chapter)}: Tatari Lv.{level if level is not None else ' Unknown'}" + level_observation)
            if needs_review or range_check:
                group["level_notes"].append(reviewed["notes"])

    stages.sort(key=lambda stage: tuple(map(int, stage["stage"].split("-"))))
    ordered_groups = sorted(groups.values(), key=lambda group: (group["chapter"], min(group["numbers"])))
    assert len({formation["formation_id"] for formation in formations}) == len(formations), "Duplicate formation IDs"
    for chapter in [30, *range(32, 40), *range(50, 74)]:
        chapter_groups = [group for group in ordered_groups if group["chapter"] == chapter]
        available = {int(stage["stage"].split("-")[1]) for stage in stages
                     if stage["stage"].startswith(f"{chapter}-")}
        expected_blocks = [numbers for decade in range(0, 80, 10)
                           for numbers in (list(range(decade + 1, decade + 5)),
                                           list(range(decade + 5, decade + 10)), [decade + 10])]
        expected_blocks = [present for block in expected_blocks
                           if (present := [number for number in block if number in available])]
        if 50 <= chapter <= 63:
            # Casey changes boards within some regular blocks; preserve those captioned splits.
            assert all(len({stage_block(number) for number in group["numbers"]}) == 1
                       for group in chapter_groups), chapter
            assert sorted(number for group in chapter_groups for number in group["numbers"]) == sorted(available), chapter
        else:
            assert [sorted(set(group["numbers"])) for group in chapter_groups] == expected_blocks, chapter

    for group in ordered_groups:
        chapter = group["chapter"]
        group["stage_label"] = stage_label(group["numbers"], chapter)
        group["card_id"] = f"stage-{chapter}-{min(group['numbers'])}"
        group["stage_numbers_attr"] = ",".join(f"{chapter}-{n}" for n in sorted(set(group["numbers"])))
        cell_sprites = []
        for r, row in enumerate(group["board"], 1):
            for c, key in enumerate(row, 1):
                if key:
                    sprite_id = key.replace(":", "-")
                    sprites.setdefault(sprite_id, sprite_path(key))
                    cell_sprites.append((r, c, key, sprite_id))
                else:
                    cell_sprites.append((r, c, None, None))
        group["cell_sprites"] = cell_sprites
        level_values = [str(level) for level in sorted(v for v in group["levels"] if v is not None)]
        if None in group["levels"]:
            level_values.append("Unknown")
        group["level_text"] = ("Lv. " if level_values == ["Unknown"] else "Lv.") + "/".join(level_values)
        group["level_title"] = html.escape("; ".join(group["level_notes"]))
        group["poster_links"] = ", ".join(
            f'<a href="{html.escape(url, quote=True)}" target="_blank" rel="noopener noreferrer">{html.escape(name)}</a>'
            for name, url in group["posters"].items())
        group["source_ids_attr"] = ",".join(dict.fromkeys(group["source_ids"]))
        group["posted_at_min"] = min(group["posted_at"],
                                      key=lambda timestamp: datetime.fromisoformat(timestamp.replace("Z", "+00:00")))

    for chapter_number in {group["chapter"] for group in ordered_groups}:
        ids = [group["card_id"] for group in ordered_groups if group["chapter"] == chapter_number]
        assert len(ids) == len(set(ids)), f"Duplicate stage anchor ids in chapter {chapter_number}"

    requested_stages = [f"{c['chapter']}-{n}" for c in CHAPTERS for n in range(c["first"], c["last"] + 1)]
    published_stages = {stage["stage"] for stage in stages}
    assert len(published_stages) == len(stages), "More than one selected formation for a stage"
    assert published_stages <= set(requested_stages), "Stage outside the reviewed chapter ranges"
    unavailable_stages = [stage for stage in requested_stages if stage not in published_stages]
    publication_policy = {
        "posted_after_date": "2026-08-27",
        "timezone": "America/Los_Angeles",
        "posted_at_minimum_inclusive": PUBLICATION_CUTOFF.isoformat().replace("+00:00", "Z"),
        "timestamp_basis": "Original message posting time, not edit time or collection time.",
        "supporting_evidence_must_qualify": True,
        "chapter_overrides": {
            str(chapter): {
                "posted_after_date": "2026-10-21",
                "posted_at_minimum_inclusive": cutoff.isoformat().replace("+00:00", "Z"),
                "reason": "Enemy formations changed in the October 21 update.",
            }
            for chapter, cutoff in CHAPTER_PUBLICATION_CUTOFFS.items()
        },
        "missing_timestamp": "Exclude from publication.",
        "missing_replacement": "Hide the stage; preserve historical records in the archive.",
    }
    dataset = {
        "schema_version": "1.14",
        "collected_at": "2026-10-25",
        "chapter_56_63_update": "October 25: 196 original Casey image posts provide 201 chapter records, replacing 615 stages with individually lower player levels across chapters 56–63. Chapters 56–58 and 60–62 use Casey throughout; 59-46 through 59-49 retain prior references because Casey’s caption has a contradictory chapter endpoint, and 63-60 onward retain their previous selections because no newer Casey caption was found. All historical records and other chapters are preserved. Exact photographed tiers, 25-cell positions, the 14-unit 61-21–22 board, and costume notes are retained. Original/source timestamps and same-post numeric levels were checked. Inclusive ranges and late screenshots retain source review notes.",
        "chapter_24_28_update": "October 24: revamped chapters 24–28 require original and supporting posts after October 21, 2026 America/Los_Angeles. Only visually identified boards with a same-source numeric player level are published. Pre-update references remain archived and unsupported stages are empty. All other chapter selections are preserved.",
        "chapter_50_update": "October 17: chapter 50 only, as clarified by the owner. Twenty-seven visually reviewed Casey posts replace all 80 chapter 50 stages after individual comparisons. Player levels 1013, 1030 and 1032 are each lower than the previous nil references at 1056, 1110 or 1121. Every level comes from the same post’s image or explicit caption. All 24 prior nil records remain preserved, and every other chapter retains its stage boards, levels and selected sources. The 50-64 caption says the screenshot was taken late and displays 50-70; its own inventory level 1032 is preserved with a reconstruction/coverage-review flag and no inferred extra stages. Other inclusive ranges retain coverage-review notes where completion of every stage is not visible. Bosses remain separate, with shorter captioned formation changes preserved.",
        "chapter_51_update": "October 16: owner-requested Casey replacements for 51-11 through 51-80. Twenty original October 11–12 posts at level 1048 were visually reviewed. All 24 original Pika records remain preserved, with website replacement relationships; 51-1 through 51-10 and all other chapters are preserved. Casey's captions are inclusive, unlike Pika's usual next-stage endpoints. The 51-50/51-51 record retains a coverage-review flag because the screenshot shows 51-51; that stage relies on Casey's explicit two-stage caption and the next post starting at 51-52. Units and levels are visually clear. Gameplay outcomes remain author-reported.",
        "chapter_52_55_update": "October 16: 109 visually reviewed Casey posts supply 112 chapter-specific records and replace 318 stages in chapters 52–55 after individual comparisons against the previous 66pika levels. Casey levels are 1048–1059 in chapter 52, 1059–1099 in chapter 53, 1099–1116 in chapter 54 and 1116–1124 in chapter 55. Every level is readable in its own screenshot or caption. Original Pika records are preserved with website replacement relationships. No explicit Casey caption covers 53-21 or 53-22, so those two stages retain their previous Pika reference. Inclusive ranges that extend beyond visible completion retain coverage-review flags. All other stage boards, levels and sources are preserved. Casey's latest collected post is 55-80; no chapter 56 or later Casey reference was found at the thread's present end.",
        "feedback_review": "October 12: add Glorp’s confirmed 5-70 clear at level 112; select TextOffender’s confirmed 13-30 clear at level 229, dojo 33322; correct 23 source-image transcriptions covering 65 stages. Selected boards must have unique Tatari families. Corrections retain source IDs, extraction revisions and cell history. Previous source claims remain preserved; gameplay outcomes are author-reported.",
        "collection_method": "Authenticated Discord website, read-only browser inspection and attachment downloads.",
        "catalog_reference": {
            "url": CATALOG["source_url"],
            "version": CATALOG["source_version"],
            "data_date": CATALOG["source_data_date"],
            "catalog_sha256": CATALOG["catalog_sha256"],
        },
        "stage_ranges": [{key: c[key] for key in ("chapter", "first", "last")} for c in CHAPTERS],
        "stages": stages,
        "publication_policy": publication_policy,
        "unavailable_stages": unavailable_stages,
        "high_confidence": [formation for formation in formations if not formation["needs_review"]],
        "needs_human_review": [formation for formation in formations if formation["needs_review"]],
        "deduplication": "Source message ID identifies each Discord submission. When one message covers two chapters, chapter-qualified formation IDs distinguish its normalized boards while preserving the shared source message ID. Stage entries reference those formation IDs. Captions retain their exact listed stages; website_stages records the selected subset without filling caption gaps. Cards group exact forms, variants and positions by formation hash. Chapters 1–30, 32–39 and 50–79 keep each 1–4 block, 5–9 block and multiple-of-10 boss separate. Early guide boundaries at stage 6 additionally split a 5–9 block when its formations differ. Existing chapter grouping is preserved. New messages are preserved separately; supersedes_message_id remains null without explicit evidence of replacement.",
        "level_selection_policy": "For chapters 1–10, the owner explicitly allows a missing player level: store null with level source unknown and display Lv. Unknown. Above chapter 10, use a formation only when its Tatari level is readable in the image or explicitly stated in the source message. A stated level is valid without image-level text; preserve whether its source is image or message_text. Do not infer an absent level from adjacent posts or enemy levels. Prefer the lowest supported level among inspected clear candidates, preserving unselected alternatives. For chapters 10–30, 32–39 and 51–79, the user waived exhaustive minimum-level comparison; choose a supported clear covering each required block.",
        "selection_scope": "Chapters 1–9 add manually reviewed post-cutoff references from Chey, tim370514, Hawkeye, Reynbowz, Adsgolf, The Fifth Pillar, CringeAlot, disen9501 and ARCHER. Unknown player levels are allowed only in chapters 1–10. Help requests, older forwarded originals, ambiguous boards and unverified stage gaps remain unavailable. Pika-style caption endpoints matching the displayed next stage are excluded as uncleared; explicitly inclusive Casey captions retain a coverage-review flag when completion is not visible. Existing chapters 10–79 are preserved. Chapters 41–50 use the supplied reference thread, except 42-15 through 42-19 found through Discord stage-name searches with has:image. Chapters 31 and 40 use Casey's Chapter 19 and onwards thread; chapter 31 uses Casey's September level-579 references for 31-5 through 31-9; Win's August-17 level-549 reference is archived and excluded. Other chapter 31 selections use Casey after comparisons with Harsh, Win, Unown, Antzer and opening-stage candidates. Casey's explicitly stated 596 for 31-10 through 31-12 is accepted as a message-text level; the record remains flagged only because the screenshot displays 31-15. The three Casey references for 31-5 through 31-9 are selected under the posting-date policy. Chapters 32–39 primarily use Antzer’s guide, with Harsh’s chapter 32 opening blocks and chapter 33 gap, Unown’s missing or ambiguous-tier blocks, and Casey’s explicitly stated level 771 for 39-1 through 39-4. Complete caption-supported blocks are kept together and each boss is separate. Chapters 20–30 now use September Vrondius references for stages previously hidden by the posting-date policy. Existing date-eligible Vanhhh, Casey and Vrondius references are retained. Search-found Vanhhh references fill 22-65, 24-74, 26-6 and 26-26; jacobdumbnut fills 27-80 and 28-23; ZERO_SUGAR fills 28-38. The corrected September-19 Vrondius post supplies 28-10 through 28-14; its earlier incorrect-image post is not published. Most replacement levels are explicitly stated in their own source captions. For 26-26, Vanhhh’s screenshot shows level 512 while the caption states 509; use the visible 512 and retain the discrepancy. Exact caption gaps and fewer-than-15 deployed units are preserved. Chapters 51–59 originally use Pika’s guides, with Saber filling 58-11 through 58-14 and 59-1 through 59-4. The October 16 owner-requested update selects Casey’s inclusive-caption references at level 1048 for 51-11 through 51-80, preserving all prior Pika submissions and all other stage selections. The 51-50/51-51 record retains a coverage-review flag because 51-51 relies on the explicit caption rather than a post-completion screenshot. The October 16 continuation additionally selects Casey for 318 stages across chapters 52–55, at supported levels 1048–1124, each lower than the previous 66pika reference. Stages 53-21 and 53-22 retain Pika because Casey has no explicit caption for them. Prior records remain archived, with website replacement relationships. The October 17 chapter-50-only update selects 27 Casey references at levels 1013–1032 for all 80 stages, each lower than nil’s previous 1056–1121; all old submissions and every other chapter selection are preserved. Stage 50-64 retains a delayed-screenshot review note. The author’s correction for 51-10 retains its supporting board post. No server-wide minimum has been established. Levels are source observations or author statements, not independently tested requirements. Chapters 60–69 add visually reviewed Pika references, with Saber filling 62-45 through 62-49 and 63-15 through 63-19, Gallivant filling 65-25 through 65-29, and Tiva’s second attachment filling 66-5 through 66-9 at level 1449. An ambiguous Kayla alternative was not used. Pika captions normally name the next stage as their endpoint; coverage excludes that endpoint when it matches the screenshot stage. Original caption numbers are preserved separately. The explicitly inclusive 67-31 through 67-35 caption shows stage 36; its shared stage 35 is selected from the following block. Chapters 10–19 add 754 of 800 requested stages from 249 manually reviewed chapter-specific records, primarily chiaki’s September guide, with Libertas and Anthi references in chapters 13–14. Jessimika_x’s September 24–29 references fill all 15 remaining chapter 13 gaps at levels 279 and 292 from their own screenshots, preserving all previously selected stages. All posting authors were verified from rendered Discord message headings. Missing and contradictory caption gaps remain unavailable; no stage is inferred from a later screenshot. Same-post explicit tier statements normalize evolved units that still use base artwork. Chapters 70–79 add 416 verified stages from 146 reviewed posts: all stages of 70–73, 47 stages of 74, and 75-1 through 75-49. Pika supplies 70–73 and the opening 74 blocks; Mw and date-eligible alternate posts supply later references. A 75-50 through 75-70 multi-image post has no readable level, and the 76-30 image clips the final level digits, so neither is used. No usable 77–79 reference was found; unsupported stages remain empty. All selections additionally require original source and supporting post timestamps after August 27, 2026 in America/Los_Angeles; earlier references remain archived and unsupported stages are hidden.",
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
            "unavailable_stages": [stage for stage in unavailable_stages if stage.startswith(f"{number}-")],
            "high_confidence": [{**record, "local_image": os.path.relpath(record["local_image_path"], chapter["directory"]) if record["local_image_path"] else None} for record in formations if record["chapter"] == number and not record["needs_review"]],
            "needs_human_review": [{**record, "local_image": os.path.relpath(record["local_image_path"], chapter["directory"]) if record["local_image_path"] else None} for record in formations if record["chapter"] == number and record["needs_review"]],
        }
        (chapter["directory"] / f"stage-{number}-lineups.json").write_text(json.dumps(chapter_dataset, ensure_ascii=False, indent=2) + "\n")
    available_chapters = {group["chapter"] for group in ordered_groups}
    assert available_chapters, "No formations meet the publication policy"

    chapter_groups_map: dict[int, list[dict]] = {}
    for group in ordered_groups:
        chapter_groups_map.setdefault(group["chapter"], []).append(group)
    chapter_stage_count = Counter(int(stage["stage"].split("-")[0]) for stage in stages)
    chapter_levels: dict[int, list[int]] = {}
    for stage in stages:
        if stage["tatari_level"] is not None:
            chapter_levels.setdefault(int(stage["stage"].split("-")[0]), []).append(stage["tatari_level"])
    chapter_stats = {}
    for chapter in CHAPTERS:
        number = chapter["chapter"]
        group_list = chapter_groups_map.get(number, [])
        levels = chapter_levels.get(number, [])
        chapter_stats[number] = {
            "cards": len(group_list),
            "stages": chapter_stage_count.get(number, 0),
            "level_min": min(levels) if levels else None,
            "level_max": max(levels) if levels else None,
        }

    template = (ROOT / "page-template.html").read_text()
    site = ROOT / "site"
    # Chapter pages are static (crawlable without JS); each chapter's sprites are separate
    # files so visitors download only what a chapter's cards reference.
    shutil.rmtree(site / "chapters", ignore_errors=True)
    for generated in ("sprites", "chapter", "vi", "og"):
        shutil.rmtree(site / generated, ignore_errors=True)
    (site / "sprites").mkdir(parents=True)
    (site / "chapter").mkdir(parents=True)
    (site / "vi" / "chapter").mkdir(parents=True)
    (site / "og").mkdir(parents=True)
    for sprite_id, path in sprites.items():
        shutil.copyfile(path, site / "sprites" / f"{sprite_id}.png")

    total_chapters = len(CHAPTERS)
    total_cards = len(groups)
    total_stages = len(stages)
    render_og_image(site / "og" / "home.png", "Critter Formations", "Clash of Critters Formations",
                     f"{total_chapters} chapters · {total_cards} cards · {total_stages} stages")
    for chapter in CHAPTERS:
        number = chapter["chapter"]
        stats = chapter_stats[number]
        caption = (f"{stats['cards']} cards · {stats['stages']} stages" if stats["cards"]
                   else "No formations yet")
        render_og_image(site / "og" / f"chapter-{number}.png", f"Chapter {number}",
                         "Clash of Critters Formations", caption)

    for lang in LANGS:
        strings = STRINGS[lang]
        main_content = render_home_main(lang, chapter_stats)
        page = render_shell(
            template, lang, "home",
            title=strings["home_title"], description=strings["home_description"],
            canonical_path=page_path(lang, "home"), h1=strings["home_h1"], main_content=main_content,
            og_image_path="og/home.png", og_image_alt=strings["og_alt_home"],
            jsonld_scripts=[website_jsonld(lang)],
        )
        home_file = site / "index.html" if lang == "en" else site / "vi" / "index.html"
        home_file.write_text(page)

    for chapter in CHAPTERS:
        number = chapter["chapter"]
        group_list = chapter_groups_map.get(number, [])
        stats = chapter_stats[number]
        for lang in LANGS:
            strings = STRINGS[lang]
            cards_html = [render_card(group, lang, index == 0) for index, group in enumerate(group_list)]
            main_content = render_chapter_main(lang, number, cards_html)
            title = strings["chapter_title"].format(n=number)
            if stats["cards"]:
                level_clause = (strings["chapter_level_clause"].format(lo=stats["level_min"], hi=stats["level_max"])
                                 if stats["level_min"] is not None else "")
                description = strings["chapter_description"].format(
                    n=number, cards=stats["cards"], stages=stats["stages"], level_clause=level_clause)
            else:
                description = strings["chapter_description_empty"].format(n=number)
            jsonld_scripts = [breadcrumb_jsonld(lang, number)]
            if group_list:
                jsonld_scripts.append(itemlist_jsonld(lang, number, group_list))
            page = render_shell(
                template, lang, "chapter", chapter=number,
                title=title, description=description, canonical_path=page_path(lang, "chapter", number),
                h1=strings["chapter_h1"].format(n=number), main_content=main_content,
                og_image_path=f"og/chapter-{number}.png", og_image_alt=strings["og_alt_chapter"].format(n=number),
                jsonld_scripts=jsonld_scripts, robots_noindex=not stats["cards"],
            )
            chapter_dir = ((site / "chapter" / str(number)) if lang == "en" else
                           (site / "vi" / "chapter" / str(number)))
            chapter_dir.mkdir(parents=True, exist_ok=True)
            (chapter_dir / "index.html").write_text(page)

    for lang in LANGS:
        strings = STRINGS[lang]
        main_content = render_privacy_main(lang)
        page = render_shell(
            template, lang, "privacy",
            title=strings["privacy_title"], description=strings["privacy_description"],
            canonical_path=page_path(lang, "privacy"), h1=strings["privacy_h1"], main_content=main_content,
            og_image_path="og/home.png", og_image_alt=strings["og_alt_home"], jsonld_scripts=[],
        )
        privacy_file = site / "privacy.html" if lang == "en" else site / "vi" / "privacy.html"
        privacy_file.write_text(page)

    collected_at = dataset["collected_at"]

    def hreflang_sitemap_links(page_type: str, chapter_number: int | None) -> str:
        links = [f'\n    <xhtml:link rel="alternate" hreflang="{lang}" '
                 f'href="{SITE_URL + page_path(lang, page_type, chapter_number)}"/>' for lang in LANGS]
        links.append(f'\n    <xhtml:link rel="alternate" hreflang="x-default" '
                     f'href="{SITE_URL + page_path("en", page_type, chapter_number)}"/>')
        return "".join(links)

    def sitemap_entry(lang: str, page_type: str, chapter_number: int | None = None) -> str:
        loc = SITE_URL + page_path(lang, page_type, chapter_number)
        return (f'  <url>\n    <loc>{loc}</loc>\n    <lastmod>{collected_at}</lastmod>'
                f'{hreflang_sitemap_links(page_type, chapter_number)}\n  </url>')

    sitemap_urls = [sitemap_entry(lang, "home") for lang in LANGS]
    sitemap_urls += [sitemap_entry(lang, "chapter", chapter["chapter"])
                     for chapter in CHAPTERS if chapter_stats[chapter["chapter"]]["cards"]
                     for lang in LANGS]
    sitemap_urls += [sitemap_entry(lang, "privacy") for lang in LANGS]
    sitemap_xml = ('<?xml version="1.0" encoding="UTF-8"?>\n'
                   '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
                   'xmlns:xhtml="http://www.w3.org/1999/xhtml">\n' + "\n".join(sitemap_urls) + "\n</urlset>\n")
    (site / "sitemap.xml").write_text(sitemap_xml)
    (site / "robots.txt").write_text(
        "User-agent: *\nAllow: /\nDisallow: /chapters/\nSitemap: " + SITE_URL + "/sitemap.xml\n")

    print(f"Built {len(stages)} stages in {len(groups)} grouped formation cards; {len(sprites)} exact sprite variants. Site: {site}")


if __name__ == "__main__":
    build()
