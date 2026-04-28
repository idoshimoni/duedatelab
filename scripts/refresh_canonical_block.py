"""
Refresh the canonical nav + drawer + footer block on every production page.

This script supersedes apply_canonical_block.py for incremental refreshes
where pages may already be in the new canonical state. It detects and
replaces the canonical block whether the page is in the legacy form or
in the current canonical form.

Per `feedback_canonical_block_rewrite.md`: rewrite the whole block from
the canonical_block template, never insert surgically.

Run:
    python3 scripts/refresh_canonical_block.py
"""

import os
import re
import sys

DIST = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from canonical_block import canonical_block
from sitemap_urls import URL_MAP


CALCULATOR_TOOLS = {
    "index.html":                 "due-date",
    "period-calculator.html":     "period",
    "ovulation-calculator.html":  "ovulation",
    "conception-calculator.html": "conception",
    "chinese-gender-chart.html":  "chinese-gender",
    "baby-percentile.html":       "baby-percentile",
    "sleep-needs-by-age.html":    "sleep-needs",
}


def _replace_header_block(html, desktop_header, mobile_header):
    """Replace from `<header class="pl-header"` through the FIRST </header>,
    then if a `<header class="pl-mobile-header"` follows, replace through
    its </header> too. Returns the new HTML and a count of headers replaced.
    """
    # Match desktop header from open tag through its closing </header>.
    desktop_pattern = re.compile(
        r'<header class="pl-header"[^>]*>.*?</header>',
        flags=re.DOTALL,
    )
    new_html, n_desktop = desktop_pattern.subn(desktop_header, html, count=1)
    if n_desktop == 0:
        return html, 0
    # If a mobile header sits immediately after (current canonical format),
    # replace it too. Otherwise the mobile_header was already inserted by
    # the desktop replacement above being followed by appended mobile.
    mobile_pattern = re.compile(
        r'<header class="pl-mobile-header"[^>]*>.*?</header>',
        flags=re.DOTALL,
    )
    new_html, n_mobile = mobile_pattern.subn(mobile_header, new_html, count=1)
    if n_mobile == 0:
        # Desktop replacement happened but no mobile header found, so we need
        # to inject the mobile header right after the new desktop header.
        new_html = new_html.replace(desktop_header, desktop_header + mobile_header, 1)
    return new_html, 1


def _replace_drawer(html, drawer):
    """Replace either `<nav id="mobile-navigation" class="pl-drawer" ...>...</nav>`
    (current canonical) or the legacy `<div class="pl-drawer" data-drawer>...</div>`."""
    # New canonical drawer (nav element).
    nav_pattern = re.compile(
        r'<nav[^>]*class="pl-drawer"[^>]*>.*?</nav>',
        flags=re.DOTALL,
    )
    new_html, n = nav_pattern.subn(drawer, html, count=1)
    if n > 0:
        return new_html, 1
    # Legacy drawer (div element).
    div_pattern = re.compile(
        r'<div class="pl-drawer" data-drawer>.*?</div>',
        flags=re.DOTALL,
    )
    new_html, n = div_pattern.subn(drawer, html, count=1)
    return new_html, 1 if n > 0 else 0


def _replace_footer(html, footer):
    """Replace `<footer class="pl-footer"...>...</footer>`."""
    footer_pattern = re.compile(
        r'<footer class="pl-footer"[^>]*>.*?</footer>',
        flags=re.DOTALL,
    )
    new_html, n = footer_pattern.subn(footer, html, count=1)
    return new_html, 1 if n > 0 else 0


def _add_data_calculator(html, tool):
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
    """Bump styles.css and app.js cache-bust to current targets.
        styles.css?v=23 (Amazon affiliate footer + card styles, 2026-04-27)
        app.js?v=17     (Amazon affiliate_click event, 2026-04-27)
    """
    n_styles = 0
    n_app = 0
    new = html
    new, c = re.subn(r'(/assets/styles\.css\?v=)(?:1[5-9]|2[0-2])(?=["\'?&])', r'\g<1>23', new)
    n_styles += c
    new, c = re.subn(r'(/assets/app\.js\?v=)(?:1[4-6])(?=["\'?&])', r'\g<1>17', new)
    n_app += c
    return new, n_styles, n_app


def main():
    targets = []
    for entry in URL_MAP:
        src = entry["source"]
        url = entry["url"]
        path = os.path.join(DIST, src)
        if not os.path.exists(path):
            print(f"  MISSING source file in URL_MAP: {src}")
            continue
        targets.append((path, url, src))
    path_404 = os.path.join(DIST, "404.html")
    if os.path.exists(path_404):
        targets.append((path_404, "/404", "404.html"))

    print(f"Refreshing canonical block on {len(targets)} pages...")
    n_changed = 0
    n_header = 0
    n_drawer = 0
    n_footer = 0
    n_calc = 0
    n_styles_bumped = 0
    n_app_bumped = 0
    failures = []

    for path, url, src in targets:
        with open(path, "r", encoding="utf-8") as f:
            html = f.read()
        original = html
        block = canonical_block(url)

        html, ok_header = _replace_header_block(
            html, block["desktop_header"], block["mobile_header"]
        )
        if ok_header:
            n_header += 1
        else:
            failures.append((src, "no header block found"))

        html, ok_drawer = _replace_drawer(html, block["drawer"])
        if ok_drawer:
            n_drawer += 1
        else:
            failures.append((src, "no drawer block found"))

        html, ok_footer = _replace_footer(html, block["footer"])
        if ok_footer:
            n_footer += 1
        else:
            failures.append((src, "no footer block found"))

        basename = os.path.basename(src) if "/" not in src else None
        if basename in CALCULATOR_TOOLS:
            html, ok_calc = _add_data_calculator(html, CALCULATOR_TOOLS[basename])
            if ok_calc:
                n_calc += 1

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
    print(f"  data-calculator added:   {n_calc}")
    print(f"  styles.css cache bumped: {n_styles_bumped}")
    print(f"  app.js cache bumped:     {n_app_bumped}")
    if failures:
        print("\n  FAILURES:")
        for src, msg in failures:
            print(f"    {src}: {msg}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
