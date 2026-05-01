"""
Canonical nav + drawer + footer block for DueDateLab.

Per `feedback_canonical_block_rewrite.md` and the v4 IA mock VERIFIED on
2026-04-25: every production HTML page renders the same nav/drawer/footer
markup, generated from this template, never inserted surgically.

Usage:
    from canonical_block import canonical_block
    html = canonical_block(current_url="/period-calculator")

Active-state rules:
    - The drawer priority link matching `current_url` gets aria-current="page".
    - The drawer section that contains `current_url` gets aria-expanded="true"
      and the matching <ul> has its `hidden` attribute removed.
    - The drawer sublink matching `current_url` gets aria-current="page",
      including section-hub "View all X" sublinks and Articles section sublinks.
    - The desktop top-level <li> whose dropdown contains `current_url` gets
      class="is-section-active" (drives the crimson underline).
    - The desktop dropdown <a> matching `current_url` gets aria-current="page",
      including section-hub "View all X" CTAs.
    - For direct top-level links (/ and /articles/), the <a> gets
      aria-current="page" when the URL matches. The Articles top-level <li>
      gets is-section-active when on /articles/, /articles/generations-by-year,
      or /methodology/.
    - Footer column links matching current_url get aria-current="page".
"""
from html import escape as html_escape
from urllib.parse import urlparse

# ─── Section + URL maps ─────────────────────────────────────────
# Each section is the bucket that owns a set of URLs. The drawer
# accordion section and the desktop dropdown share the same bucket.
SECTIONS = {
    "cycle-fertility": {
        "label": "Cycle & Fertility",
        "drawer_id": "drawer-cycle",
        "nav_id": "nav-cycle",
        "hub": "/cycle-and-fertility/",
        "tools": [
            ("/period-calculator",     "Period Calculator"),
            ("/ovulation-calculator",  "Ovulation Calculator"),
            ("/conception-calculator", "Conception Calculator"),
        ],
        "guides": [
            ("/articles/spotting-during-ovulation", "Spotting During Ovulation"),
            ("/articles/implantation-bleeding",     "Implantation Bleeding"),
        ],
        "reference": [],
    },
    "pregnancy": {
        "label": "Pregnancy",
        "drawer_id": "drawer-pregnancy",
        "nav_id": "nav-pregnancy",
        "hub": "/pregnancy/",
        "tools": [
            ("/chinese-gender-chart", "Chinese Gender Chart", "Entertainment"),
        ],
        "guides": [
            ("/articles/first-trimester-week-by-week", "First Trimester Week by Week"),
            ("/articles/due-date-vs-conception-date",  "Due Date vs Conception Date"),
        ],
        "reference": [
            ("/articles/chinese-gender-chart-accuracy", "Chinese Gender Chart Accuracy"),
        ],
    },
    "baby-child": {
        "label": "Baby & Child",
        "drawer_id": "drawer-baby-child",
        "nav_id": "nav-baby-child",
        "hub": "/baby-child/",
        "tools": [
            ("/baby-percentile",     "Baby Percentile Calculator"),
            ("/sleep-needs-by-age",  "Sleep Needs by Age"),
        ],
        "guides": [
            ("/articles/sleep-regressions-by-month", "Sleep Regressions by Month"),
            ("/articles/4-month-sleep-regression",   "4 Month Sleep Regression"),
            ("/articles/8-month-sleep-regression",   "8 Month Sleep Regression"),
            ("/articles/baby-percentile-explained",  "Baby Percentile Explained"),
        ],
        "reference": [],
    },
}

# Drawer "About" section (legal + company links).
ABOUT_SECTION = {
    "label": "About",
    "drawer_id": "drawer-about",
    "links": [
        ("/about",                 "About"),
        ("/privacy",               "Privacy"),
        ("/terms",                 "Terms"),
        ("/disclaimer",            "Disclaimer"),
        ("/affiliate-disclosure",  "Affiliate Disclosure"),
        ("/contact",               "Contact"),
    ],
}

# Drawer "Articles" section. The articles-bucket sublink only deep-links
# to /articles/; the topical articles already live in their own buckets.
ARTICLES_SECTION = {
    "drawer_id": "drawer-articles",
}

