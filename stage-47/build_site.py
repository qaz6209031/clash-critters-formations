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
from zoneinfo import ZoneInfo
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
SITE_URL = "https://critterformations.com"
LANGS = ("en", "zh-hant", "ko", "vi")
# Per-language URL prefix, HTML/hreflang codes, Open Graph and JSON-LD locales, and the
# native name shown in the language switcher (always in that language's own script).
LANG_INFO = {
    "en": {"prefix": "", "code": "en", "og_locale": "en_US", "jsonld": "en-US", "native": "EN"},
    "zh-hant": {"prefix": "/zh-hant", "code": "zh-Hant", "og_locale": "zh_TW", "jsonld": "zh-Hant", "native": "繁體中文"},
    "ko": {"prefix": "/ko", "code": "ko", "og_locale": "ko_KR", "jsonld": "ko-KR", "native": "한국어"},
    "vi": {"prefix": "/vi", "code": "vi", "og_locale": "vi_VN", "jsonld": "vi-VN", "native": "Tiếng Việt"},
}
# After August 27 in the owner's America/Los_Angeles time zone (PDT).
PUBLICATION_CUTOFF = datetime(2026, 8, 28, 7, tzinfo=timezone.utc)
# The October 21 update changed enemy formations in these chapters.
# The owner requires references posted after October 21 in Los Angeles.
CHAPTER_PUBLICATION_CUTOFFS = {
    chapter: datetime(2026, 10, 22, 7, tzinfo=timezone.utc)
    for chapter in range(23, 29)
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
        "site_title": "Critter Formations",
        "chapter_label": "Chapter",
        "chapter_option_label": "Chapter {n}",
        "home_title": "Clash of Critters Formations by Chapter | Critter Formations",
        "home_description": "Browse Clash of Critters Main Stage formations by chapter, with Tatari levels and links to the original player posts.",
        "home_h1": "Clash of Critters Formations",
        "home_chapters_heading": "Chapters",
        "chapter_count": "{cards} cards · {stages} stages",
        "chapter_count_empty": "No formations yet",
        "chapter_title": "Clash of Critters Chapter {n} Formations (Stages {n}-1–{n}-80) | Critter Formations",
        "chapter_description": "{cards} verified formation cards covering {stages} stages in Chapter {n} (stages {n}-1–{n}-80){level_clause}, with Tatari levels and links to the original Discord posts.",
        "chapter_level_clause": ", observed Tatari levels {lo}–{hi}",
        "chapter_description_empty": "No verified formations are available yet for Chapter {n} (stages {n}-1–{n}-80).",
        "chapter_h1": "Chapter {n} Formations",
        "empty_chapter_message": "No verified formations available for this chapter yet.",
        "next_stage_button": "Next: Stage {n}-1",
        "next_stage_aria": "Go to Chapter {n}, starting at stage {n}-1",
        "donation_label": "Finding these formations helpful?",
        "donation_desktop": "Buy me a coffee",
        "donation_mobile": "Donate",
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
             "<p>Critter Formations is a static website with no accounts and no server-side code of its own. "
             "This page explains what limited data is collected when you visit or send feedback.</p>"),
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
            ("Feedback (Supabase)",
             '<p>The feedback form sends your star rating, message, optional email address, the page you were on '
             'and the site language to a database hosted by <a href="https://supabase.com/privacy" target="_blank" '
             'rel="noopener noreferrer">Supabase</a>. Feedback is only used to improve this site; it is never '
             'published or sold. Leave the email field empty if you don’t need a reply.</p>'
             "<p>The “Can’t pass this stage?” button on each formation sends the formation, the stage if you pick "
             "one, the page and the site language to the same database. Reports are only used to find formations "
             "that need rechecking.</p>"),
            ("No accounts, no data sold",
             "<p>This site does not require an account and does not sell data. Apart from feedback you choose to "
             "send, it does not store any personal data.</p>"),
            ("Contact",
             '<p>Questions about this policy can be filed as a '
             '<a href="https://github.com/qaz6209031/clash-critters-formations/issues" target="_blank" rel="noopener noreferrer">'
             'GitHub issue</a>.</p>'),
            ("Effective date", "<p>November 4, 2026.</p>"),
        ],
    },
    "zh-hant": {
        "site_title": "Critter Formations",
        "chapter_label": "章節",
        "chapter_option_label": "第 {n} 章",
        "home_title": "塔塔冒險隊 各章節陣容攻略 | Critter Formations",
        "home_description": "依章節瀏覽塔塔冒險隊（Clash of Critters）主線關卡陣容，附 Tatari 等級與玩家原始貼文連結。",
        "home_h1": "塔塔冒險隊 陣容",
        "home_chapters_heading": "章節",
        "chapter_count": "{cards} 張卡片 · {stages} 關",
        "chapter_count_empty": "尚無陣容",
        "chapter_title": "塔塔冒險隊 第 {n} 章陣容（關卡 {n}-1–{n}-80）| Critter Formations",
        "chapter_description": "第 {n} 章（關卡 {n}-1–{n}-80）共 {cards} 張已驗證的陣容卡片，涵蓋 {stages} 個關卡{level_clause}，附 Tatari 等級與 Discord 原始貼文連結。",
        "chapter_level_clause": "，觀察到的 Tatari 等級 {lo}–{hi}",
        "chapter_description_empty": "第 {n} 章（關卡 {n}-1–{n}-80）目前尚無已驗證的陣容。",
        "chapter_h1": "第 {n} 章陣容",
        "empty_chapter_message": "這個章節目前尚無已驗證的陣容。",
        "next_stage_button": "下一關：{n}-1",
        "next_stage_aria": "前往第 {n} 章，從關卡 {n}-1 開始",
        "donation_label": "覺得這些陣容有幫助嗎？",
        "donation_desktop": "請我喝杯咖啡",
        "donation_mobile": "贊助",
        "donation_aria": "透過 PayPal 請我喝杯咖啡（在新分頁開啟）",
        "posted_by": "發布者",
        "discord_link_title": "開啟 Discord 原始貼文",
        "row_col": "第 {row} 列，第 {column} 欄",
        "empty_cell": "空格 · 第 {row} 列，第 {column} 欄",
        "board_aria": "關卡 {stage}：5×5 陣容，最上排為前排",
        "footer_unofficial": "非官方粉絲自製內容，與 Farlight 無關，亦未獲 Farlight 認可。",
        "footer_trademark": "Clash of Critters（塔塔冒險隊）為其各自所有者的商標。",
        "footer_privacy_label": "隱私權政策",
        "breadcrumb_home": "首頁",
        "og_alt_home": "Critter Formations：依章節整理的塔塔冒險隊陣容",
        "og_alt_chapter": "塔塔冒險隊第 {n} 章陣容預覽",
        "privacy_title": "隱私權政策 | Critter Formations",
        "privacy_description": "Critter Formations 如何處理訪客資料：GitHub Pages 託管、Google Analytics 4 與 PayPal 贊助。",
        "privacy_h1": "隱私權政策",
        "privacy_sections": [
            ("概述",
             "<p>Critter Formations 是一個靜態網站，沒有帳號，也沒有自己的伺服器端程式。"
             "本頁說明您造訪網站或送出意見回饋時，會收集哪些有限的資料。</p>"),
            ("託管（GitHub Pages）",
             '<p>本網站託管於 GitHub Pages。GitHub 可能基於安全目的記錄訪客的 IP 位址與請求資料。請參閱 GitHub 的'
             '<a href="https://docs.github.com/en/site-policy/privacy-policies/github-general-privacy-statement" '
             'target="_blank" rel="noopener noreferrer">一般隱私權聲明</a>。</p>'),
            ("分析（Google Analytics 4）",
             '<p>本網站使用 Google Analytics 4 了解流量並改善內容。GA4 會設定 <code>_ga</code> 等 Cookie，'
             '並收集使用資料，包括瀏覽的頁面、大致位置及裝置／瀏覽器資訊。請參閱 Google 的'
             '<a href="https://policies.google.com/technologies/partner-sites" target="_blank" rel="noopener noreferrer">'
             '合作夥伴網站政策</a>。您可以使用 <a href="https://tools.google.com/dlpage/gaoptout" target="_blank" '
             'rel="noopener noreferrer">Google Analytics 停用瀏覽器外掛程式</a>選擇退出。</p>'),
            ("贊助（PayPal）",
             '<p>贊助按鈕會連到 PayPal，由 PayPal 依其'
             '<a href="https://www.paypal.com/myaccount/privacy/privacyStatementFull" target="_blank" rel="noopener noreferrer">'
             '隱私權政策</a>處理付款。本網站不會看到您的信用卡或付款資訊。</p>'),
            ("Discord 連結",
             "<p>卡片標題與發布者名稱會連到作為資料來源的 Discord 原始貼文。造訪這些連結時，"
             "適用 Discord 自己的隱私權規範。</p>"),
            ("意見回饋（Supabase）",
             '<p>意見回饋表單會將您的星等評分、留言、選填的電子郵件、您所在的頁面與網站語言，傳送到由 '
             '<a href="https://supabase.com/privacy" target="_blank" rel="noopener noreferrer">Supabase</a> '
             '託管的資料庫。這些回饋只用於改善本網站，絕不會公開或販售。如果不需要回覆，請將電子郵件欄位留空。</p>'
             "<p>每個陣容下方的「打不過這關？」按鈕，會把陣容、您選擇的關卡（若有選），連同所在頁面與網站語言，"
             "傳送到同一個資料庫。這些回報只用來找出需要重新檢查的陣容。</p>"),
            ("無帳號、不販售資料",
             "<p>本網站不需要帳號，也不販售資料。除了您主動送出的意見回饋之外，本網站不儲存任何個人資料。</p>"),
            ("聯絡方式",
             '<p>對本政策有任何疑問，歡迎提交 '
             '<a href="https://github.com/qaz6209031/clash-critters-formations/issues" target="_blank" rel="noopener noreferrer">'
             'GitHub issue</a>。</p>'),
            ("生效日期", "<p>2026 年 11 月 4 日。</p>"),
        ],
    },
    "ko": {
        "site_title": "Critter Formations",
        "chapter_label": "챕터",
        "chapter_option_label": "챕터 {n}",
        "home_title": "뚜까펫: 서바이벌 챕터별 진형 공략 | Critter Formations",
        "home_description": "뚜까펫: 서바이벌(Clash of Critters) 메인 스테이지 진형을 챕터별로 확인하세요. Tatari 레벨과 원본 플레이어 게시물 링크를 함께 제공합니다.",
        "home_h1": "뚜까펫: 서바이벌 진형",
        "home_chapters_heading": "챕터",
        "chapter_count": "카드 {cards}개 · 스테이지 {stages}개",
        "chapter_count_empty": "아직 진형 없음",
        "chapter_title": "뚜까펫: 서바이벌 챕터 {n} 진형 (스테이지 {n}-1–{n}-80) | Critter Formations",
        "chapter_description": "챕터 {n}(스테이지 {n}-1–{n}-80)의 스테이지 {stages}개를 다루는 검증된 진형 카드 {cards}개{level_clause}. Tatari 레벨과 원본 Discord 게시물 링크를 함께 제공합니다.",
        "chapter_level_clause": ", 확인된 Tatari 레벨 {lo}–{hi}",
        "chapter_description_empty": "챕터 {n}(스테이지 {n}-1–{n}-80)에는 아직 검증된 진형이 없습니다.",
        "chapter_h1": "챕터 {n} 진형",
        "empty_chapter_message": "이 챕터에는 아직 검증된 진형이 없습니다.",
        "next_stage_button": "다음: 스테이지 {n}-1",
        "next_stage_aria": "챕터 {n}의 스테이지 {n}-1로 이동",
        "donation_label": "진형 정보가 도움이 되셨나요?",
        "donation_desktop": "커피 한 잔 후원하기",
        "donation_mobile": "후원",
        "donation_aria": "PayPal로 커피 한 잔 후원하기 (새 탭에서 열림)",
        "posted_by": "작성자",
        "discord_link_title": "원본 Discord 게시물 열기",
        "row_col": "{row}행 {column}열",
        "empty_cell": "빈 칸 · {row}행 {column}열",
        "board_aria": "스테이지 {stage}: 5×5 진형, 맨 윗줄이 전열",
        "footer_unofficial": "비공식 팬 제작물이며, Farlight와 제휴하거나 Farlight의 승인을 받지 않았습니다.",
        "footer_trademark": "Clash of Critters(뚜까펫: 서바이벌)는 해당 소유자의 상표입니다.",
        "footer_privacy_label": "개인정보 처리방침",
        "breadcrumb_home": "홈",
        "og_alt_home": "Critter Formations: 챕터별 뚜까펫: 서바이벌 진형",
        "og_alt_chapter": "뚜까펫: 서바이벌 챕터 {n} 진형 미리보기",
        "privacy_title": "개인정보 처리방침 | Critter Formations",
        "privacy_description": "Critter Formations의 방문자 데이터 처리 방식: GitHub Pages 호스팅, Google Analytics 4, PayPal 후원.",
        "privacy_h1": "개인정보 처리방침",
        "privacy_sections": [
            ("개요",
             "<p>Critter Formations는 계정과 자체 서버 측 코드가 없는 정적 웹사이트입니다. "
             "이 페이지는 사이트 방문 또는 피드백 전송 시 수집되는 제한적인 데이터에 대해 설명합니다.</p>"),
            ("호스팅 (GitHub Pages)",
             '<p>이 사이트는 GitHub Pages에서 호스팅됩니다. GitHub는 보안 목적으로 방문자의 IP 주소와 요청 데이터를 '
             '기록할 수 있습니다. GitHub의 <a href="https://docs.github.com/en/site-policy/privacy-policies/github-general-privacy-statement" '
             'target="_blank" rel="noopener noreferrer">일반 개인정보 보호정책</a>을 참고하세요.</p>'),
            ("분석 (Google Analytics 4)",
             '<p>이 사이트는 트래픽을 파악하고 콘텐츠를 개선하기 위해 Google Analytics 4를 사용합니다. GA4는 '
             '<code>_ga</code> 등의 쿠키를 설정하고, 조회한 페이지, 대략적인 위치, 기기/브라우저 정보 등의 사용 데이터를 '
             '수집합니다. Google의 <a href="https://policies.google.com/technologies/partner-sites" target="_blank" '
             'rel="noopener noreferrer">파트너 사이트 정책</a>을 참고하세요. '
             '<a href="https://tools.google.com/dlpage/gaoptout" target="_blank" rel="noopener noreferrer">Google 애널리틱스 '
             '차단 브라우저 부가기능</a>으로 수집을 거부할 수 있습니다.</p>'),
            ("후원 (PayPal)",
             '<p>후원 버튼은 PayPal로 연결되며, 결제는 PayPal의 '
             '<a href="https://www.paypal.com/myaccount/privacy/privacyStatementFull" target="_blank" rel="noopener noreferrer">'
             '개인정보 보호정책</a>에 따라 처리됩니다. 이 사이트는 카드 정보나 결제 정보를 절대 볼 수 없습니다.</p>'),
            ("Discord 링크",
             "<p>카드 제목과 작성자 이름은 출처로 사용된 원본 Discord 게시물로 연결됩니다. 해당 링크 방문에는 "
             "Discord 자체의 개인정보 보호 정책이 적용됩니다.</p>"),
            ("피드백 (Supabase)",
             '<p>피드백 양식은 별점, 메시지, 선택 입력한 이메일 주소, 현재 페이지와 사이트 언어를 '
             '<a href="https://supabase.com/privacy" target="_blank" rel="noopener noreferrer">Supabase</a>에서 '
             '호스팅하는 데이터베이스로 전송합니다. 피드백은 사이트 개선에만 사용되며 공개되거나 판매되지 않습니다. '
             '답변이 필요 없다면 이메일 칸은 비워 두세요.</p>'
             "<p>각 진형 아래의 「이 스테이지를 못 깨셨나요?」 버튼은 진형과 선택한 스테이지(선택한 경우)를 "
             "현재 페이지 및 사이트 언어와 함께 같은 데이터베이스로 전송합니다. 이 제보는 다시 확인이 필요한 진형을 "
             "찾는 데에만 사용됩니다.</p>"),
            ("계정 없음, 데이터 판매 없음",
             "<p>이 사이트는 계정이 필요 없고 데이터를 판매하지 않습니다. 직접 보내 주신 피드백 외에는 어떠한 "
             "개인정보도 저장하지 않습니다.</p>"),
            ("문의",
             '<p>이 정책에 관한 문의는 '
             '<a href="https://github.com/qaz6209031/clash-critters-formations/issues" target="_blank" rel="noopener noreferrer">'
             'GitHub issue</a>로 남겨 주세요.</p>'),
            ("시행일", "<p>2026년 11월 4일.</p>"),
        ],
    },
    "vi": {
        "site_title": "Critter Formations",
        "chapter_label": "Chương",
        "chapter_option_label": "Chương {n}",
        "home_title": "Đội Hình Chiến Thú Hỗn Chiến Theo Chương | Critter Formations",
        "home_description": "Xem đội hình Main Stage của Chiến Thú Hỗn Chiến (Clash of Critters) theo từng chương, kèm cấp Tatari và liên kết đến bài đăng gốc của người chơi.",
        "home_h1": "Đội Hình Chiến Thú Hỗn Chiến",
        "home_chapters_heading": "Các chương",
        "chapter_count": "{cards} đội hình · {stages} màn",
        "chapter_count_empty": "Chưa có đội hình",
        "chapter_title": "Đội hình Chiến Thú Hỗn Chiến Chương {n} (Clash of Critters) | Critter Formations",
        "chapter_description": "{cards} đội hình đã được xác minh, bao phủ {stages} màn trong Chương {n} (màn {n}-1–{n}-80){level_clause}, kèm cấp Tatari và liên kết đến bài đăng Discord gốc.",
        "chapter_level_clause": ", cấp Tatari quan sát được {lo}–{hi}",
        "chapter_description_empty": "Chưa có đội hình nào được xác minh cho Chương {n} (màn {n}-1–{n}-80).",
        "chapter_h1": "Đội hình Chương {n}",
        "empty_chapter_message": "Chưa có đội hình nào được xác minh cho chương này.",
        "next_stage_button": "Tiếp theo: Màn {n}-1",
        "next_stage_aria": "Đi đến Chương {n}, bắt đầu từ màn {n}-1",
        "donation_label": "Thấy các đội hình này hữu ích?",
        "donation_desktop": "Mời tôi một ly cà phê",
        "donation_mobile": "Ủng hộ",
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
             "<p>Critter Formations là một trang web tĩnh, không có tài khoản và không có mã phía máy chủ riêng. "
             "Trang này giải thích dữ liệu hạn chế nào được thu thập khi bạn truy cập hoặc gửi góp ý.</p>"),
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
            ("Góp ý (Supabase)",
             '<p>Biểu mẫu góp ý gửi số sao đánh giá, nội dung, email (không bắt buộc), trang bạn đang xem và ngôn ngữ '
             'của trang đến cơ sở dữ liệu do <a href="https://supabase.com/privacy" target="_blank" '
             'rel="noopener noreferrer">Supabase</a> lưu trữ. Góp ý chỉ được dùng để cải thiện trang này, không bao '
             'giờ được công khai hay bán. Hãy để trống ô email nếu bạn không cần phản hồi.</p>'
             "<p>Nút “Không qua được màn này?” dưới mỗi đội hình gửi đội hình, màn chơi bạn chọn (nếu có), "
             "cùng trang đang xem và ngôn ngữ, đến cùng cơ sở dữ liệu đó. Các báo cáo "
             "chỉ được dùng để tìm đội hình cần kiểm tra lại.</p>"),
            ("Không tài khoản, không bán dữ liệu",
             "<p>Trang này không yêu cầu tài khoản và không bán dữ liệu. Ngoài góp ý do bạn tự gửi, trang không lưu "
             "trữ bất kỳ dữ liệu cá nhân nào.</p>"),
            ("Liên hệ",
             '<p>Thắc mắc về chính sách này có thể gửi qua '
             '<a href="https://github.com/qaz6209031/clash-critters-formations/issues" target="_blank" rel="noopener noreferrer">'
             'GitHub issue</a>.</p>'),
            ("Ngày có hiệu lực", "<p>4 tháng 11, 2026.</p>"),
        ],
    },
}


