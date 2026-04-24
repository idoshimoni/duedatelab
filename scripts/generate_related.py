#!/usr/bin/env python3
"""
Regenerate Related-card grids across the DueDateLab site.

For every HTML file listed in INCLUDED_FOR_RELATED (site_topics.py),
find the existing <div class="pl-related-grid..."> block, determine the
N best topically-adjacent URLs from URL_TOPICS, and rewrite the grid's
inner anchors. Card rendering style (div+p for flagship tools, strong+span
for articles/methodology) is auto-detected from the existing block.

Scoring rule:
  score(target, candidate) = |topics(target) ∩ topics(candidate)|
Tie-break:
  1. Sister page is always included first if defined.
  2. Higher sitemap priority wins (lower number = higher priority).
  3. Stable alphabetical URL.

Self-links and excluded URLs are never candidates.

Usage:
  python3 scripts/generate_related.py --check   # dry run, exit 1 if any file would change
  python3 scripts/generate_related.py --write   # apply changes
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from sitemap_urls import URL_MAP  # noqa: E402
from site_topics import (  # noqa: E402
    URL_TOPICS,
    INCLUDED_FOR_RELATED,
    EXCLUDED_FROM_RELATED,
    RELATED_CARD_COUNT,
    SISTER_PAGES,
)

DIST_DIR = SCRIPT_DIR.parent

# Build helpers ----------------------------------------------------------------

URL_BY_SOURCE = {e["source"]: e["url"] for e in URL_MAP}
SOURCE_BY_URL = {e["url"]: e["source"] for e in URL_MAP}
PRIORITY_BY_URL = {e["url"]: float(e["priority"]) for e in URL_MAP}


def candidates_for(target_url: str) -> list[str]:
    """Return ranked list of candidate URLs for a target page's Related grid."""
    target_topics = set(URL_TOPICS.get(target_url, {}).get("topics", []))

    # Sister page first (pair convention).
    ranked: list[str] = []
    sister = SISTER_PAGES.get(target_url)
    if sister and sister in URL_TOPICS and sister != target_url:
        ranked.append(sister)

    # All other candidates, scored.
    scored: list[tuple[int, float, str, str]] = []
    for url, meta in URL_TOPICS.items():
        if url == target_url:
            continue
        if url in ranked:
            continue
        cand_topics = set(meta.get("topics", []))
        score = len(target_topics & cand_topics)
        if score == 0:
            continue
        # Exclude hub pages from non-hub targets (hubs crowd the grid).
        if "hub" in cand_topics and "hub" not in target_topics:
            continue
        # Exclude company pages.
        if "company" in cand_topics:
            continue
        priority = -PRIORITY_BY_URL.get(url, 0.5)  # higher priority ranks first
        scored.append((-score, priority, url, url))

    scored.sort()
    for _s, _p, url, _u in scored:
        if url not in ranked:
            ranked.append(url)

    # Padding fallback: if we still have fewer than RELATED_CARD_COUNT,
    # fill with top-priority non-hub, non-company URLs (excluding self/duplicates).
    # Happens for narrow-topic pages like the gender-chart cluster where
    # only 2 other URLs share the "novelty" / "sex-determination" tags.
    if len(ranked) < RELATED_CARD_COUNT:
        pad_candidates: list[tuple[float, str]] = []
        for url, meta in URL_TOPICS.items():
            if url == target_url or url in ranked:
                continue
            cand_topics = set(meta.get("topics", []))
            if "hub" in cand_topics or "company" in cand_topics:
                continue
            pad_candidates.append((-PRIORITY_BY_URL.get(url, 0.5), url))
        pad_candidates.sort()
        for _p, url in pad_candidates:
            if len(ranked) >= RELATED_CARD_COUNT:
                break
            ranked.append(url)

    return ranked[:RELATED_CARD_COUNT]


# Rendering --------------------------------------------------------------------

DIV_CARD = (
    '<a class="pl-related-card" href="{url}">'
    '<div class="pl-related-title">{title}</div>'
    '<p class="pl-related-desc">{desc}</p>'
    '</a>'
)
STRONG_CARD = (
    '<a class="pl-related-card" href="{url}">'
    '<strong>{title}</strong>'
    '<span>{desc}</span>'
    '</a>'
)


def card_style_for(grid_html: str) -> str:
    """Detect card style from the existing grid block."""
    if 'pl-related-title' in grid_html:
        return "div"
    return "strong"