# Footer columns. Pulled out for readability and so the canonical_block
# function stays under 300 lines.
FOOTER_CALCULATORS = [
    ("/",                       "Due Date Calculator"),
    ("/period-calculator",      "Period Calculator"),
    ("/ovulation-calculator",   "Ovulation Calculator"),
    ("/conception-calculator",  "Conception Calculator"),
    ("/chinese-gender-chart",   "Chinese Gender Chart"),
    ("/baby-percentile",        "Baby Percentile Calculator"),
    ("/sleep-needs-by-age",     "Sleep Needs by Age"),
]

FOOTER_PREGNANCY = [
    ("/pregnancy/weeks-to-months/",              "Weeks to Months Calculator"),
    ("/articles/first-trimester-week-by-week",   "First Trimester Week by Week"),
    ("/articles/due-date-vs-conception-date",    "Due Date vs Conception Date"),
    ("/articles/chinese-gender-chart-accuracy",  "Chinese Gender Chart Accuracy"),
]

FOOTER_BABY_CHILD = [
    ("/articles/baby-percentile-explained",     "Baby Percentile Explained"),
    ("/articles/sleep-regressions-by-month",    "Sleep Regressions by Month"),
    ("/articles/4-month-sleep-regression",      "4 Month Sleep Regression"),
    ("/articles/8-month-sleep-regression",      "8 Month Sleep Regression"),
]

FOOTER_REFERENCE = [
    ("/articles/generations-by-year", "Generations by Year"),
    ("/articles/",                    "All articles"),
    ("/methodology/",                 "Methodology"),
]

FOOTER_COMPANY = [
    ("/about",                 "About"),
    ("/privacy",               "Privacy"),
    ("/terms",                 "Terms"),
    ("/disclaimer",            "Disclaimer"),
    ("/affiliate-disclosure",  "Affiliate Disclosure"),
    ("/contact",               "Contact"),
]


def _norm_url(value):
    """Normalize a URL value to its bare path with no trailing slash, except
    for the home page which stays as '/'. Strips scheme, host, query, fragment.
    A leading slash is added if missing, so callers passing relative paths
    such as 'period-calculator' still match the section map.
    Defensive against integration callers passing full URLs or query strings."""
    if not value:
        return "/"
    parsed = urlparse(value)
    if parsed.scheme or parsed.netloc:
        path = parsed.path or "/"
    else:
        path = value.split("?", 1)[0].split("#", 1)[0]
    if not path.startswith("/"):
        path = "/" + path
    return path.rstrip("/") or "/"


def _aria_current(url, current_url):
    """Return ' aria-current="page"' when url matches current_url, else empty."""
    return ' aria-current="page"' if _is_current(url, current_url) else ""


def _section_key_for_url(current_url):
    """Return the section key (cycle-fertility / pregnancy / baby-child / about /
    articles / None) that owns the given URL. Used to drive active state."""
    if not current_url:
        return None
    norm = _norm_url(current_url)
    # Direct mapping for tools and articles.
    for key, section in SECTIONS.items():
        for entry in section["tools"]:
            url = entry[0]
            if norm == url.rstrip("/"):
                return key
        for url, _ in section["guides"]:
            if norm == url.rstrip("/"):
                return key
        for url, _ in section["reference"]:
            if norm == url.rstrip("/"):
                return key
        if norm == section["hub"].rstrip("/"):
            return key
    # Methodology pages map to their tool's section.
    methodology_map = {
        "/methodology/period-calculator":     "cycle-fertility",
        "/methodology/ovulation-calculator":  "cycle-fertility",
        "/methodology/conception-calculator": "cycle-fertility",
        "/methodology/due-date-calculator":   None,  # / is direct-link, not a section
        "/methodology/chinese-gender-chart":  "pregnancy",
        "/methodology/baby-percentile":       "baby-child",
        "/methodology/sleep-needs-by-age":    "baby-child",
    }
    if norm in methodology_map:
        return methodology_map[norm]
    # About-bucket
    if norm in {"/about", "/privacy", "/terms", "/disclaimer", "/contact"}:
        return "about"
    # Articles direct link (/articles/) and methodology hub map to "articles" drawer.
    if norm in {"/articles", "/methodology", "/articles/generations-by-year"}:
        return "articles"
    # /calculators/ : drawer "All Calculators" priority link.
    if norm == "/calculators":
        return "all-calculators"
    return None


def _is_current(url, current_url):
    if not current_url or not url:
        return False
    return _norm_url(url) == _norm_url(current_url)