# Feedback form copy, merged into STRINGS below. Error keys match the codes returned by
# the critter-feedback Edge Function (supabase/functions/critter-feedback/index.ts).
FEEDBACK_ENDPOINT = "https://njzrhztlmvhcpjglnuut.supabase.co/functions/v1/critter-feedback"
FEEDBACK_STRINGS = {
    "en": {
        "lang_label": "Language",
        "feedback_heading": "Share your feedback",
        "feedback_intro": "Spotted a wrong or outdated formation, or have an idea for the site? Let me know.",
        "feedback_rating_question": "How helpful is this site?",
        "feedback_optional": "(optional)",
        "feedback_rating_labels": ["Not helpful", "Slightly helpful", "Helpful", "Very helpful", "Extremely helpful"],
        "feedback_star_one": "{n} star",
        "feedback_star_many": "{n} stars",
        "feedback_message_label": "Message",
        "feedback_message_placeholder": "e.g. The 50-12 formation no longer works after the update",
        "feedback_email_label": "Email",
        "feedback_email_hint": "(optional, only if you'd like a reply)",
        "feedback_send": "Send feedback",
        "feedback_sending": "Sending…",
        "feedback_thanks_heading": "Thanks for your feedback!",
        "feedback_thanks_text": "I read every message.",
        "feedback_send_more": "Send more feedback",
        "feedback_errors": {
            "empty": "Please add a rating or a message.",
            "invalid_email": "Please enter a valid email address.",
            "invalid_rating": "Rating must be between 1 and 5 stars.",
            "message_too_long": "Message must be 2,000 characters or fewer.",
            "rate_limited": "Too many submissions. Please wait a minute and try again.",
            "server": "Could not send feedback. Please try again later.",
        },
    },
    "zh-hant": {
        "lang_label": "語言",
        "feedback_heading": "意見回饋",
        "feedback_intro": "發現陣容有錯或已過時，或對網站有任何建議嗎？歡迎告訴我。",
        "feedback_rating_question": "這個網站對你有幫助嗎？",
        "feedback_optional": "（選填）",
        "feedback_rating_labels": ["沒有幫助", "有一點幫助", "有幫助", "很有幫助", "非常有幫助"],
        "feedback_star_one": "{n} 顆星",
        "feedback_star_many": "{n} 顆星",
        "feedback_message_label": "留言",
        "feedback_message_placeholder": "例如：50-12 的陣容在更新後已經打不過了",
        "feedback_email_label": "電子郵件",
        "feedback_email_hint": "（選填，需要回覆時再填）",
        "feedback_send": "送出回饋",
        "feedback_sending": "傳送中…",
        "feedback_thanks_heading": "感謝你的回饋！",
        "feedback_thanks_text": "每一則留言我都會看。",
        "feedback_send_more": "再送一則回饋",
        "feedback_errors": {
            "empty": "請給個評分或留下訊息。",
            "invalid_email": "請輸入有效的電子郵件地址。",
            "invalid_rating": "評分必須介於 1 到 5 顆星。",
            "message_too_long": "留言不能超過 2,000 個字元。",
            "rate_limited": "送出次數太多了，請稍等一分鐘再試。",
            "server": "無法送出回饋，請稍後再試。",
        },
    },
    "ko": {
        "lang_label": "언어",
        "feedback_heading": "피드백 보내기",
        "feedback_intro": "잘못되었거나 오래된 진형을 발견했거나 사이트에 대한 아이디어가 있으신가요? 알려 주세요.",
        "feedback_rating_question": "이 사이트가 얼마나 도움이 되었나요?",
        "feedback_optional": "(선택)",
        "feedback_rating_labels": ["도움 안 됨", "조금 도움 됨", "도움 됨", "많이 도움 됨", "매우 도움 됨"],
        "feedback_star_one": "별 {n}개",
        "feedback_star_many": "별 {n}개",
        "feedback_message_label": "메시지",
        "feedback_message_placeholder": "예: 업데이트 후 50-12 진형이 더 이상 통하지 않아요",
        "feedback_email_label": "이메일",
        "feedback_email_hint": "(선택, 답변을 원하실 때만)",
        "feedback_send": "피드백 보내기",
        "feedback_sending": "보내는 중…",
        "feedback_thanks_heading": "피드백 감사합니다!",
        "feedback_thanks_text": "보내 주신 메시지는 모두 읽고 있어요.",
        "feedback_send_more": "피드백 더 보내기",
        "feedback_errors": {
            "empty": "별점이나 메시지를 남겨 주세요.",
            "invalid_email": "올바른 이메일 주소를 입력해 주세요.",
            "invalid_rating": "별점은 1~5개 사이여야 합니다.",
            "message_too_long": "메시지는 2,000자 이하로 입력해 주세요.",
            "rate_limited": "너무 많이 보내셨어요. 1분 후에 다시 시도해 주세요.",
            "server": "피드백을 보내지 못했습니다. 잠시 후 다시 시도해 주세요.",
        },
    },
    "vi": {
        "lang_label": "Ngôn ngữ",
        "feedback_heading": "Gửi góp ý",
        "feedback_intro": "Bạn thấy đội hình nào sai hoặc đã lỗi thời, hay có ý tưởng cho trang web? Hãy cho mình biết.",
        "feedback_rating_question": "Trang web này hữu ích với bạn đến đâu?",
        "feedback_optional": "(không bắt buộc)",
        "feedback_rating_labels": ["Không hữu ích", "Hơi hữu ích", "Hữu ích", "Rất hữu ích", "Cực kỳ hữu ích"],
        "feedback_star_one": "{n} sao",
        "feedback_star_many": "{n} sao",
        "feedback_message_label": "Nội dung",
        "feedback_message_placeholder": "Ví dụ: Đội hình 50-12 không còn dùng được sau bản cập nhật",
        "feedback_email_label": "Email",
        "feedback_email_hint": "(không bắt buộc, chỉ khi bạn muốn được phản hồi)",
        "feedback_send": "Gửi góp ý",
        "feedback_sending": "Đang gửi…",
        "feedback_thanks_heading": "Cảm ơn góp ý của bạn!",
        "feedback_thanks_text": "Mình đọc mọi tin nhắn.",
        "feedback_send_more": "Gửi thêm góp ý",
        "feedback_errors": {
            "empty": "Vui lòng chọn số sao hoặc nhập nội dung.",
            "invalid_email": "Vui lòng nhập địa chỉ email hợp lệ.",
            "invalid_rating": "Số sao phải từ 1 đến 5.",
            "message_too_long": "Nội dung không được vượt quá 2.000 ký tự.",
            "rate_limited": "Bạn gửi quá nhiều lần. Vui lòng đợi một phút rồi thử lại.",
            "server": "Không gửi được góp ý. Vui lòng thử lại sau.",
        },
    },
}
for _lang, _extra in FEEDBACK_STRINGS.items():
    STRINGS[_lang].update(_extra)

