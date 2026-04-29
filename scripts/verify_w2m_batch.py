"""
Weeks-to-months batch validator.

Phase 2 Step 5 (Option B), G2A sample-page validator.

Verifies a generated leaf set against the round 1.5 must-fix list:
  1. Arithmetic correctness on every leaf (4-week months, calendar
     months, days since LMP all derived from week * 7 / convention).
  2. JSON-LD parses as JSON; carries WebPage and BreadcrumbList only;
     no FAQPage, no HowTo, no Product, no MedicalWebPage.
  3. Title, H1, meta description, canonical URL all unique across
     the set.
  4. Self-canonical, never points to the hub or another leaf.
  5. Hero answer exists, mentions four-week pregnancy months, mentions
     average calendar months, mentions days since LMP.
  6. Forbidden language: no medical claims ("post-term", "normal",
     "should", "doctor", "clinician recommends", etc.) on any leaf.
  7. Edge-week LMP note present on weeks 1, 2, 3.
  8. Adjacent-week links present except where at the boundary.
  9. styles.css and app.js cache-bust query strings present.

Usage:
    python3 scripts/verify_w2m_batch.py --dir pregnancy/weeks-to-months-staging
    python3 scripts/verify_w2m_batch.py --dir pregnancy/weeks-to-months
"""

from __future__ import annotations
import argparse
import json
import os
import re
import sys

DIST = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from w2m_data_schema import (
    make_record, descriptive_adjacent_anchor_text,
    AVG_CALENDAR_MONTH_DAYS, FOUR_WEEK_MONTH_DAYS,
    MIN_WEEK, MAX_WEEK,
)


# Forbidden language per round 2 Q10 must-fix (tightened from round 1.5).
# Hard-fail patterns: any match aborts the build.
FORBIDDEN_PATTERNS = [
    r"\bpost[-\s]?term\b",
    r"\bpre[-\s]?term\b",
    r"\bdoctor\b",
    r"\bclinician\b",
    r"\bmidwife\b",
    r"\bprovider\b",
    r"\bdiagnos\w*\b",
    r"\bsymptom\w*\b",
    r"\bappointment\b",
    r"\bultrasound\b",
    r"\bfetal\b",
    r"\bfetus\b",
    r"\bembryo\b",
    r"\bbaby weight\b",
    r"\bnormal range\b",
    r"\btrimester\b",
    r"\bcontraction\w*\b",
    r"\bmiscarriage\b",
    r"\bcomplication\w*\b",
    r"\brisks?\b",
]

# Warning-only patterns: emit a warning but do NOT fail the build.
# These tend to appear in harmless context (source descriptions, technical
# copy) but warrant human review at the G2A sample gate.
ADVICE_WARN_PATTERNS = [
    r"\bshould\b",
    r"\brecommend(?:ed|s|ation)?\b",
    r"\bsee your\b",
    r"\bask your\b",
    r"\bcheck with\b",
]

# Allow-list of literal phrases that legitimately contain forbidden
# words. These are global asset names (e.g., article titles linked from
# the related-tools section). Stripped from the scanned text before the
# forbidden-pattern check runs. Keep this list small and explicit.
ALLOWED_LITERAL_PHRASES = [
    "First Trimester Week by Week",   # global article title in related-tools
    "first-trimester-week-by-week",   # the URL slug for that article
]