def _attr(name, value):
    """Helper to emit an HTML attribute only when value is truthy."""
    return f' {name}="{value}"' if value else ""


def _desktop_dropdown_item(item, current_url, nav_label):
    """Render one <li><a> inside a desktop dropdown panel."""
    if len(item) == 3:
        url, label, badge = item
    else:
        url, label = item
        badge = "Tool"
    aria_current = _aria_current(url, current_url)
    badge_class = ""
    if badge == "Article":
        badge_class = " badge-article"
    elif badge == "Entertainment":
        badge_class = " badge-entertainment"
    return (
        f'<li><a href="{url}" data-nav-area="desktop" data-nav-label="{nav_label}"'
        f'{aria_current}>'
        f'<span>{html_escape(label)}</span>'
        f'<span class="pl-badge{badge_class}">{html_escape(badge)}</span></a></li>'
    )


def _drawer_sublink(item, current_url, nav_label):
    """Render one drawer sublink <li><a>."""
    if len(item) == 3:
        url, label, badge = item
    else:
        url, label = item
        badge = None
    aria_current = _aria_current(url, current_url)
    badge_class = ""
    if badge == "Entertainment":
        badge_class = " badge-entertainment"
    elif badge == "Article":
        badge_class = " badge-article"
    badge_html = (
        f'<span class="pl-badge{badge_class}">{html_escape(badge)}</span>'
        if badge else ""
    )
    return (
        f'<li><a href="{url}" class="pl-drawer-sublink"'
        f' data-nav-area="drawer" data-nav-label="{nav_label}"{aria_current}>'
        f'<span>{html_escape(label)}</span>{badge_html}</a></li>'
    )


def _desktop_nav_section(key, section, active_section, current_url):
    """Render one top-level <li> with dropdown."""
    is_active = (key == active_section)
    li_class = "pl-nav-item is-section-active" if is_active else "pl-nav-item"
    items_html = []
    if section["tools"]:
        items_html.append('<li class="pl-dropdown-group-label">Tools</li>')
        for tool in section["tools"]:
            items_html.append(_desktop_dropdown_item(tool, current_url, key))
    if section["guides"]:
        items_html.append('<li class="pl-dropdown-divider" aria-hidden="true"></li>')
        items_html.append('<li class="pl-dropdown-group-label">Guides</li>')
        for guide in section["guides"]:
            items_html.append(
                _desktop_dropdown_item((guide[0], guide[1], "Article"), current_url, key)
            )
    if section["reference"]:
        items_html.append('<li class="pl-dropdown-divider" aria-hidden="true"></li>')
        items_html.append('<li class="pl-dropdown-group-label">Reference</li>')
        for ref in section["reference"]:
            items_html.append(
                _desktop_dropdown_item((ref[0], ref[1], "Article"), current_url, key)
            )
    items_html.append('<li class="pl-dropdown-divider" aria-hidden="true"></li>')
    hub_aria = _aria_current(section["hub"], current_url)
    items_html.append(
        f'<li><a href="{section["hub"]}" class="pl-dropdown-cta"'
        f' data-nav-area="desktop" data-nav-label="{key}"{hub_aria}>'
        f'<span>View all {html_escape(section["label"])}</span>'
        '<svg class="icon" width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true">'
        '<path d="M2.5 7h9M8 3.5 11.5 7 8 10.5" stroke="currentColor" stroke-width="1.6" '
        'stroke-linecap="round" stroke-linejoin="round"/></svg></a></li>'
    )
    items_html_str = "".join(items_html)
    return (
        f'<li class="{li_class}" data-pl-dropdown data-nav-label="{key}">'
        f'<button type="button" class="pl-nav-link" aria-expanded="false"'
        f' aria-controls="{section["nav_id"]}">{html_escape(section["label"])}'
        '<svg class="icon caret" width="10" height="10" viewBox="0 0 12 12" fill="none" aria-hidden="true">'
        '<path d="M2.5 4.5 L6 8 L9.5 4.5" stroke="currentColor" stroke-width="1.6" '
        'stroke-linecap="round" stroke-linejoin="round"/></svg>'
        '</button>'
        f'<ul id="{section["nav_id"]}" class="pl-dropdown" hidden>{items_html_str}</ul>'
        f'</li>'
    )