# "Can't pass this stage?" report copy, merged into STRINGS. Reports go to the same
# critter-feedback Edge Function with kind "stage_report"; error keys match its codes.
REPORT_STRINGS = {
    "en": {
        "report_button": "Can’t pass this stage?",
        "report_done": "Reported",
        "report_stage_label": "Which stage?",
        "report_stage_choose": "Not sure",
        "report_submit": "Report",
        "report_cancel": "Cancel",
        "report_thanks": "Thanks! This formation will be rechecked.",
    },
    "zh-hant": {
        "report_button": "打不過這關？",
        "report_done": "已回報",
        "report_stage_label": "哪一關？",
        "report_stage_choose": "不確定",
        "report_submit": "回報",
        "report_cancel": "取消",
        "report_thanks": "謝謝！我會重新檢查這個陣容。",
    },
    "ko": {
        "report_button": "이 스테이지를 못 깨셨나요?",
        "report_done": "제보 완료",
        "report_stage_label": "어느 스테이지인가요?",
        "report_stage_choose": "잘 모르겠어요",
        "report_submit": "제보하기",
        "report_cancel": "취소",
        "report_thanks": "감사합니다! 이 진형을 다시 확인할게요.",
    },
    "vi": {
        "report_button": "Không qua được màn này?",
        "report_done": "Đã báo cáo",
        "report_stage_label": "Màn nào?",
        "report_stage_choose": "Không rõ",
        "report_submit": "Báo cáo",
        "report_cancel": "Hủy",
        "report_thanks": "Cảm ơn bạn! Đội hình này sẽ được kiểm tra lại.",
    },
}
for _lang, _extra in REPORT_STRINGS.items():
    STRINGS[_lang].update(_extra)

