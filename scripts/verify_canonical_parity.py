"""
Generate a machine-readable canonical-block parity report across every
production HTML page.

Per round-4 review §6 of `audit/reviews/ia-integration-2026-04-25-round4-review.md`:
the bundle reviewer asked for a structured parity report proving that
every URL_MAP page has the correct canonical block, active states,
cache-bust references, and tool data-calculator attributes.

Output: CSV at `audit/parity-2026-04-25.csv` plus a one-line summary
to stdout.

Columns (in order):
    source
    url
    has_desktop_header        new <header class="pl-header" role="banner">
    has_mobile_header         new <header class="pl-mobile-header" role="banner">
    has_new_drawer            new <nav id="mobile-navigation" ... data-pl-drawer>
    has_new_footer            new <footer class="pl-footer" role="contentinfo"> with 6 columns
    old_drawer_absent         no <div class="pl-drawer" data-drawer> markers
    old_toggle_absent         no data-drawer-toggle markers
    style_v16                 <link ... styles.css?v=16>
    app_v15                   <script ... app.js?v=15>
    body_data_calculator      data-calculator="X" on body, or "n/a" for non-tool pages
    desktop_current           number of aria-current="page" in desktop nav, or
                              "section-active" if the active state is is-section-active
    drawer_expanded           number of drawer sections with aria-expanded="true"
    drawer_current            number of aria-current="page" in drawer
    footer_current            number of aria-current="page" in footer

Run:
    python3 scripts/verify_canonical_parity.py
"""

import os
import re
import sys
import csv

DIST = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sitemap_urls import URL_MAP

# Pages that should carry a body data-calculator attribute. Others get "n/a".
CALCULATOR_TOOLS = {
    "/":                          "due-date",
    "/period-calculator":         "period",
    "/ovulation-calculator":      "ovulation",
    "/conception-calculator":     "conception",
    "/chinese-gender-chart":      "chinese-gender",
    "/baby-percentile":           "baby-percentile",
    "/sleep-needs-by-age":        "sleep-needs",
}


def _slice_section(html, start_marker, end_marker):
    s = html.find(start_marker)
    if s == -1:
        return ""
    e = html.find(end_marker, s)
    if e == -1:
        return html[s:]
    return html[s:e + len(end_marker)]


def _check_page(path, url):
    with open(path, "r", encoding="utf-8") as f:
        html = f.read()

    # Slice the canonical-block regions so we can score active state per region.
    desktop_section = _slice_section(html, '<header class="pl-header"', '</header>')
    mobile_section = _slice_section(html, '<header class="pl-mobile-header"', '</header>')
    drawer_section = _slice_section(html, '<nav id="mobile-navigation"', '</nav>')
    footer_section = _slice_section(html, '<footer class="pl-footer"', '</footer>')

    has_desktop_header = '<header class="pl-header" role="banner">' in html
    has_mobile_header = '<header class="pl-mobile-header" role="banner">' in html
    has_new_drawer = ('<nav id="mobile-navigation"' in html
                      and 'data-pl-drawer' in html
                      and 'class="pl-drawer-section"' in drawer_section)
    has_new_footer = ('<footer class="pl-footer" role="contentinfo">' in html
                      and footer_section.count('class="pl-footer-col') == 6)

    old_drawer_absent = ('<div class="pl-drawer" data-drawer>' not in html)
    old_toggle_absent = ('data-drawer-toggle' not in html)

    style_v16 = 'assets/styles.css?v=16' in html
    app_v15 = 'assets/app.js?v=15' in html

    expected_calc = CALCULATOR_TOOLS.get(url)
    body_dc = re.search(r'<body[^>]*\bdata-calculator="([^"]+)"', html, flags=re.I)
    if expected_calc:
        if body_dc:
            body_data_calculator = body_dc.group(1)
            if body_data_calculator != expected_calc:
                body_data_calculator = f"{body_data_calculator}!=expected:{expected_calc}"
        else:
            body_data_calculator = f"missing:expected={expected_calc}"
    else:
        body_data_calculator = "n/a" if not body_dc else f"unexpected:{body_dc.group(1)}"

    # desktop_current: count aria-current=page anchors in the desktop section,
    # or "section-active" if the bucket has is-section-active without a current
    # link (happens for child pages of a bucket).
    desktop_current_count = desktop_section.count('aria-current="page"')
    has_section_active = 'is-section-active' in desktop_section
    if desktop_current_count > 0:
        desktop_current = str(desktop_current_count)
    elif has_section_active:
        desktop_current = "section-active"
    else:
        desktop_current = "0"

    drawer_expanded = drawer_section.count('aria-expanded="true"')
    drawer_current = drawer_section.count('aria-current="page"')
    footer_current = footer_section.count('aria-current="page"')

    return {
        "source": os.path.relpath(path, DIST),
        "url": url,
        "has_desktop_header": has_desktop_header,
        "has_mobile_header": has_mobile_header,
        "has_new_drawer": has_new_drawer,
        "has_new_footer": has_new_footer,
        "old_drawer_absent": old_drawer_absent,
        "old_toggle_absent": old_toggle_absent,
        "style_v16": style_v16,
        "app_v15": app_v15,
        "body_data_calculator": body_data_calculator,
        "desktop_current": desktop_current,
        "drawer_expanded": drawer_expanded,
        "drawer_current": drawer_current,
        "footer_current": footer_current,
    }


def main():
    rows = []
    # Process every URL_MAP entry plus 404.html.
    pages = [(entry["source"], entry["url"]) for entry in URL_MAP]
    pages.append(("404.html", "/404"))

    for src, url in pages:
        path = os.path.join(DIST, src)
        if not os.path.exists(path):
            print(f"  MISSING: {src}")
            continue
        rows.append(_check_page(path, url))

    out_path = os.path.join(DIST, "..", "audit", "parity-2026-04-25.csv")
    out_path = os.path.abspath(out_path)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    fieldnames = list(rows[0].keys())
    with open(out_path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow(r)
    print(f"  Wrote parity report: {out_path}")
    print(f"  Pages reported: {len(rows)}")

    # Pass/fail summary on the structural columns.
    fails = []
    for r in rows:
        # Build a list of failing fields for this row.
        bad = []
        for k in ("has_desktop_header", "has_mobile_header", "has_new_drawer",
                  "has_new_footer", "old_drawer_absent", "old_toggle_absent",
                  "style_v16", "app_v15"):
            if r[k] is not True:
                bad.append(k)
        if isinstance(r["body_data_calculator"], str) and (
            r["body_data_calculator"].startswith("missing:")
            or r["body_data_calculator"].startswith("unexpected:")
            or "!=" in r["body_data_calculator"]
        ):
            bad.append("body_data_calculator")
        if bad:
            fails.append((r["source"], bad))

    if fails:
        print("\n  FAILS (structural):")
        for src, bad in fails:
            print(f"    {src}: {bad}")
        return 1
    print("\n  All structural columns PASS for all pages.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