def _drawer_section(key, section, active_section, current_url):
    """Render one drawer accordion section."""
    is_active = (key == active_section)
    expanded = "true" if is_active else "false"
    hidden_attr = "" if is_active else " hidden"
    items = []
    for tool in section["tools"]:
        items.append(_drawer_sublink(tool, current_url, key))
    for guide in section["guides"]:
        items.append(_drawer_sublink(guide, current_url, key))
    for ref in section["reference"]:
        items.append(_drawer_sublink(ref, current_url, key))
    hub_aria = _aria_current(section["hub"], current_url)
    items.append(
        f'<li><a href="{section["hub"]}" class="pl-drawer-sublink"'
        f' data-nav-area="drawer" data-nav-label="{key}"{hub_aria}>'
        f'<span>View all {html_escape(section["label"])}</span></a></li>'
    )
    items_html = "".join(items)
    return (
        f'<div class="pl-drawer-section">'
        f'<button type="button" class="pl-drawer-section-header" aria-expanded="{expanded}"'
        f' aria-controls="{section["drawer_id"]}" data-section-label="{key}">'
        f'<span>{html_escape(section["label"])}</span>'
        '<svg class="icon chevron" width="12" height="12" viewBox="0 0 12 12" fill="none" aria-hidden="true">'
        '<path d="M4.5 2.5 L8 6 L4.5 9.5" stroke="currentColor" stroke-width="1.6" '
        'stroke-linecap="round" stroke-linejoin="round"/></svg>'
        '</button>'
        f'<ul id="{section["drawer_id"]}" class="pl-drawer-section-items"{hidden_attr}>'
        f'{items_html}</ul>'
        f'</div>'
    )


def _drawer_articles_section(active_section, current_url):
    """Articles drawer section: All articles + Generations + Methodology with
    aria-current="page" on the matching sublink."""
    is_active = (active_section == "articles")
    expanded = "true" if is_active else "false"
    hidden_attr = "" if is_active else " hidden"

    def _article_drawer_link(url, label):
        aria = _aria_current(url, current_url)
        return (
            f'<li><a href="{url}" class="pl-drawer-sublink" '
            f'data-nav-area="drawer" data-nav-label="articles"{aria}>'
            f'<span>{html_escape(label)}</span></a></li>'
        )

    return (
        f'<div class="pl-drawer-section">'
        f'<button type="button" class="pl-drawer-section-header" aria-expanded="{expanded}"'
        f' aria-controls="{ARTICLES_SECTION["drawer_id"]}" data-section-label="articles">'
        '<span>Articles</span>'
        '<svg class="icon chevron" width="12" height="12" viewBox="0 0 12 12" fill="none" aria-hidden="true">'
        '<path d="M4.5 2.5 L8 6 L4.5 9.5" stroke="currentColor" stroke-width="1.6" '
        'stroke-linecap="round" stroke-linejoin="round"/></svg>'
        '</button>'
        f'<ul id="{ARTICLES_SECTION["drawer_id"]}" class="pl-drawer-section-items"{hidden_attr}>'
        + _article_drawer_link("/articles/", "All articles")
        + _article_drawer_link("/articles/generations-by-year", "Generations by Year")
        + _article_drawer_link("/methodology/", "Methodology")
        + '</ul>'
        '</div>'
    )


def _drawer_about_section(active_section, current_url):
    is_active = (active_section == "about")
    expanded = "true" if is_active else "false"
    hidden_attr = "" if is_active else " hidden"
    items = []
    for url, label in ABOUT_SECTION["links"]:
        aria_current = _aria_current(url, current_url)
        items.append(
            f'<li><a href="{url}" class="pl-drawer-sublink" data-nav-area="drawer" data-nav-label="about"'
            f'{aria_current}><span>{html_escape(label)}</span></a></li>'
        )
    items_html = "".join(items)
    return (
        f'<div class="pl-drawer-section">'
        f'<button type="button" class="pl-drawer-section-header" aria-expanded="{expanded}"'
        f' aria-controls="{ABOUT_SECTION["drawer_id"]}" data-section-label="about">'
        '<span>About</span>'
        '<svg class="icon chevron" width="12" height="12" viewBox="0 0 12 12" fill="none" aria-hidden="true">'
        '<path d="M4.5 2.5 L8 6 L4.5 9.5" stroke="currentColor" stroke-width="1.6" '
        'stroke-linecap="round" stroke-linejoin="round"/></svg>'
        '</button>'
        f'<ul id="{ABOUT_SECTION["drawer_id"]}" class="pl-drawer-section-items"{hidden_attr}>'
        f'{items_html}</ul>'
        f'</div>'
    )