# Posted date shown under the level on each card. Dates use the same
# America/Los_Angeles day as the publication cutoffs.
POSTED_DATE_STRINGS = {
    "en": {"posted_on": "Posted {date}"},
    "zh-hant": {"posted_on": "發布於 {date}"},
    "ko": {"posted_on": "{date} 게시"},
    "vi": {"posted_on": "Đăng ngày {date}"},
}
for _lang, _extra in POSTED_DATE_STRINGS.items():
    STRINGS[_lang].update(_extra)

# Badge Dojo: five element dojos, floors 1–7, ten stages per floor, and a 4-row by
# 3-column player grid (row 1 is the front, nearest the enemy).
DOJO_ELEMENTS = ("water", "fire", "grass", "rock", "lightning")
DOJO_FLOORS = range(1, 8)
DOJO_ROWS, DOJO_COLUMNS = 4, 3
DOJO_FILE = ROOT.parent / "dojo" / "reviewed-dojo-formations.json"
DOJO_REVIEWED = json.loads(DOJO_FILE.read_text())
DOJO_STRINGS = {
    "en": {
        "dojo_nav": "Dojo",
        "dojo_heading": "Badge Dojo",
        "dojo_element_names": {"water": "Water", "fire": "Fire", "grass": "Grass", "rock": "Rock", "lightning": "Lightning"},
        "dojo_element_title": "{element} Dojo",
        "dojo_floor_heading": "{element} Dojo {n}",
        "dojo_floor_link": "Dojo {n}",
        "dojo_count": "{cards} cards · {stages} stages",
        "dojo_index_title": "Clash of Critters Badge Dojo Formations | Critter Formations",
        "dojo_index_description": "Water, Fire, Grass, Rock and Lightning Dojo formations for Clash of Critters, Dojo 1–7, with links to the original player posts.",
        "dojo_index_h1": "Badge Dojo Formations",
        "dojo_title": "Clash of Critters {element} Dojo Formations (1-1–7-10) | Critter Formations",
        "dojo_description": "{cards} formation cards covering {stages} {element} Dojo stages (1-1–7-10) in Clash of Critters, with links to the original Discord posts.",
        "dojo_h1": "{element} Dojo Formations",
        "dojo_board_aria": "{element} Dojo {stage}: 3 by 4 formation, top row is the front",
        "og_alt_dojo": "{element} Dojo Clash of Critters formations preview",
    },
    "zh-hant": {
        "dojo_nav": "道場",
        "dojo_heading": "徽章道場",
        "dojo_element_names": {"water": "水", "fire": "火", "grass": "草", "rock": "岩", "lightning": "雷"},
        "dojo_element_title": "{element}道場",
        "dojo_floor_heading": "{element}道場 {n}",
        "dojo_floor_link": "道場 {n}",
        "dojo_count": "{cards} 張卡片 · {stages} 關",
        "dojo_index_title": "塔塔冒險隊 徽章道場陣容 | Critter Formations",
        "dojo_index_description": "塔塔冒險隊（Clash of Critters）水、火、草、岩、雷道場 1–7 的陣容，附玩家原始貼文連結。",
        "dojo_index_h1": "徽章道場陣容",
        "dojo_title": "塔塔冒險隊 {element}道場陣容（1-1–7-10）| Critter Formations",
        "dojo_description": "{element}道場（1-1–7-10）共 {cards} 張陣容卡片，涵蓋 {stages} 個關卡，附 Discord 原始貼文連結。",
        "dojo_h1": "{element}道場陣容",
        "dojo_board_aria": "{element}道場 {stage}：3×4 陣容，最上排為前排",
        "og_alt_dojo": "塔塔冒險隊 {element}道場陣容預覽",
    },
    "ko": {
        "dojo_nav": "도장",
        "dojo_heading": "배지 도장",
        "dojo_element_names": {"water": "물", "fire": "불", "grass": "풀", "rock": "바위", "lightning": "번개"},
        "dojo_element_title": "{element} 도장",
        "dojo_floor_heading": "{element} 도장 {n}",
        "dojo_floor_link": "도장 {n}",
        "dojo_count": "카드 {cards}개 · {stages}개 스테이지",
        "dojo_index_title": "Clash of Critters 배지 도장 편성 | Critter Formations",
        "dojo_index_description": "Clash of Critters 물·불·풀·바위·번개 도장 1–7 편성과 원본 플레이어 게시물 링크.",
        "dojo_index_h1": "배지 도장 편성",
        "dojo_title": "Clash of Critters {element} 도장 편성 (1-1–7-10) | Critter Formations",
        "dojo_description": "{element} 도장(1-1–7-10) {stages}개 스테이지를 다루는 편성 카드 {cards}개와 원본 Discord 게시물 링크.",
        "dojo_h1": "{element} 도장 편성",
        "dojo_board_aria": "{element} 도장 {stage}: 3×4 편성, 맨 위 줄이 전열",
        "og_alt_dojo": "Clash of Critters {element} 도장 편성 미리보기",
    },
    "vi": {
        "dojo_nav": "Võ đường",
        "dojo_heading": "Võ đường huy hiệu",
        "dojo_element_names": {"water": "Nước", "fire": "Lửa", "grass": "Cỏ", "rock": "Đá", "lightning": "Sét"},
        "dojo_element_title": "Võ đường {element}",
        "dojo_floor_heading": "Võ đường {element} {n}",
        "dojo_floor_link": "Võ đường {n}",
        "dojo_count": "{cards} thẻ · {stages} màn",
        "dojo_index_title": "Đội hình Võ đường huy hiệu Clash of Critters | Critter Formations",
        "dojo_index_description": "Đội hình Võ đường Nước, Lửa, Cỏ, Đá và Sét 1–7 trong Clash of Critters, kèm liên kết bài đăng gốc của người chơi.",
        "dojo_index_h1": "Đội hình Võ đường huy hiệu",
        "dojo_title": "Đội hình Võ đường {element} Clash of Critters (1-1–7-10) | Critter Formations",
        "dojo_description": "{cards} thẻ đội hình cho {stages} màn Võ đường {element} (1-1–7-10) trong Clash of Critters, kèm liên kết bài đăng Discord gốc.",
        "dojo_h1": "Đội hình Võ đường {element}",
        "dojo_board_aria": "Võ đường {element} {stage}: đội hình 3×4, hàng trên cùng là hàng đầu",
        "og_alt_dojo": "Xem trước đội hình Võ đường {element} Clash of Critters",
    },
}
for _lang, _extra in DOJO_STRINGS.items():
    STRINGS[_lang].update(_extra)

