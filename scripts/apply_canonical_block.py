"""
Apply the canonical nav/drawer/footer block across the 30 production HTML pages.

Per `feedback_canonical_block_rewrite.md` and round-3 VERIFIED disposition on
the canonical block: the whole nav + drawer + footer block is rewritten from
the canonical_block template, never inserted surgically.

For each file, this script:
    1. Determines the public URL from the file path.
    2. Generates canonical_block(current_url).
    3. Replaces the existing OLD <header class="pl-header">...</header>
       with desktop_header + mobile_header.
    4. Replaces the existing OLD <div class="pl-drawer" data-drawer>...</div>
       with the new drawer.
    5. Replaces the existing OLD <footer class="pl-footer">...</footer>
       with the new footer.
    6. For the 7 tool pages, adds data-calculator="X" to <body>.
    7. Bumps the cache-bust query: styles.css?v=15 → ?v=16, app.js?v=14 → ?v=15.

Run:
    python3 scripts/apply_canonical_block.py
"""

import os
import re
import sys

DIST = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from canonical_block import canonical_block
from sitemap_urls import URL_MAP, EXCLUDED_FROM_SITEMAP


# Tool pages need a data-calculator body attribute so the v4 IIFE can fire
# the calculator_start event with the right tool name.
CALCULATOR_TOOLS = {
    "index.html":                 "due-date",
    "period-calculator.html":     "period",
    "ovulation-calculator.html":  "ovulation",
    "conception-calculator.html": "conception",
    "chinese-gender-chart.html":  "chinese-gender",
    "baby-percentile.html":       "baby-percentile",
    "sleep-needs-by-age.html":    "sleep-needs",
}


def _replace_block(html, pattern_open, pattern_close, replacement):
    """Replace the smallest substring from the first pattern_open match
    through the next pattern_close match with `replacement`.
    Both patterns are anchored as prefix matches on a literal string."""
    open_idx = html.find(pattern_open)
    if open_idx == -1:
        return html, False
    close_idx = html.find(pattern_close, open_idx)
    if close_idx == -1:
        return html, False
    end = close_idx + len(pattern_close)
    return html[:open_idx] + replacement + html[end:], True


def _replace_header(html, desktop_header, mobile_header):
    return _replace_block(
        html,
        '<header class="pl-header">',
        '</header>',
        desktop_header + mobile_header,
    )


def _replace_drawer(html, drawer):
    # The OLD production drawer is `<div class="pl-drawer" data-drawer>` ...
    # `</div>` (no nested divs inside, so we can safely match the next </div>).
    return _replace_block(
        html,
        '<div class="pl-drawer" data-drawer>',
        '</div>',
        drawer,
    )


def _replace_footer(html, footer):
    return _replace_block(
        html,
        '<footer class="pl-footer">',
        '</footer>',
        footer,
    )


def _add_data_calculator(html, tool):
    """Add data-calculator="<tool>" to the <body> tag. Idempotent: if any
    <body> tag already carries a data-calculator attribute, do nothing.
    Per round-4 review §7.1."""
    if re.search(r'<body[^>]*\bdata-calculator=', html, flags=re.I):
        return html, False
    new_html, n = re.subn(
        r'<body([^>]*)>',
        lambda m: f'<body data-calculator="{tool}"{m.group(1)}>',
        html,
        count=1,
    )
    return new_html, n > 0


def _bump_cachebust(html):
    """Bump styles.css and app.js cache-bust versions to current targets.
    Idempotent. Current targets:
        styles.css?v=23 (Amazon affiliate footer + card styles, 2026-04-27)
        app.js?v=17     (Amazon affiliate_click event, 2026-04-27)
    """
    n_styles = 0
    n_app = 0
    new = html
    # Bump any styles.css version 15-22 up to v=23.
    new, c = re.subn(r'(/assets/styles\.css\?v=)(?:1[5-9]|2[0-2])(?=["\'?&])', r'\g<1>23', new)
    n_styles += c
    # Bump any app.js version 14-16 up to v=17.
    new, c = re.subn(r'(/assets/app\.js\?v=)(?:1[4-6])(?=["\'?&])', r'\g<1>17', new)
    n_app += c
    return new, n_styles, n_app


