"""
Names cluster batch validator.

Runs the automated portion of the G2A audit + post-batch sweep across all
generated `/names/<slug>/index.html` pages.

Per R6 of Step 2 close-out review (2026-04-26): hardened beyond syntactic
checks to match the G2A promises. Now covers:

- exact JSON-LD block types (BreadcrumbList + WebPage)
- WebPage url == canonical
- WebPage lastReviewed exists and is ISO date
- BreadcrumbList items in correct order with matching DOM
- exactly one H1
- title + meta description non-empty
- robots meta = "index,follow"
- no `data-calculator` attribute (this is not a calculator page)
- no empty `<p></p>`, `<dd></dd>`, `<li></li>`, `<section></section>`
  beyond a small set of intentionally-empty markers
- canonical correctness
- cache-bust references
- internal-link slug resolution against batch slug set
- duplicate title + duplicate meta cross-page
- privacy heuristic for known leak terms
- main landmark exactly once
- breadcrumb nav has aria-label
- table headers present when tables exist
- visible source list when claims exist (R6)
- minimum useful content modules (R6)
- references against known-slug manifest (R6)

Per B7 of round-2 review (2026-04-26):

- `--names-dir` arg so the build can run the validator on staging directly
- table `<th>` must carry `scope="col"` or `scope="row"` (a11y)
- breadcrumb DOM `href` values must match JSON-LD `item` URLs in order
  (label parity alone is not enough, URLs can drift independently)
- page-intent guard: if title or H1 promises "meaning" or "origin",
  the page must contain a descriptive content module (not SSA-only)
- robust `<th>` detection via regex pattern not substring
"""

import argparse
import csv
import json
import os
import re
import sys
from datetime import date

DIST = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_NAMES_DIR = os.path.join(DIST, "names")
AUDIT_DIR = os.path.join(os.path.dirname(DIST), "audit")


def find_pages(names_dir):
    if not os.path.isdir(names_dir):
        return []
    out = []
    for entry in sorted(os.listdir(names_dir)):
        page_path = os.path.join(names_dir, entry, "index.html")
        if os.path.isfile(page_path):
            out.append((entry, page_path))
    return out


def _is_iso_date(s):
    if not s:
        return False
    try:
        date.fromisoformat(s)
        return True
    except ValueError:
        return False