POSTED_DATE_ZONE = ZoneInfo("America/Los_Angeles")
MONTH_ABBR = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def format_posted_date(timestamp: str, lang: str) -> str:
    local = datetime.fromisoformat(timestamp.replace("Z", "+00:00")).astimezone(POSTED_DATE_ZONE)
    if lang == "zh-hant":
        return f"{local.year}/{local.month}/{local.day}"
    if lang == "ko":
        return f"{local.year}. {local.month}. {local.day}."
    if lang == "vi":
        return f"{local.day}/{local.month}/{local.year}"
    return f"{MONTH_ABBR[local.month - 1]} {local.day}, {local.year}"


def lang_prefix(lang: str) -> str:
    return LANG_INFO[lang]["prefix"]


def lang_dir(site: Path, lang: str) -> Path:
    prefix = lang_prefix(lang)
    return site / prefix.lstrip("/") if prefix else site


def page_path(lang: str, page_type: str, chapter: int | None = None) -> str:
    prefix = lang_prefix(lang)
    if page_type == "home":
        return f"{prefix}/" if prefix else "/"
    if page_type == "chapter":
        return f"{prefix}/chapter/{chapter}/"
    if page_type == "privacy":
        return f"{prefix}/privacy.html"
    if page_type == "dojo_index":
        return f"{prefix}/dojo/"
    if page_type == "dojo":
        # For dojo pages the "chapter" argument carries the element slug.
        return f"{prefix}/dojo/{chapter}/"
    raise ValueError(page_type)


def hreflang_links(page_type: str, chapter: int | None = None) -> str:
    links = [f'<link rel="alternate" hreflang="{LANG_INFO[lang]["code"]}" href="{SITE_URL + page_path(lang, page_type, chapter)}">'
             for lang in LANGS]
    links.append(f'<link rel="alternate" hreflang="x-default" href="{SITE_URL + page_path("en", page_type, chapter)}">')
    return "\n  ".join(links)


def og_meta(lang: str, page_type: str, title: str, description: str, image_path: str, image_alt: str,
            chapter: int | None = None) -> str:
    url = SITE_URL + page_path(lang, page_type, chapter)
    image_url = f"{SITE_URL}/{image_path}"
    alternates = [f'<meta property="og:locale:alternate" content="{LANG_INFO[other]["og_locale"]}">'
                  for other in LANGS if other != lang]
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
        f'<meta property="og:locale" content="{LANG_INFO[lang]["og_locale"]}">',
        *alternates,
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
        "inLanguage": LANG_INFO[lang]["jsonld"],
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
    lang_options = "".join(
        f'<option value="{page_path(l, page_type, chapter)}" data-lang="{l}" lang="{LANG_INFO[l]["code"]}"'
        + (' selected' if l == lang else '')
        + f'>{html.escape(LANG_INFO[l]["native"])}</option>'
        for l in LANGS)
    show_feedback = page_type in ("home", "chapter", "dojo_index", "dojo")
    is_dojo = page_type in ("dojo_index", "dojo")
    footer_lang_links = "\n      ".join(
        f'<a href="{page_path(l, page_type, chapter)}" hreflang="{LANG_INFO[l]["code"]}" lang="{LANG_INFO[l]["code"]}">'
        f'{html.escape(LANG_INFO[l]["native"])}</a>'
        for l in LANGS if l != lang)
    mapping = {
        "HTML_LANG": LANG_INFO[lang]["code"],
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
        "LANG_LABEL_TEXT": html.escape(S["lang_label"]),
        "LANG_OPTIONS": lang_options,
        "CHAPTER_LABEL_TEXT": html.escape(S["chapter_label"]),
        "CHAPTER_OPTIONS": chapter_options(lang, chapter if page_type == "chapter" else None),
        "DOJO_NAV": (f'<a class="dojo-nav-link" href="{page_path(lang, "dojo_index")}"'
                     + (' aria-current="page"' if page_type == "dojo_index" else '')
                     + (' data-active="true"' if is_dojo else '')
                     + f'>{html.escape(S["dojo_nav"])}</a>'),
        "DONATION_LABEL_TEXT": html.escape(S["donation_label"]),
        "DONATION_ARIA_TEXT": html.escape(S["donation_aria"], quote=True),
        "DONATION_DESKTOP_TEXT": html.escape(S["donation_desktop"]),
        "DONATION_MOBILE_TEXT": html.escape(S["donation_mobile"]),
        "H1_ATTRIBUTES": ' class="sr-only"' if page_type in ("chapter", "home") else "",
        "H1_TEXT": html.escape(h1),
        "MAIN_CONTENT": main_content,
        "FEEDBACK_SECTION": render_feedback_section(lang) if show_feedback else "",
        "FOOTER_UNOFFICIAL_TEXT": html.escape(S["footer_unofficial"]),
        "FOOTER_TRADEMARK_TEXT": html.escape(S["footer_trademark"]),
        "FOOTER_PRIVACY_HREF": page_path(lang, "privacy"),
        "FOOTER_PRIVACY_LABEL_TEXT": html.escape(S["footer_privacy_label"]),
        "FOOTER_LANG_LINKS": footer_lang_links,
        "JS_CONFIG_JSON": json.dumps({
            "lang": lang,
            "langPrefix": lang_prefix(lang),
            "pageType": page_type,
            "chapter": chapter if page_type == "chapter" else None,
            "dojoElement": chapter if page_type == "dojo" else None,
            "feedback": {
                "endpoint": FEEDBACK_ENDPOINT,
                "ratingLabels": S["feedback_rating_labels"],
                "send": S["feedback_send"],
                "sending": S["feedback_sending"],
                "errors": S["feedback_errors"],
            } if show_feedback else None,
            "report": {
                "endpoint": FEEDBACK_ENDPOINT,
                "strings": {key: S[key] for key in REPORT_STRINGS["en"]},
                "errors": {key: S["feedback_errors"][key] for key in ("rate_limited", "server")},
                "optional": S["feedback_optional"],
            } if page_type == "chapter" else None,
        }, ensure_ascii=False).replace("</", "<\\/"),
    }
    page = template
    for key, value in mapping.items():
        token = f"<!-- {key} -->"
        assert token in page, f"Missing template marker {token}"
        page = page.replace(token, value)
    assert not _TEMPLATE_MARKER.search(page), "Unfilled template marker remains"
    return page