def main():
    # Map each public URL to its source file.
    by_source = {entry["source"]: entry["url"] for entry in URL_MAP}

    # Walk every HTML in dist except 404 and the 4 hubs (which were generated
    # by build_hubs.py and are already canonical).
    targets = []
    for entry in URL_MAP:
        src = entry["source"]
        url = entry["url"]
        path = os.path.join(DIST, src)
        if not os.path.exists(path):
            print(f"  MISSING source file in URL_MAP: {src}")
            continue
        targets.append((path, url, src))

    # 404.html is in EXCLUDED_FROM_SITEMAP but still needs the canonical
    # block. Per round-4 review §4: the JS merge removed the old initDrawer,
    # so the 404 hamburger would silently break without canonicalization.
    path_404 = os.path.join(DIST, "404.html")
    if os.path.exists(path_404):
        targets.append((path_404, "/404", "404.html"))

    print(f"Applying canonical block to {len(targets)} production pages...")
    n_changed = 0
    n_header = 0
    n_drawer = 0
    n_footer = 0
    n_already_canonical = 0
    n_calc = 0
    n_styles_bumped = 0
    n_app_bumped = 0
    failures = []

    for path, url, src in targets:
        with open(path, "r", encoding="utf-8") as f:
            html = f.read()
        original = html
        block = canonical_block(url)

        # If the page is already canonical (has the new disclosure header
        # and v4 drawer), the OLD markers won't be found. That's not a
        # failure — it's idempotency. Detect this case so re-runs are safe.
        already_canonical = (
            'class="pl-header" role="banner"' in html
            and 'class="pl-mobile-header" role="banner"' in html
            and 'data-pl-drawer' in html
            and 'class="pl-footer-grid"' in html
        )

        html, ok_header = _replace_header(html, block["desktop_header"], block["mobile_header"])
        if ok_header:
            n_header += 1
        elif not already_canonical:
            failures.append((src, "no <header class=\"pl-header\"> block found"))

        html, ok_drawer = _replace_drawer(html, block["drawer"])
        if ok_drawer:
            n_drawer += 1
        elif not already_canonical:
            failures.append((src, "no <div class=\"pl-drawer\" data-drawer> block found"))

        html, ok_footer = _replace_footer(html, block["footer"])
        if ok_footer:
            n_footer += 1
        elif not already_canonical:
            failures.append((src, "no <footer class=\"pl-footer\"> block found"))

        if already_canonical and not (ok_header or ok_drawer or ok_footer):
            n_already_canonical += 1

        # Add data-calculator on tool pages (top-level files only — methodology
        # pages do NOT get data-calculator because the calculator JS is on the
        # tool pages, not the methodology pages).
        basename = os.path.basename(src) if "/" not in src else None
        if basename in CALCULATOR_TOOLS:
            html, ok_calc = _add_data_calculator(html, CALCULATOR_TOOLS[basename])
            if ok_calc:
                n_calc += 1

        # Cache-bust query bump.
        html, c_styles, c_app = _bump_cachebust(html)
        n_styles_bumped += c_styles
        n_app_bumped += c_app

        if html != original:
            with open(path, "w", encoding="utf-8") as f:
                f.write(html)
            n_changed += 1

    print(f"  Files changed:           {n_changed}/{len(targets)}")
    print(f"  Header blocks replaced:  {n_header}")
    print(f"  Drawer blocks replaced:  {n_drawer}")
    print(f"  Footer blocks replaced:  {n_footer}")
    print(f"  Already canonical:       {n_already_canonical} (idempotent re-run)")
    print(f"  data-calculator added:   {n_calc}")
    print(f"  styles.css ?v=15->16:    {n_styles_bumped}")
    print(f"  app.js ?v=14->15:        {n_app_bumped}")

    if failures:
        print("\n  FAILURES:")
        for src, msg in failures:
            print(f"    {src}: {msg}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