def _read_html(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _extract_main_content(html: str) -> str:
    """Return the <main>...</main> region only.

    Per round 2 Q10 reviewer note: scan the main content region plus
    JSON-LD for forbidden language, NOT the whole page. The canonical
    nav and drawer contain words like "trimester" via legitimate global
    links to articles like "First Trimester Week by Week"; those are not
    leaf-copy drift.
    """
    m = re.search(r'<main\b[^>]*>(.*?)</main>', html, flags=re.DOTALL | re.IGNORECASE)
    return m.group(1) if m else ""


def _extract_jsonld_blocks(html: str) -> list[dict]:
    blocks = re.findall(
        r'<script type="application/ld\+json">(.*?)</script>',
        html, flags=re.DOTALL,
    )
    parsed = []
    for b in blocks:
        parsed.append(json.loads(b))
    return parsed


def _check_one(week: int, html: str, expected_robots: str,
              errors: list[str], warnings: list[str]) -> None:
    rec = make_record(week)
    where = f"week {week}"

    # 1. Title / H1 / meta / canonical match the deterministic record.
    if rec.title not in html:
        errors.append(f"{where}: title missing or wrong")
    if f'<h1 class="pl-h1">{rec.h1}</h1>' not in html:
        errors.append(f"{where}: H1 missing or wrong")
    if rec.meta_description not in html:
        errors.append(f"{where}: meta description missing or wrong")
    if f'rel="canonical" href="{rec.canonical_url}"' not in html:
        errors.append(f"{where}: canonical missing or wrong")

    # 1a. Singular week handling (round 2 Q4 + Q13 must-fix).
    # Prevent "1 weeks" from appearing anywhere.
    if rec.week == 1:
        bad_phrases = ["1 weeks", "1 Weeks"]
        for bad in bad_phrases:
            if bad in html:
                errors.append(f"{where}: rendered '{bad}' instead of singular form")

    # 2. Hero answer present.
    if rec.hero_answer not in html:
        errors.append(f"{where}: hero answer not rendered correctly")

    # 3. Cache-bust strings present.
    if "/assets/styles.css?v=25" not in html:
        errors.append(f"{where}: styles.css cache-bust missing")
    if "/assets/app.js?v=19" not in html:
        errors.append(f"{where}: app.js cache-bust missing")

    # 4. Robots meta matches build mode (round 2 Q11 must-fix).
    expected = f'<meta name="robots" content="{expected_robots}"'
    if expected not in html:
        errors.append(f"{where}: robots meta missing or wrong, expected '{expected_robots}'")

    # 5. JSON-LD parses, has WebPage + BreadcrumbList, no forbidden types.
    try:
        blocks = _extract_jsonld_blocks(html)
    except json.JSONDecodeError as e:
        errors.append(f"{where}: JSON-LD parse error: {e}")
        return
    types_seen = set()
    webpage_block = None
    breadcrumb_block = None
    for b in blocks:
        t = b.get("@type")
        if isinstance(t, list):
            for x in t:
                types_seen.add(x)
        elif isinstance(t, str):
            types_seen.add(t)
        if t == "WebPage":
            webpage_block = b
        elif t == "BreadcrumbList":
            breadcrumb_block = b
    forbidden_types = {"FAQPage", "HowTo", "Product", "Offer", "AggregateRating",
                       "Review", "MedicalWebPage", "Article"}
    bad = forbidden_types & types_seen
    if bad:
        errors.append(f"{where}: forbidden JSON-LD types present: {bad}")
    if "WebPage" not in types_seen:
        errors.append(f"{where}: WebPage JSON-LD missing")
    if "BreadcrumbList" not in types_seen:
        errors.append(f"{where}: BreadcrumbList JSON-LD missing")

    # 5a. Schema @id, url, breadcrumb final-item parity (round 2 Q9 + Q13).
    if webpage_block is not None:
        wp_id = webpage_block.get("@id", "")
        if not wp_id.startswith(rec.canonical_url):
            errors.append(f"{where}: WebPage @id missing or wrong, expected to start with {rec.canonical_url}")
        if webpage_block.get("url") != rec.canonical_url:
            errors.append(f"{where}: WebPage url does not equal canonical")
    if breadcrumb_block is not None:
        bc_id = breadcrumb_block.get("@id", "")
        if not bc_id.startswith(rec.canonical_url):
            errors.append(f"{where}: BreadcrumbList @id missing or wrong")
        items = breadcrumb_block.get("itemListElement", [])
        if not items:
            errors.append(f"{where}: BreadcrumbList has no itemListElement")
        else:
            last = items[-1]
            if last.get("item") != rec.canonical_url:
                errors.append(f"{where}: BreadcrumbList final item != canonical")
            if last.get("name") != rec.breadcrumb_position3_name:
                errors.append(f"{where}: BreadcrumbList final name != expected")

    # 6. Forbidden language check (hard-fail), scoped to <main> only.
    # Per round 2 Q10: do not scan global nav/drawer/footer because those
    # carry legitimate global links to articles like "First Trimester
    # Week by Week" which would false-positive. Also strip allow-listed
    # global phrases (article titles linked from related-tools) so they
    # don't trigger the forbidden check inside <main>.
    main_html = _extract_main_content(html).lower()
    for phrase in ALLOWED_LITERAL_PHRASES:
        main_html = main_html.replace(phrase.lower(), "")
    for pat in FORBIDDEN_PATTERNS:
        if re.search(pat, main_html):
            errors.append(f"{where}: forbidden language matches /{pat}/ in <main>")

    # 6a. Advice-language warnings (do not fail), also <main> scoped.
    for pat in ADVICE_WARN_PATTERNS:
        if re.search(pat, main_html):
            warnings.append(f"{where}: advice-like language matches /{pat}/ in <main> (review at G2A)")

    # 7. LMP note on weeks 1-3.
    if rec.is_lmp_counted and "pl-w2m-lmp-note" not in html:
        errors.append(f"{where}: LMP-counted week missing the LMP note section")

    # 8. Adjacent-week links present where they should be, with descriptive text.
    if rec.prev_week is not None:
        prev_text = descriptive_adjacent_anchor_text(rec.prev_week)
        if f'href="/pregnancy/weeks-to-months/{rec.prev_week}/"' not in html:
            errors.append(f"{where}: prev-week link to week {rec.prev_week} missing")
        if prev_text not in html:
            errors.append(f"{where}: prev link descriptive text '{prev_text}' missing")
    if rec.next_week is not None:
        next_text = descriptive_adjacent_anchor_text(rec.next_week)
        if f'href="/pregnancy/weeks-to-months/{rec.next_week}/"' not in html:
            errors.append(f"{where}: next-week link to week {rec.next_week} missing")
        if next_text not in html:
            errors.append(f"{where}: next link descriptive text '{next_text}' missing")

    # 9. Hub link.
    if 'href="/pregnancy/weeks-to-months/"' not in html:
        errors.append(f"{where}: hub link missing")
    # 10. Methodology link.
    if 'href="/methodology/weeks-to-months"' not in html:
        errors.append(f"{where}: methodology link missing")

    # 11. Mini-table arithmetic (round 2 Q13 must-fix).
    # Window is target ± 2, clipped at boundaries.
    expected_window = []
    for w in range(rec.week - 2, rec.week + 3):
        if MIN_WEEK <= w <= MAX_WEEK:
            expected_window.append(w)
    for w in expected_window:
        wrec = make_record(w)
        # Each row should contain week, four-week-months, calendar, days.
        # The first <td> may carry an LMP-counted span on weeks 1-3 with
        # a class name that itself contains a digit, so we use .*? in
        # DOTALL mode rather than a digit-excluding character class.
        row_pattern = re.compile(
            r'<tr[^>]*>\s*<td>%d(?:</td>|\s.*?</td>)\s*<td>%s</td>\s*<td>~%s</td>\s*<td>%d</td>'
            % (w, re.escape(wrec.four_week_months_str),
               re.escape(wrec.calendar_months_str),
               wrec.days_since_lmp),
            re.DOTALL,
        )
        if not row_pattern.search(html):
            errors.append(
                f"{where}: mini-table row for week {w} missing or wrong "
                f"(expected {wrec.four_week_months_str} 4wm, "
                f"~{wrec.calendar_months_str} cal, {wrec.days_since_lmp}d)"
            )

    # 12. Social meta parity (round 2 Q13 must-fix).
    og_title = f'<meta property="og:title" content="{rec.title}"'
    og_desc = f'<meta property="og:description" content="{rec.meta_description}"'
    og_url = f'<meta property="og:url" content="{rec.canonical_url}"'
    twitter_title = f'<meta name="twitter:title" content="{rec.title}"'
    twitter_desc = f'<meta name="twitter:description" content="{rec.meta_description}"'
    if og_title not in html:
        errors.append(f"{where}: og:title != page title")
    if og_desc not in html:
        errors.append(f"{where}: og:description != meta description")
    if og_url not in html:
        errors.append(f"{where}: og:url != canonical")
    if twitter_title not in html:
        errors.append(f"{where}: twitter:title != page title")
    if twitter_desc not in html:
        errors.append(f"{where}: twitter:description != meta description")


def _check_uniqueness(records: dict, errors: list[str]) -> None:
    titles = {}
    h1s = {}
    metas = {}
    canonicals = {}
    for w, html in records.items():
        rec = make_record(w)
        for d, key in ((titles, rec.title),
                       (h1s, rec.h1),
                       (metas, rec.meta_description),
                       (canonicals, rec.canonical_url)):
            d.setdefault(key, []).append(w)
    for d, name in ((titles, "title"), (h1s, "H1"),
                    (metas, "meta"), (canonicals, "canonical")):
        for v, ws in d.items():
            if len(ws) > 1:
                errors.append(f"non-unique {name} across weeks {ws}: {v[:60]}")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dir", required=True,
                    help="dist-relative directory containing N/index.html leaves")
    ap.add_argument("--weeks", default=None,
                    help="comma-separated week subset; default inspects whatever exists")
    args = ap.parse_args()

    base = os.path.join(DIST, args.dir)
    if not os.path.isdir(base):
        print(f"directory not found: {base}", file=sys.stderr)
        return 1

    weeks_filter = None
    if args.weeks:
        weeks_filter = {int(t.strip()) for t in args.weeks.split(",") if t.strip()}

    found = {}
    for entry in sorted(os.listdir(base), key=lambda x: (not x.isdigit(), int(x) if x.isdigit() else 0)):
        if not entry.isdigit():
            continue
        w = int(entry)
        if weeks_filter and w not in weeks_filter:
            continue
        path = os.path.join(base, entry, "index.html")
        if not os.path.isfile(path):
            continue
        found[w] = _read_html(path)

    if not found:
        print(f"no leaves found in {base}", file=sys.stderr)
        return 1

    # Determine expected robots mode from the directory name.
    is_staging = "staging" in args.dir.lower()
    expected_robots = "noindex,nofollow" if is_staging else "index,follow"

    errors: list[str] = []
    warnings: list[str] = []
    for w in sorted(found.keys()):
        _check_one(w, found[w], expected_robots, errors, warnings)
    _check_uniqueness(found, errors)

    print(f"verified {len(found)} leaves in {os.path.relpath(base, DIST)} "
          f"(expecting robots={expected_robots})")
    if warnings:
        print(f"\nWARNINGS ({len(warnings)}):")
        for w in warnings:
            print(f"  {w}")
    if errors:
        print(f"\nFAIL — {len(errors)} issues:")
        for e in errors:
            print(f"  {e}")
        return 1
    print("PASS — all checks clean")
    return 0


if __name__ == "__main__":
    sys.exit(main())