STAR_PATH = ("M11.48 3.499a.562.562 0 011.04 0l2.125 5.111a.563.563 0 00.475.345l5.518.442c.499.04.701.663.321.988"
             "l-4.204 3.602a.563.563 0 00-.182.557l1.285 5.385a.562.562 0 01-.84.61l-4.725-2.885a.563.563 0 00-.586 0"
             "L6.982 20.54a.562.562 0 01-.84-.61l1.285-5.386a.562.562 0 00-.182-.557l-4.204-3.602a.563.563 0 01.321-.988"
             "l5.518-.442a.563.563 0 00.475-.345L11.48 3.5z")


def render_feedback_section(lang: str) -> str:
    S = STRINGS[lang]
    e = html.escape
    stars = "".join(
        f'<button type="button" class="star" aria-pressed="false" '
        f'aria-label="{e((S["feedback_star_many"] if n > 1 else S["feedback_star_one"]).format(n=n), quote=True)}">'
        f'<svg aria-hidden="true" viewBox="0 0 24 24"><path d="{STAR_PATH}"/></svg></button>'
        for n in range(1, 6))
    optional = f'<span class="hint">{e(S["feedback_optional"])}</span>'
    return (
        '<section class="feedback" aria-labelledby="feedback-heading">'
        f'<h2 id="feedback-heading">{e(S["feedback_heading"])}</h2>'
        f'<p class="feedback-intro">{e(S["feedback_intro"])}</p>'
        '<form id="feedback-form" novalidate>'
        f'<fieldset class="feedback-field"><legend>{e(S["feedback_rating_question"])} {optional}</legend>'
        f'<div class="stars">{stars}<span class="star-label" aria-hidden="true"></span></div></fieldset>'
        f'<div class="feedback-field"><label for="feedback-message">{e(S["feedback_message_label"])} {optional}</label>'
        f'<textarea id="feedback-message" name="message" rows="4" maxlength="2000" '
        f'placeholder="{e(S["feedback_message_placeholder"], quote=True)}"></textarea></div>'
        f'<div class="feedback-field"><label for="feedback-email">{e(S["feedback_email_label"])} '
        f'<span class="hint">{e(S["feedback_email_hint"])}</span></label>'
        '<input id="feedback-email" name="email" type="email" maxlength="320" autocomplete="email" '
        'inputmode="email" placeholder="you@example.com"></div>'
        # Honeypot: hidden from people, catches bots that fill every field.
        '<input class="hp" type="text" name="website" tabindex="-1" autocomplete="off" aria-hidden="true">'
        '<p class="feedback-error" role="alert" hidden></p>'
        f'<button type="submit" class="feedback-submit">{e(S["feedback_send"])}</button>'
        '</form>'
        '<div class="feedback-thanks" id="feedback-thanks" role="status" hidden>'
        f'<p class="feedback-thanks-heading">{e(S["feedback_thanks_heading"])}</p>'
        f'<p>{e(S["feedback_thanks_text"])}</p>'
        f'<button type="button" class="feedback-again">{e(S["feedback_send_more"])}</button>'
        '</div></section>')


REPORT_FLAG_SVG = ('<svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
                   'stroke-linecap="round" stroke-linejoin="round"><path d="M5 21V4M5 4h11l-2 4 2 4H5"/></svg>')


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
    posted_date = format_posted_date(group["posted_at_min"], lang)
    posted_label = S["posted_on"].format(date=posted_date)
    return (
        f'<article class="stage" id="{card_id}" data-chapter="{chapter}" '
        f'data-formation-id="{group["formation_id"]}" data-source-message-ids="{group["source_ids_attr"]}" '
        f'data-stages="{",".join(str(n) for n in sorted(set(group["numbers"])))}" '
        f'data-posted-at="{html.escape(group["posted_at_min"], quote=True)}">'
        f'<h2 class="stage-title"><a href="{source["source_message_url"]}" target="_blank" rel="noopener noreferrer" '
        f'title="{html.escape(S["discord_link_title"], quote=True)}">{stage}</a>'
        f'<span class="card-meta">'
        f'<span class="level" title="{group["level_title"]}" aria-label="{group["level_title"]}">{group["level_text"]}</span>'
        f'<time class="posted" datetime="{html.escape(group["posted_at_min"], quote=True)}" title="{html.escape(posted_label, quote=True)}">'
        f'{html.escape(posted_date)}</time></span>'
        f'</h2>'
        f'<p class="poster">{S["posted_by"]} {group["poster_links"]}</p>'
        f'<div class="board" role="group" aria-label="{board_aria}">{"".join(cells_html)}</div>'
        f'<div class="report"><button type="button" class="report-btn" aria-expanded="false">'
        f'{REPORT_FLAG_SVG}<span>{html.escape(S["report_button"])}</span></button></div></article>')


def count_spans(fmt: str, cards: int, stages: int) -> str:
    """Split a "{cards} … · {stages} …" string into two spans (stages first), no joining dot."""
    parts = [part.strip() for part in fmt.split(" · ")]
    parts.sort(key=lambda part: "{stages}" not in part)
    return "".join(f'<span>{html.escape(part.format(cards=cards, stages=stages))}</span>' for part in parts)


def render_home_main(lang: str, chapter_stats: dict, dojo_stats: dict) -> str:
    S = STRINGS[lang]
    items = []
    for c in CHAPTERS:
        n = c["chapter"]
        stats = chapter_stats[n]
        empty = stats["cards"] == 0
        count_html = (f'<span>{html.escape(S["chapter_count_empty"])}</span>' if empty else
                      count_spans(S["chapter_count"], stats["cards"], stats["stages"]))
        items.append(
            f'<li><a class="{"is-empty" if empty else ""}" href="{page_path(lang, "chapter", n)}">'
            f'<span class="chapter-name">{html.escape(S["chapter_option_label"].format(n=n))}</span>'
            f'<span class="chapter-count">{count_html}</span></a></li>')
    heading = html.escape(S["home_chapters_heading"])
    return (f'<h2 class="section-heading">{heading}</h2>'
            f'<ul class="chapter-grid" aria-label="{heading}">{"".join(items)}</ul>'
            f'<h2 class="section-heading" id="dojo">{html.escape(S["dojo_heading"])}</h2>'
            + render_dojo_grid(lang, dojo_stats))


def render_chapter_main(lang: str, chapter_number: int, cards_html: list[str]) -> str:
    S = STRINGS[lang]
    if cards_html:
        body = f'<div class="cards-grid" id="chapter-cards">{"".join(cards_html)}</div>'
    else:
        body = f'<p class="empty-chapter">{html.escape(S["empty_chapter_message"])}</p>'
    numbers = [c["chapter"] for c in CHAPTERS]
    idx = numbers.index(chapter_number)
    if idx < len(numbers) - 1:
        next_n = numbers[idx + 1]
        body += (
            f'<div class="next-stage"><a class="next-stage-link" href="{page_path(lang, "chapter", next_n)}" '
            f'data-next-chapter="{next_n}" '
            f'aria-label="{html.escape(S["next_stage_aria"].format(n=next_n), quote=True)}">'
            f'{html.escape(S["next_stage_button"].format(n=next_n))}</a></div>')
    return body