def render_cards(urls: list[str], style: str) -> str:
    tmpl = DIV_CARD if style == "div" else STRONG_CARD
    out = []
    for url in urls:
        meta = URL_TOPICS[url]
        out.append(tmpl.format(url=url, title=meta["title"], desc=meta["desc"]))
    return "".join(out)


# File rewriting ---------------------------------------------------------------

# Match the outer <div class="pl-related-grid..."> ... </div> followed by </section>.
# This anchor is necessary because flagship-tool cards contain nested
# <div class="pl-related-title">...</div> elements — a naive non-greedy
# </div> match would close at the first title-div and corrupt the HTML.
# Every grid is wrapped in <section class="pl-related">, so the grid's
# own </div> is the one immediately before </section>.
GRID_PATTERN = re.compile(
    r'(<div class="pl-related-grid[^"]*">)([\s\S]*?)(</div>)(\s*</section>)',
    re.MULTILINE,
)


def regenerate_file(source_rel: str) -> tuple[bool, str | None]:
    """Regenerate the Related grid in one file. Returns (changed, error_msg)."""
    target_url = URL_BY_SOURCE.get(source_rel)
    if target_url is None:
        return False, f"{source_rel}: not in sitemap_urls.URL_MAP"
    if target_url not in URL_TOPICS:
        return False, f"{source_rel}: not in site_topics.URL_TOPICS"

    path = DIST_DIR / source_rel
    if not path.exists():
        return False, f"{source_rel}: file does not exist"

    html = path.read_text()
    match = GRID_PATTERN.search(html)
    if not match:
        return False, f"{source_rel}: no pl-related-grid block found"

    open_tag, inner, close_tag, section_trailer = (
        match.group(1), match.group(2), match.group(3), match.group(4),
    )
    style = card_style_for(open_tag + inner + close_tag)

    cards = candidates_for(target_url)
    if len(cards) < RELATED_CARD_COUNT:
        return False, f"{source_rel}: only {len(cards)} candidates (< {RELATED_CARD_COUNT})"

    new_cards = render_cards(cards, style)
    indent_match = re.search(r'\n(\s*)<a class="pl-related-card"', inner)
    indent = indent_match.group(1) if indent_match else "      "

    # Detect grid closer indent (the whitespace before </div>).
    close_indent_match = re.search(r'\n(\s*)$', inner)
    close_indent = close_indent_match.group(1) if close_indent_match else "    "

    separator = "\n" + indent
    formatted = separator + separator.join(
        re.findall(r'<a class="pl-related-card"[^>]*>.*?</a>', new_cards)
    ) + "\n" + close_indent

    new_block = open_tag + formatted + close_tag + section_trailer
    old_block = match.group(0)
    if new_block == old_block:
        return False, None

    new_html = html[:match.start()] + new_block + html[match.end():]
    path.write_text(new_html)
    return True, None


def main() -> int:
    ap = argparse.ArgumentParser()
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true", help="dry run, exit 1 if changes would apply")
    group.add_argument("--write", action="store_true", help="apply regeneration")
    args = ap.parse_args()

    targets = sorted(INCLUDED_FOR_RELATED)
    any_change = False
    errors: list[str] = []

    for source_rel in targets:
        if source_rel in EXCLUDED_FROM_RELATED:
            continue
        if args.check:
            # Re-read and compare without writing.
            target_url = URL_BY_SOURCE.get(source_rel)
            if not target_url or target_url not in URL_TOPICS:
                errors.append(f"skipped {source_rel}: not in URL_MAP/URL_TOPICS")
                continue
            path = DIST_DIR / source_rel
            if not path.exists():
                errors.append(f"skipped {source_rel}: file missing")
                continue
            html = path.read_text()
            match = GRID_PATTERN.search(html)
            if not match:
                errors.append(f"skipped {source_rel}: no grid block")
                continue
            style = card_style_for(match.group(0))
            cards = candidates_for(target_url)
            new_cards_flat = render_cards(cards, style)
            # Loose comparison: does the new anchor set match what is currently there?
            current_anchors = sorted(re.findall(r'href="([^"]+)"', match.group(2)))
            new_anchors = sorted([u for u in cards])
            if current_anchors != new_anchors:
                any_change = True
                print(f"would regenerate: {source_rel} (was {current_anchors} -> {new_anchors})")
        else:
            changed, err = regenerate_file(source_rel)
            if err:
                errors.append(err)
            if changed:
                any_change = True
                print(f"regenerated: {source_rel}")

    for err in errors:
        print(f"NOTE: {err}", file=sys.stderr)

    if args.check and any_change:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
