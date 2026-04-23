#!/usr/bin/env python3
"""
Refresh freshness dates across the DueDateLab site.

What this does, in one pass:

  1. For each HTML file in dist/ (excluding build artifacts), rewrite
     all freshness fields to today's date:
       - visible "Last updated MONTH DD, YYYY"
       - JSON-LD "dateModified":"YYYY-MM-DD"
       - JSON-LD "lastReviewed":"YYYY-MM-DD"
       - <meta property="article:modified_time" content="YYYY-MM-DD"/>
       - flagship byline <time datetime="YYYY-MM-DD">Month DD, YYYY</time>
       - methodology "Last reviewed" <time datetime="YYYY-MM-DD">...
     Preserves datePublished / article:published_time / visible
     "Published Month DD, YYYY" — those are the real first-publish
     date and must not drift.

  2. Regenerate sitemap.xml from scripts/sitemap_urls.py, using git's
     last-commit date for each source file as <lastmod>. Files never
     committed fall back to today.

  3. Sanity check: every HTML file in dist/ must either be in the
     sitemap URL map or in EXCLUDED_FROM_SITEMAP. Otherwise fail loud.

Usage:

  # Refresh only files that are staged for commit (the pre-commit-hook path):
  python3 scripts/refresh_dates.py --staged

  # Refresh every HTML in dist/ (useful once after adding a page):
  python3 scripts/refresh_dates.py --all

  # Dry run, shows what would change, exits 1 if anything would change:
  python3 scripts/refresh_dates.py --check

The script is designed to be fast (no BeautifulSoup, pure regex) and
deterministic (idempotent on a clean tree).
"""

import argparse
import datetime as dt
import os
import re
import subprocess
import sys
from pathlib import Path

# Allow importing sitemap_urls.py regardless of how the script is invoked.
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from sitemap_urls import URL_MAP, EXCLUDED_FROM_SITEMAP, SITE_BASE  # noqa: E402

DIST_DIR = SCRIPT_DIR.parent  # dist/
TODAY = dt.date.today()
TODAY_ISO = TODAY.isoformat()                # 2026-04-23
TODAY_LONG = TODAY.strftime("%B %-d, %Y")     # April 23, 2026

# ---- Regex patterns for freshness fields ---------------------------------

# Each pattern below targets exactly one field shape. Do not make these
# greedy; we only replace dates, never surrounding markup.

# Visible "Last updated April 22, 2026." in paragraph footer.
PAT_FOOTER_LAST_UPDATED = re.compile(
    r"(<strong>Last updated</strong>\s+)[A-Z][a-z]+\s+\d{1,2},\s*\d{4}",
)

# Visible "Last updated <time datetime='...'>April 22, 2026</time>" byline.
PAT_BYLINE_TIME = re.compile(
    r'(Last updated\s+<time datetime=")\d{4}-\d{2}-\d{2}(">)[A-Z][a-z]+\s+\d{1,2},\s*\d{4}(</time>)',
)

# Visible "Last reviewed <time datetime='...'>April 22, 2026</time>" on methodology.
PAT_LAST_REVIEWED_TIME = re.compile(
    r'(<time datetime=")\d{4}-\d{2}-\d{2}(">Last reviewed\s+)[A-Z][a-z]+\s+\d{1,2},\s*\d{4}(</time>)',
)

# JSON-LD "dateModified":"2026-04-22"
PAT_JSONLD_DATE_MODIFIED = re.compile(r'("dateModified":")\d{4}-\d{2}-\d{2}(")')

# JSON-LD "lastReviewed":"2026-04-22"
PAT_JSONLD_LAST_REVIEWED = re.compile(r'("lastReviewed":")\d{4}-\d{2}-\d{2}(")')

# <meta property="article:modified_time" content="2026-04-22"/>
PAT_OG_MODIFIED_TIME = re.compile(
    r'(<meta property="article:modified_time" content=")\d{4}-\d{2}-\d{2}("/>)',
)

# Replacements ----------------------------------------------------------------

def bump_freshness(html: str) -> tuple[str, bool]:
    """
    Return (new_html, changed). Rewrites every freshness-date field to
    today's date. Preserves datePublished / Published lines untouched.
    """
    original = html

    html = PAT_FOOTER_LAST_UPDATED.sub(rf"\1{TODAY_LONG}", html)
    html = PAT_BYLINE_TIME.sub(rf"\g<1>{TODAY_ISO}\g<2>{TODAY_LONG}\g<3>", html)
    html = PAT_LAST_REVIEWED_TIME.sub(rf"\g<1>{TODAY_ISO}\g<2>{TODAY_LONG}\g<3>", html)
    html = PAT_JSONLD_DATE_MODIFIED.sub(rf"\g<1>{TODAY_ISO}\g<2>", html)
    html = PAT_JSONLD_LAST_REVIEWED.sub(rf"\g<1>{TODAY_ISO}\g<2>", html)
    html = PAT_OG_MODIFIED_TIME.sub(rf"\g<1>{TODAY_ISO}\g<2>", html)

    return html, html != original


# ---- Git helpers ---------------------------------------------------------