# ─── Brand block (preserved from production: SVG mark + text) ───
def _brand_logo(extra_class=""):
    cls = f"ddl-logo pl-logo{(' ' + extra_class) if extra_class else ''}"
    return (
        f'<a class="{cls}" href="/" aria-label="DueDateLab home" data-pl-logo>'
        '<svg class="ddl-logo-mark" width="32" height="32" viewBox="0 0 64 64" '
        'aria-hidden="true" focusable="false">'
        '<path d="M8 46 Q 22 46, 28 32 T 50 14" stroke="currentColor" stroke-width="5" '
        'stroke-linecap="round" fill="none"/>'
        '<circle cx="50" cy="14" r="6" fill="#EC0D5C"/>'
        '<circle cx="8" cy="46" r="3.5" fill="currentColor"/>'
        '</svg>'
        '<span>DueDate<em>Lab</em></span>'
        '</a>'
    )


def _footer_col(label, items, current_url, footer_section, cta=None):
    def _li(url, text):
        aria = _aria_current(url, current_url)
        return (
            f'<li><a href="{url}" data-footer-section="{footer_section}"{aria}>'
            f'{html_escape(text)}</a></li>'
        )
    list_html = "".join(_li(url, text) for url, text in items)
    cta_html = ""
    if cta:
        cta_url, cta_text = cta
        cta_aria = _aria_current(cta_url, current_url)
        cta_html = (
            f'<a href="{cta_url}" class="pl-footer-cta" data-footer-section="{footer_section}"{cta_aria}>'
            f'{html_escape(cta_text)} '
            '<svg class="icon" width="12" height="12" viewBox="0 0 14 14" fill="none" aria-hidden="true">'
            '<path d="M2.5 7h9M8 3.5 11.5 7 8 10.5" stroke="currentColor" stroke-width="1.6" '
            'stroke-linecap="round" stroke-linejoin="round"/></svg></a>'
        )
    return (
        f'<div class="pl-footer-col">'
        f'<h4>{html_escape(label)}</h4>'
        f'<ul>{list_html}</ul>'
        f'{cta_html}'
        f'</div>'
    )