def render_dojo_card(group: dict, lang: str, is_first: bool) -> str:
    S = STRINGS[lang]
    element = group["element"]
    element_name = S["dojo_element_names"][element]
    cells_html = []
    for r, c, key in group["cells"]:
        if key:
            unit = unit_record(key, r, c)
            label = f'{unit["name"]} · T{unit["tier"]} · ' + S["row_col"].format(row=r, column=c)
            loading_attr = "" if is_first else ' loading="lazy"'
            cells_html.append(
                f'<div class="cell occupied" title="{html.escape(label)}">'
                f'<img src="/sprites/{key}.png" alt="{html.escape(label)}" width="200" height="200" '
                f'decoding="async" draggable="false"{loading_attr}></div>')
        else:
            empty_label = S["empty_cell"].format(row=r, column=c)
            cells_html.append(f'<div class="cell" aria-label="{html.escape(empty_label)}"></div>')
    stage = group["stage_label"]
    board_aria = html.escape(S["dojo_board_aria"].format(element=element_name, stage=stage), quote=True)
    posted_date = format_posted_date(group["posted_at"], lang)
    posted_label = S["posted_on"].format(date=posted_date)
    poster = (f'<a href="{html.escape(group["source_message_url"], quote=True)}" target="_blank" '
              f'rel="noopener noreferrer">{html.escape(group["display_name"])}</a>')
    return (
        f'<article class="stage dojo-card" id="{group["card_id"]}" data-dojo="{element}" data-floor="{group["floor"]}" '
        f'data-formation-id="{group["formation_id"]}" data-stages="{",".join(str(n) for n in group["numbers"])}" '
        f'data-posted-at="{html.escape(group["posted_at"], quote=True)}">'
        f'<h3 class="stage-title"><a href="{html.escape(group["source_message_url"], quote=True)}" target="_blank" '
        f'rel="noopener noreferrer" title="{html.escape(S["discord_link_title"], quote=True)}">{stage}</a>'
        f'<span class="card-meta"><time class="posted" datetime="{html.escape(group["posted_at"], quote=True)}" '
        f'title="{html.escape(posted_label, quote=True)}">{html.escape(posted_date)}</time></span></h3>'
        f'<p class="poster">{S["posted_by"]} {poster}</p>'
        f'<div class="board dojo-board" role="group" aria-label="{board_aria}">{"".join(cells_html)}</div></article>')


def render_dojo_tabs(lang: str, current: str | None) -> str:
    S = STRINGS[lang]
    tabs = "".join(
        f'<a class="dojo-tab dojo-{element}" href="{page_path(lang, "dojo", element)}"'
        + (' aria-current="page"' if element == current else '')
        + f'>{html.escape(S["dojo_element_title"].format(element=S["dojo_element_names"][element]))}</a>'
        for element in DOJO_ELEMENTS)
    return f'<nav class="dojo-tabs" aria-label="{html.escape(S["dojo_heading"], quote=True)}">{tabs}</nav>'


def render_dojo_grid(lang: str, dojo_stats: dict) -> str:
    S = STRINGS[lang]
    items = []
    for element in DOJO_ELEMENTS:
        stats = dojo_stats[element]
        items.append(
            f'<li><a class="dojo-{element}" href="{page_path(lang, "dojo", element)}">'
            f'<span class="chapter-name">{html.escape(S["dojo_element_title"].format(element=S["dojo_element_names"][element]))}</span>'
            f'<span class="chapter-count">{count_spans(S["dojo_count"], stats["cards"], stats["stages"])}</span></a></li>')
    heading = html.escape(S["dojo_heading"])
    return f'<ul class="chapter-grid dojo-grid" aria-label="{heading}">{"".join(items)}</ul>'


def render_dojo_index_main(lang: str, dojo_stats: dict) -> str:
    return render_dojo_grid(lang, dojo_stats)