def git(*args: str) -> str:
    """Run git in DIST_DIR and return stdout (stripped)."""
    result = subprocess.run(
        ["git", *args],
        cwd=DIST_DIR,
        check=False,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def last_commit_date_iso(source_rel: str) -> str:
    """
    Return the ISO date of the last commit that touched the given file,
    relative to dist/. Falls back to today if the file has never been
    committed.
    """
    out = git("log", "-1", "--format=%cI", "--", source_rel)
    if not out:
        return TODAY_ISO
    # %cI gives 2026-04-23T16:28:00+02:00 — take the date portion only.
    return out[:10]


def staged_html_files() -> list[str]:
    """Return staged HTML files under dist/, as paths relative to dist/."""
    out = git("diff", "--cached", "--name-only", "--diff-filter=ACMR")
    files = [line for line in out.splitlines() if line.endswith(".html")]
    return files


def all_html_files() -> list[str]:
    """Return every HTML file under dist/, as paths relative to dist/."""
    paths = []
    for p in sorted(DIST_DIR.rglob("*.html")):
        if any(part in {"node_modules", ".git"} for part in p.parts):
            continue
        paths.append(str(p.relative_to(DIST_DIR)))
    return paths


# ---- Sitemap regeneration ------------------------------------------------

SITEMAP_HEADER = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
SITEMAP_FOOTER = '</urlset>\n'

def regenerate_sitemap() -> tuple[str, bool]:
    """Build sitemap.xml text from URL_MAP + git mtimes. Write it."""
    lines = [SITEMAP_HEADER]
    for entry in URL_MAP:
        source_rel = entry["source"]
        lastmod = last_commit_date_iso(source_rel)
        lines.append("  <url>\n")
        lines.append(f"    <loc>{SITE_BASE}{entry['url']}</loc>\n")
        lines.append(f"    <lastmod>{lastmod}</lastmod>\n")
        lines.append(f"    <changefreq>{entry['changefreq']}</changefreq>\n")
        lines.append(f"    <priority>{entry['priority']}</priority>\n")
        lines.append("  </url>\n")
    lines.append(SITEMAP_FOOTER)
    new_text = "".join(lines)

    sitemap_path = DIST_DIR / "sitemap.xml"
    old_text = sitemap_path.read_text() if sitemap_path.exists() else ""
    changed = new_text != old_text
    if changed:
        sitemap_path.write_text(new_text)
    return str(sitemap_path.relative_to(DIST_DIR)), changed


# ---- Sitemap coverage sanity check ---------------------------------------

def check_sitemap_coverage() -> list[str]:
    """
    Return a list of error strings. Empty list means OK. Every HTML file
    in dist/ must be in URL_MAP (by source path) or in EXCLUDED_FROM_SITEMAP.
    """
    errors: list[str] = []
    known_sources = {entry["source"] for entry in URL_MAP}
    for rel in all_html_files():
        if rel in known_sources:
            continue
        if rel in EXCLUDED_FROM_SITEMAP:
            continue
        errors.append(f"HTML file not mapped: {rel}. Add it to URL_MAP in sitemap_urls.py or EXCLUDED_FROM_SITEMAP.")
    return errors


# ---- Main ----------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser()
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--staged", action="store_true", help="only refresh files git has staged")
    group.add_argument("--all", action="store_true", help="refresh every HTML file under dist/")
    group.add_argument("--check", action="store_true", help="dry-run; exit 1 if anything would change")
    args = ap.parse_args()

    coverage_errors = check_sitemap_coverage()
    if coverage_errors:
        print("sitemap coverage errors:", file=sys.stderr)
        for e in coverage_errors:
            print(f"  - {e}", file=sys.stderr)
        return 2

    if args.staged:
        targets = [f for f in staged_html_files()]
    else:
        targets = all_html_files()

    any_change = False
    for rel in targets:
        path = DIST_DIR / rel
        if not path.exists():
            continue
        old = path.read_text()
        new, changed = bump_freshness(old)
        if changed:
            any_change = True
            if args.check:
                print(f"would refresh: {rel}")
            else:
                path.write_text(new)
                print(f"refreshed: {rel}")

    sitemap_rel, sitemap_changed = (None, False)
    if not args.check:
        sitemap_rel, sitemap_changed = regenerate_sitemap()
        if sitemap_changed:
            any_change = True
            print(f"regenerated: {sitemap_rel}")
    else:
        # In check mode, compare the existing sitemap to what we'd regenerate.
        tmp_lines = [SITEMAP_HEADER]
        for entry in URL_MAP:
            lastmod = last_commit_date_iso(entry["source"])
            tmp_lines.append("  <url>\n")
            tmp_lines.append(f"    <loc>{SITE_BASE}{entry['url']}</loc>\n")
            tmp_lines.append(f"    <lastmod>{lastmod}</lastmod>\n")
            tmp_lines.append(f"    <changefreq>{entry['changefreq']}</changefreq>\n")
            tmp_lines.append(f"    <priority>{entry['priority']}</priority>\n")
            tmp_lines.append("  </url>\n")
        tmp_lines.append(SITEMAP_FOOTER)
        existing = (DIST_DIR / "sitemap.xml").read_text() if (DIST_DIR / "sitemap.xml").exists() else ""
        if "".join(tmp_lines) != existing:
            any_change = True
            print("would regenerate: sitemap.xml")

    if args.check and any_change:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