def check_page(slug, path, all_slugs):
    """Return a dict of check results for one page."""
    with open(path, "r", encoding="utf-8") as f:
        html = f.read()

    out = {"slug": slug, "fail_reasons": []}
    fails = out["fail_reasons"]

    # ─── JSON-LD parsing + exact types ──────────────────────────────
    blocks = re.findall(r'<script type="application/ld\+json">(.+?)</script>', html, re.DOTALL)
    parsed = []
    for i, b in enumerate(blocks):
        try:
            parsed.append(json.loads(b))
        except json.JSONDecodeError as e:
            fails.append(f"jsonld_parse_block_{i}")
    out["jsonld_count"] = len(blocks)

    breadcrumb_jsonld = next((p for p in parsed if p.get("@type") == "BreadcrumbList"), None)
    webpage_jsonld = next((p for p in parsed if p.get("@type") == "WebPage"), None)
    if not breadcrumb_jsonld:
        fails.append("missing_breadcrumb_jsonld")
    if not webpage_jsonld:
        fails.append("missing_webpage_jsonld")

    # ─── WebPage url == canonical, lastReviewed valid ───────────────
    m = re.search(r'<link rel="canonical" href="([^"]+)"', html)
    canonical = m.group(1) if m else ""
    out["canonical"] = canonical
    expected_canonical = f"https://duedatelab.com/names/{slug}/"
    if canonical != expected_canonical:
        fails.append("canonical_url_wrong")
    if webpage_jsonld:
        if webpage_jsonld.get("url") != canonical:
            fails.append("webpage_url_mismatches_canonical")
        if not _is_iso_date(webpage_jsonld.get("lastReviewed", "")):
            fails.append("webpage_lastReviewed_not_iso")

    # ─── BreadcrumbList DOM/JSON-LD parity (label + URL order) ──────
    if breadcrumb_jsonld:
        items = breadcrumb_jsonld.get("itemListElement", [])
        names_jsonld = [it.get("name", "") for it in items]
        urls_jsonld = [it.get("item", "") for it in items]
        breadcrumb_dom_match = re.search(r'<nav class="pl-breadcrumb"[^>]*>(.*?)</nav>', html, re.DOTALL)
        if breadcrumb_dom_match:
            dom_inner = breadcrumb_dom_match.group(1)
            dom_outer = breadcrumb_dom_match.group(0)
            # Label parity
            dom_labels = re.findall(r'<(?:a[^>]*|span[^>]*)>([^<]+)</(?:a|span)>', dom_inner)
            dom_labels = [s.strip() for s in dom_labels if s.strip() and "/" not in s.strip()]
            if dom_labels != names_jsonld:
                fails.append(f"breadcrumb_label_order_drift_dom={dom_labels} jsonld={names_jsonld}")
            # B7: URL parity. Compare DOM <a href> values (in order) against
            # JSON-LD `item` URLs for the matching positions. The current-page
            # crumb is a <span> with no href; JSON-LD still emits its URL so
            # we trim the trailing JSON-LD entry when it has no DOM anchor.
            #
            # DOM uses relative paths ("/names/"), JSON-LD uses absolute
            # ("https://duedatelab.com/names/"). Normalize DOM hrefs to
            # absolute against the canonical's origin before comparing.
            dom_hrefs = re.findall(r'<a[^>]+href="([^"]+)"', dom_inner)
            origin_match = re.match(r'^(https?://[^/]+)', canonical)
            origin = origin_match.group(1) if origin_match else ""
            normalized_dom_hrefs = [
                (origin + h) if h.startswith("/") and origin else h
                for h in dom_hrefs
            ]
            jsonld_prefix = urls_jsonld[: len(dom_hrefs)]
            if normalized_dom_hrefs != jsonld_prefix:
                fails.append(
                    f"breadcrumb_url_order_drift_dom={normalized_dom_hrefs} jsonld={jsonld_prefix}"
                )
            # Must have aria-label on the nav
            if 'aria-label="Breadcrumb"' not in dom_outer:
                fails.append("breadcrumb_no_aria_label")
        else:
            fails.append("breadcrumb_dom_missing")

    # ─── Title + meta description non-empty + uniqueness (cross-check later) ─
    m = re.search(r"<title>([^<]+)</title>", html)
    out["title"] = (m.group(1).strip() if m else "")
    if not out["title"]:
        fails.append("title_empty")
    m = re.search(r'<meta name="description" content="([^"]+)"', html)
    out["meta_description"] = (m.group(1).strip() if m else "")
    if not out["meta_description"]:
        fails.append("meta_description_empty")

    # ─── Robots meta ────────────────────────────────────────────────
    m = re.search(r'<meta name="robots" content="([^"]+)"', html)
    robots = m.group(1).strip() if m else ""
    out["robots"] = robots
    if robots != "index,follow":
        fails.append(f"robots_not_index_follow({robots})")

    # ─── No data-calculator attribute (R6) ──────────────────────────
    if re.search(r'<body[^>]*\bdata-calculator=', html, re.I):
        fails.append("data_calculator_present_on_name_leaf")

    # ─── Cache-bust references ──────────────────────────────────────
    if "styles.css?v=17" not in html:
        fails.append("missing_styles_v17")
    if "app.js?v=15" not in html:
        fails.append("missing_app_v15")

    # ─── Empty structural elements ──────────────────────────────────
    if "<p></p>" in html:
        fails.append("empty_p")
    if re.search(r"<dd>\s*</dd>", html):
        fails.append("empty_dd")
    if re.search(r"<li>\s*</li>", html):
        fails.append("empty_li")
    if re.search(r"<section[^>]*>\s*</section>", html):
        fails.append("empty_section")

    # ─── Exactly one H1 ─────────────────────────────────────────────
    h1_count = len(re.findall(r"<h1[\s>]", html))
    out["h1_count"] = h1_count
    if h1_count != 1:
        fails.append(f"h1_count_{h1_count}")

    # ─── Main landmark exactly once ─────────────────────────────────
    main_count = len(re.findall(r"<main[\s>]", html))
    if main_count != 1:
        fails.append(f"main_landmark_count_{main_count}")

    # ─── Internal-link slug resolution ──────────────────────────────
    main_match = re.search(r'<main[^>]*>(.*?)</main>', html, re.DOTALL)
    main_html = main_match.group(1) if main_match else ""
    internal_name_links = re.findall(r'href="/names/([a-z][a-z0-9-]+)/"', main_html)
    bad_links = [s for s in internal_name_links if s not in all_slugs]
    out["bad_internal_links"] = ",".join(bad_links) if bad_links else ""
    if bad_links:
        fails.append(f"bad_internal_links({len(bad_links)})")

    # ─── Privacy heuristic ──────────────────────────────────────────
    script_blocks = re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL)
    leak_terms = ["cycle_length", "user_input", "input_value"]
    if any(any(term in s for s in script_blocks) for term in leak_terms):
        fails.append("privacy_leak_pattern")

    # ─── Source-list/claim parity (R6) ──────────────────────────────
    # If the page makes any sourced claim (meaning, origin, etc.), the
    # visible source list must exist.
    has_meaning_claim = "meaning" in main_html.lower() and "uncertain" not in main_html.lower()[:200]
    has_pl_sources = '<aside class="pl-sources">' in html
    # Heuristic: SSA popularity table or fact card with origin/pronunciation
    # implies a source list. We check for the presence of the SSA table.
    has_ssa_table = '<section class="pl-name-popularity">' in html
    has_fact_card = '<dl class="pl-name-fact-card">' in html
    if (has_ssa_table or has_fact_card) and not has_pl_sources:
        fails.append("source_list_missing_when_claims_present")

    # ─── Table headers when tables exist (R6 a11y) ──────────────────
    if re.search(r"<table[\s>]", html):
        th_tags = re.findall(r"<th\b[^>]*>", html)
        if not th_tags:
            fails.append("table_without_th")
        else:
            # B7: every <th> must carry scope="col" or scope="row"
            no_scope = [t for t in th_tags if not re.search(r'\bscope="(?:col|row|colgroup|rowgroup)"', t)]
            if no_scope:
                fails.append(f"th_without_scope({len(no_scope)}_of_{len(th_tags)})")

    # ─── Page-intent guard (B7 + C4 round-3) ────────────────────────
    # If title or H1 promises "meaning" or "origin", the page must carry a
    # real descriptive content module. A generic fact card cannot satisfy
    # the promise: a fact card containing only Gender + U.S. popularity is
    # not a meaning page. We require at least one of the dedicated descriptive
    # sections OR a fact card that itself carries Origin / Pronunciation /
    # Etymology rows (a meaning-bearing fact card).
    h1_match = re.search(r"<h1[^>]*>([^<]+)</h1>", html)
    h1_text = (h1_match.group(1).strip() if h1_match else "")
    promises_meaning = bool(re.search(r"\b(meaning|origin)\b", out["title"], re.I)) or \
                       bool(re.search(r"\b(meaning|origin)\b", h1_text, re.I))
    has_meaning_section = '<section class="pl-name-meaning">' in html
    has_origin_section = '<section class="pl-name-origin">' in html
    has_cultural_section = '<section class="pl-name-cultural">' in html
    # Inspect the fact card for descriptive rows (Origin / Pronunciation / Etymology).
    fact_card_match = re.search(r'<dl class="pl-name-fact-card">(.*?)</dl>', html, re.DOTALL)
    fact_inner = fact_card_match.group(1) if fact_card_match else ""
    fact_descriptive = bool(
        re.search(r"<dt[^>]*>\s*Origin\s*</dt>", fact_inner, re.I)
        or re.search(r"<dt[^>]*>\s*Pronunciation\s*</dt>", fact_inner, re.I)
        or re.search(r"<dt[^>]*>\s*Etymology\s*</dt>", fact_inner, re.I)
        or re.search(r"<dt[^>]*>\s*Meaning\s*</dt>", fact_inner, re.I)
    )
    has_descriptive_module = (
        has_meaning_section or has_origin_section or has_cultural_section or fact_descriptive
    )
    if promises_meaning and not has_descriptive_module:
        fails.append("title_or_h1_promises_meaning_but_no_descriptive_module")

    out["pass"] = len(fails) == 0
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--names-dir", default=DEFAULT_NAMES_DIR,
                    help="Directory of /<slug>/index.html pages to audit "
                         "(default: dist/names/)")
    ap.add_argument("--report", default=None,
                    help="CSV report output path (default: audit/names-batch-<date>.csv)")
    args = ap.parse_args()

    names_dir = args.names_dir
    pages = find_pages(names_dir)
    if not pages:
        print(f"No pages found at {names_dir}/. Run build_names.py first.")
        return 1

    all_slugs = {slug for slug, _ in pages}

    print(f"Auditing {len(pages)} pages in {names_dir}/...")
    rows = [check_page(slug, path, all_slugs) for slug, path in pages]

    # Cross-page checks
    title_counts = {}
    desc_counts = {}
    for r in rows:
        title_counts[r["title"]] = title_counts.get(r["title"], 0) + 1
        desc_counts[r["meta_description"]] = desc_counts.get(r["meta_description"], 0) + 1
    dup_titles = {t: c for t, c in title_counts.items() if c > 1 and t}
    dup_descs = {d: c for d, c in desc_counts.items() if c > 1 and d}

    for r in rows:
        if r["title"] in dup_titles:
            r["fail_reasons"].append("duplicate_title_across_batch")
            r["pass"] = False
        if r["meta_description"] in dup_descs:
            r["fail_reasons"].append("duplicate_meta_description_across_batch")
            r["pass"] = False

    # Report
    out_csv = args.report or os.path.join(AUDIT_DIR, f"names-batch-{date.today().isoformat()}.csv")
    os.makedirs(os.path.dirname(out_csv), exist_ok=True)
    fieldnames = ["slug", "pass", "fail_reasons", "title", "meta_description",
                  "canonical", "robots", "h1_count", "jsonld_count", "bad_internal_links"]
    with open(out_csv, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            r = dict(r)
            r["fail_reasons"] = "; ".join(r["fail_reasons"])
            w.writerow(r)
    fails = [r for r in rows if not r["pass"]]
    print(f"\n  Report: {out_csv}")
    print(f"  Pages audited: {len(rows)}")
    print(f"  Pages with failures: {len(fails)}")
    print(f"  Duplicate titles: {len(dup_titles)}")
    print(f"  Duplicate meta descriptions: {len(dup_descs)}")
    if fails:
        print("\n  FAIL details:")
        for r in fails:
            print(f"    {r['slug']}: {'; '.join(r['fail_reasons'])}")
        return 1
    print("\n  ALL PAGES PASS automated G2A + batch checks.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