def render_dojo_main(lang: str, element: str, floor_groups: dict[int, list[dict]]) -> str:
    S = STRINGS[lang]
    element_name = S["dojo_element_names"][element]
    jump = "".join(
        f'<a href="#dojo-{element}-{floor}">{html.escape(S["dojo_floor_link"].format(n=floor))}</a>'
        for floor in DOJO_FLOORS if floor_groups.get(floor))
    sections = []
    card_index = 0
    for floor in DOJO_FLOORS:
        groups = floor_groups.get(floor, [])
        if not groups:
            continue
        cards = []
        for group in groups:
            cards.append(render_dojo_card(group, lang, card_index == 0))
            card_index += 1
        sections.append(
            f'<section class="dojo-floor" id="dojo-{element}-{floor}" aria-labelledby="dojo-{element}-{floor}-heading">'
            f'<div class="floor-head"><h2 class="section-heading" id="dojo-{element}-{floor}-heading">'
            f'{html.escape(S["dojo_floor_heading"].format(element=element_name, n=floor))}</h2>'
            f'<p class="floor-range">{floor}-1 – {floor}-10</p></div>'
            f'<div class="cards-grid dojo-cards">{"".join(cards)}</div></section>')
    return (render_dojo_tabs(lang, element)
            + f'<nav class="floor-jump" aria-label="{html.escape(S["dojo_element_title"].format(element=element_name), quote=True)}">{jump}</nav>'
            + "".join(sections))


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
        if 50 <= chapter <= 73:
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
        "chapter_71_74_update": "November 13: owner requested Casey's latest formations after 71-9. 111 Casey image posts (November 5–13) supply 113 chapter records covering 71-10 through 74-37 at player levels 1457–1616. Previous 66pika and other references for those stages are archived with replacement relationships; 74-38 onward keep their prior selections. The 73-25–73-26 post is captioned 75-25 to 75-26; its screenshot shows 73-27.",
        "chapter_23_update": "November 10: chapter 23 follows the same October 21 cutoff after stage reports showed pre-update boards failing; all 80 stages use tim370514's November 7–8 clears.",
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

    # Badge Dojo formations: separate from chapter stages, one 4×3 board per record.
    dojo_records = []
    dojo_groups: dict[tuple, dict] = {}
    dojo_coverage: Counter = Counter()
    for record in DOJO_REVIEWED:
        element, floor, board = record["element"], record["floor"], record["board"]
        mid = record["source_message_id"]
        assert element in DOJO_ELEMENTS and floor in DOJO_FLOORS, mid
        assert len(board) == DOJO_ROWS and all(len(row) == DOJO_COLUMNS for row in board), mid
        numbers = record["website_stage_numbers"]
        assert numbers and all(1 <= n <= 10 for n in numbers) and numbers == sorted(set(numbers)), mid
        assert datetime.fromisoformat(record["posted_at"].replace("Z", "+00:00")) <= datetime.now(timezone.utc), mid
        lineup = [unit_record(key, r, c) for r, row in enumerate(board, 1) for c, key in enumerate(row, 1) if key]
        for unit in lineup:
            unit["position"] = (unit["row"] - 1) * DOJO_COLUMNS + unit["column"]
            assert FORMS[unit["form_id"]]["element"].lower() == element, (mid, unit["form_id"])
        assert len(lineup) == 5, (mid, len(lineup))
        families = Counter(unit["family_id"] for unit in lineup)
        assert all(count == 1 for count in families.values()), (mid, families)
        if not record.get("selected_for_website", True):
            continue
        for n in numbers:
            dojo_coverage[(element, floor, n)] += 1
        formation_id = f"{mid}:dojo-{element}-{floor}-{record['image_index']}"
        signature = json.dumps([(u["position"], u["form_id"]) for u in lineup], separators=(",", ":"))
        dojo_records.append({**record, "formation_id": formation_id, "lineup": lineup,
                             "formation_hash": hashlib.sha256(signature.encode()).hexdigest(),
                             "outcome_basis": "Author-reported clear; not independently tested in game."})
        group = dojo_groups.setdefault((element, floor, dojo_records[-1]["formation_hash"]), {
            "element": element, "floor": floor, "board": board, "numbers": [],
            "formation_id": formation_id, "source_message_url": record["source_message_url"],
            "display_name": record["display_name"], "posted_at": record["posted_at"],
        })
        group["numbers"] = sorted(set(group["numbers"]) | set(numbers))
        if record["posted_at"] < group["posted_at"]:
            group["posted_at"] = record["posted_at"]
    duplicated = [key for key, count in dojo_coverage.items() if count > 1]
    assert not duplicated, f"More than one selected dojo formation for {duplicated}"
    dojo_floor_groups: dict[str, dict[int, list[dict]]] = {element: {} for element in DOJO_ELEMENTS}
    for group in sorted(dojo_groups.values(), key=lambda g: (DOJO_ELEMENTS.index(g["element"]), g["floor"], g["numbers"][0])):
        element, floor = group["element"], group["floor"]
        group["stage_label"] = stage_label(group["numbers"], floor)
        group["card_id"] = f"dojo-{element}-{floor}-{group['numbers'][0]}"
        group["cells"] = [(r, c, key) for r, row in enumerate(group["board"], 1) for c, key in enumerate(row, 1)]
        for row in group["board"]:
            for key in row:
                if key:
                    sprites.setdefault(key, sprite_path(key))
        dojo_floor_groups[element].setdefault(floor, []).append(group)
    dojo_stats = {element: {"cards": sum(len(groups) for groups in dojo_floor_groups[element].values()),
                            "stages": sum(1 for (e, _, _) in dojo_coverage if e == element)}
                  for element in DOJO_ELEMENTS}
    (DOJO_FILE.parent / "dojo-lineups.json").write_text(json.dumps({
        "schema_version": "1.0",
        "collected_at": "2026-11-11",
        "description": "Badge Dojo formations for Water, Fire, Grass, Rock and Lightning Dojo 1–7. Boards have 4 rows (front to rear) and 3 columns (left to right).",
        "collection_method": "Authenticated Discord website, read-only browser inspection of posts found with element dojo searches.",
        "catalog_reference": {"url": CATALOG["source_url"], "version": CATALOG["source_version"]},
        "selection_policy": "One selected formation per dojo stage, preferring posts after August 27, 2026 that cover a whole floor or the author's explicit stage list. Lightning Dojo 2 uses a July 19 post because no newer complete reference was found.",
        "stages": [{"stage": f"{element}-{floor}-{n}", "formation_id": record["formation_id"]}
                   for record in dojo_records for element, floor in [(record["element"], record["floor"])]
                   for n in record["website_stage_numbers"]],
        "unavailable_stages": [f"{e}-{f}-{n}" for e in DOJO_ELEMENTS for f in DOJO_FLOORS for n in range(1, 11)
                               if (e, f, n) not in dojo_coverage],
        "formations": dojo_records,
    }, ensure_ascii=False, indent=2) + "\n")

    template = (ROOT / "page-template.html").read_text()
    site = ROOT / "site"
    # Chapter pages are static (crawlable without JS); each chapter's sprites are separate
    # files so visitors download only what a chapter's cards reference.
    shutil.rmtree(site / "chapters", ignore_errors=True)
    for generated in ("sprites", "chapter", "dojo", "og", *(lang_prefix(l).lstrip("/") for l in LANGS if lang_prefix(l))):
        shutil.rmtree(site / generated, ignore_errors=True)
    (site / "sprites").mkdir(parents=True)
    (site / "chapter").mkdir(parents=True)
    for lang in LANGS:
        (lang_dir(site, lang) / "chapter").mkdir(parents=True, exist_ok=True)
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
    render_og_image(site / "og" / "dojo.png", "Badge Dojo", "Clash of Critters Formations",
                     f"{len(DOJO_ELEMENTS)} elements · Dojo 1–7")
    for element in DOJO_ELEMENTS:
        stats = dojo_stats[element]
        render_og_image(site / "og" / f"dojo-{element}.png", f"{STRINGS['en']['dojo_element_names'][element]} Dojo",
                         "Clash of Critters Formations", f"{stats['cards']} cards · {stats['stages']} stages")

    for lang in LANGS:
        strings = STRINGS[lang]
        main_content = render_home_main(lang, chapter_stats, dojo_stats)
        page = render_shell(
            template, lang, "home",
            title=strings["home_title"], description=strings["home_description"],
            canonical_path=page_path(lang, "home"), h1=strings["home_h1"], main_content=main_content,
            og_image_path="og/home.png", og_image_alt=strings["og_alt_home"],
            jsonld_scripts=[website_jsonld(lang)],
        )
        home_file = lang_dir(site, lang) / "index.html"
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
            chapter_dir = lang_dir(site, lang) / "chapter" / str(number)
            chapter_dir.mkdir(parents=True, exist_ok=True)
            (chapter_dir / "index.html").write_text(page)

    for lang in LANGS:
        strings = STRINGS[lang]
        page = render_shell(
            template, lang, "dojo_index",
            title=strings["dojo_index_title"], description=strings["dojo_index_description"],
            canonical_path=page_path(lang, "dojo_index"), h1=strings["dojo_index_h1"],
            main_content=render_dojo_index_main(lang, dojo_stats),
            og_image_path="og/dojo.png", og_image_alt=strings["dojo_index_h1"], jsonld_scripts=[],
        )
        dojo_dir = lang_dir(site, lang) / "dojo"
        dojo_dir.mkdir(parents=True, exist_ok=True)
        (dojo_dir / "index.html").write_text(page)
        for element in DOJO_ELEMENTS:
            element_name = strings["dojo_element_names"][element]
            stats = dojo_stats[element]
            breadcrumb = jsonld_script({
                "@context": "https://schema.org", "@type": "BreadcrumbList",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": strings["breadcrumb_home"], "item": SITE_URL + page_path(lang, "home")},
                    {"@type": "ListItem", "position": 2, "name": strings["dojo_heading"], "item": SITE_URL + page_path(lang, "dojo_index")},
                    {"@type": "ListItem", "position": 3, "name": strings["dojo_element_title"].format(element=element_name),
                     "item": SITE_URL + page_path(lang, "dojo", element)},
                ],
            })
            page = render_shell(
                template, lang, "dojo", chapter=element,
                title=strings["dojo_title"].format(element=element_name),
                description=strings["dojo_description"].format(element=element_name, cards=stats["cards"], stages=stats["stages"]),
                canonical_path=page_path(lang, "dojo", element), h1=strings["dojo_h1"].format(element=element_name),
                main_content=render_dojo_main(lang, element, dojo_floor_groups[element]),
                og_image_path=f"og/dojo-{element}.png", og_image_alt=strings["og_alt_dojo"].format(element=element_name),
                jsonld_scripts=[breadcrumb], robots_noindex=not stats["cards"],
            )
            (dojo_dir / element).mkdir(parents=True, exist_ok=True)
            (dojo_dir / element / "index.html").write_text(page)

    for lang in LANGS:
        strings = STRINGS[lang]
        main_content = render_privacy_main(lang)
        page = render_shell(
            template, lang, "privacy",
            title=strings["privacy_title"], description=strings["privacy_description"],
            canonical_path=page_path(lang, "privacy"), h1=strings["privacy_h1"], main_content=main_content,
            og_image_path="og/home.png", og_image_alt=strings["og_alt_home"], jsonld_scripts=[],
        )
        privacy_file = lang_dir(site, lang) / "privacy.html"
        privacy_file.write_text(page)

    collected_at = dataset["collected_at"]

    def hreflang_sitemap_links(page_type: str, chapter_number: int | None) -> str:
        links = [f'\n    <xhtml:link rel="alternate" hreflang="{LANG_INFO[lang]["code"]}" '
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
    sitemap_urls += [sitemap_entry(lang, "dojo_index") for lang in LANGS]
    sitemap_urls += [sitemap_entry(lang, "dojo", element) for element in DOJO_ELEMENTS
                     if dojo_stats[element]["cards"] for lang in LANGS]
    sitemap_urls += [sitemap_entry(lang, "privacy") for lang in LANGS]
    sitemap_xml = ('<?xml version="1.0" encoding="UTF-8"?>\n'
                   '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
                   'xmlns:xhtml="http://www.w3.org/1999/xhtml">\n' + "\n".join(sitemap_urls) + "\n</urlset>\n")
    (site / "sitemap.xml").write_text(sitemap_xml)
    (site / "robots.txt").write_text(
        "User-agent: *\nAllow: /\nDisallow: /chapters/\nSitemap: " + SITE_URL + "/sitemap.xml\n")

    print(f"Built {len(stages)} stages in {len(groups)} grouped formation cards; "
          f"{len(dojo_coverage)} dojo stages in {sum(s['cards'] for s in dojo_stats.values())} dojo cards; "
          f"{len(sprites)} exact sprite variants. Site: {site}")


if __name__ == "__main__":
    build()