def canonical_block(current_url):
    """Return the canonical desktop nav + mobile header + drawer + footer
    HTML for a page at `current_url`."""
    current_url = _norm_url(current_url) if current_url else "/"
    active_section = _section_key_for_url(current_url)

    # Home top-level: aria-current only when literally on /, never on a tool/article.
    home_aria = _aria_current("/", current_url)

    # Articles top-level: aria-current only when literally on /articles/.
    # is-section-active fires on /articles/, /articles/generations-by-year,
    # and /methodology/ to give desktop users a section cue without
    # mismarking child pages as the current page.
    articles_aria = _aria_current("/articles/", current_url)
    articles_li_class = (
        "pl-nav-item is-section-active"
        if active_section == "articles"
        else "pl-nav-item"
    )

    desktop_sections_html = "".join(
        _desktop_nav_section(key, SECTIONS[key], active_section, current_url)
        for key in ("cycle-fertility", "pregnancy", "baby-child")
    )

    desktop_header = (
        '<header class="pl-header" role="banner">'
        f'{_brand_logo()}'
        '<nav class="pl-nav" aria-label="Main">'
        '<ul class="pl-nav-list">'
        f'<li class="pl-nav-item">'
        f'<a href="/" class="pl-nav-link"{home_aria} data-nav-label="due-date" data-nav-area="desktop">Due Date</a>'
        '</li>'
        f'{desktop_sections_html}'
        f'<li class="{articles_li_class}">'
        f'<a href="/articles/" class="pl-nav-link"{articles_aria} data-nav-label="articles" data-nav-area="desktop">Articles</a>'
        '</li>'
        '</ul>'
        '</nav>'
        '</header>'
    )

    mobile_header = (
        '<header class="pl-mobile-header" role="banner">'
        f'{_brand_logo()}'
        '<button type="button" class="pl-hamburger" data-pl-hamburger '
        'aria-label="Open navigation" aria-expanded="false" aria-controls="mobile-navigation">'
        '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
        'stroke-width="2" stroke-linecap="round" aria-hidden="true">'
        '<line x1="3" y1="6" x2="21" y2="6"/>'
        '<line x1="3" y1="12" x2="21" y2="12"/>'
        '<line x1="3" y1="18" x2="21" y2="18"/>'
        '</svg>'
        '</button>'
        '</header>'
    )

    # Drawer priority links: Due Date Calculator (always to /), All Calculators
    # (to /calculators/). The matching one gets aria-current="page".
    duedate_pri_aria = _aria_current("/", current_url)
    allcalcs_pri_aria = _aria_current("/calculators/", current_url)
    drawer_priority = (
        '<div class="pl-drawer-priority">'
        f'<a href="/" class="pl-drawer-link"{duedate_pri_aria} data-nav-area="drawer" data-nav-label="due-date">Due Date Calculator</a>'
        f'<a href="/calculators/" class="pl-drawer-link"{allcalcs_pri_aria} data-nav-area="drawer" data-nav-label="all-calculators">All Calculators</a>'
        '</div>'
    )

    drawer_sections_html = "".join(
        _drawer_section(key, SECTIONS[key], active_section, current_url)
        for key in ("cycle-fertility", "pregnancy", "baby-child")
    )
    drawer_articles_html = _drawer_articles_section(active_section, current_url)
    drawer_about_html = _drawer_about_section(active_section, current_url)

    drawer = (
        '<nav id="mobile-navigation" class="pl-drawer" aria-label="Mobile navigation" '
        'data-pl-drawer hidden>'
        f'{drawer_priority}'
        '<div class="pl-drawer-divider" aria-hidden="true"></div>'
        f'{drawer_sections_html}'
        f'{drawer_articles_html}'
        f'{drawer_about_html}'
        '</nav>'
    )

    footer = (
        '<footer class="pl-footer" role="contentinfo">'
        '<div class="pl-footer-grid">'
        '<div class="pl-footer-col pl-footer-brand">'
        f'{_brand_logo("pl-footer-logo")}'
        '<p>Free, private, evidence-based pregnancy and parenting calculators.</p>'
        '<p class="legal">© 2026 DueDateLab. Not medical advice.</p>'
        '<p class="legal pl-footer-affiliate">As an Amazon Associate, '
        'DueDateLab earns from qualifying purchases.</p>'
        '</div>'
        + _footer_col("Calculators", FOOTER_CALCULATORS, current_url, "calculators",
                      cta=("/calculators/", "All Calculators"))
        + _footer_col("Pregnancy", FOOTER_PREGNANCY, current_url, "pregnancy")
        + _footer_col("Baby & Child", FOOTER_BABY_CHILD, current_url, "baby-child")
        + _footer_col("Reference", FOOTER_REFERENCE, current_url, "reference")
        + _footer_col("Company", FOOTER_COMPANY, current_url, "company")
        + '</div>'
        + '<div class="pl-footer-bottom">'
        + '<span>Privacy-first tools. Informational only — '
        + '<a href="/disclaimer">not medical advice</a>.</span>'
        + '<span>Made with care.</span>'
        + '</div>'
        '</footer>'
    )

    return {
        "desktop_header": desktop_header,
        "mobile_header": mobile_header,
        "drawer": drawer,
        "footer": footer,
    }


if __name__ == "__main__":
    # Smoke test: emit the canonical block for / and verify it parses.
    import sys
    block = canonical_block("/")
    out = block["desktop_header"] + "\n" + block["mobile_header"] + "\n" + block["drawer"] + "\n" + block["footer"]
    print(f"Total bytes: {len(out)}")
    print(f"Contains 'pl-nav': {'pl-nav' in out}")
    print(f"Contains 'data-pl-hamburger': {'data-pl-hamburger' in out}")
    print(f"Contains 'data-pl-drawer': {'data-pl-drawer' in out}")
    print(f"Contains 6 footer columns: {out.count('pl-footer-col') == 6}")
    needle = 'data-nav-label="due-date" data-nav-area="desktop">Due Date</a>'
    print(f"Home Due-Date anchor present: {needle in out}")
    aria_needle = 'aria-current="page" data-nav-label="due-date"'
    print(f"Home aria-current set: {aria_needle in out}")
    sys.exit(0)
