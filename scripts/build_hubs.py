"""
Build the 4 IA-restructure hub pages from a single template.

Per v4 IA mock VERIFIED on 2026-04-25 (PI2): /calculators/, /pregnancy/,
/cycle-and-fertility/, /baby-child/ must return useful 200 pages in the
same release as the IA restructure, or links must be hidden until live.

Hub copy should stay source-claim-light. Any sourced specifics should
live on the destination article or methodology page, or be visibly
supported here.

Run:
    python3 scripts/build_hubs.py
"""

import os
import json
from html import escape as html_escape
from canonical_block import canonical_block, SECTIONS

DIST = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ─── Schema helpers ─────────────────────────────────────────────
SITE_BASE = "https://duedatelab.com"
PUBLISHER = {
    "@type": "Organization",
    "name": "DueDateLab",
    "url": SITE_BASE + "/",
    "logo": {
        "@type": "ImageObject",
        "url": SITE_BASE + "/assets/duedatelab-mark-512.png",
        "width": 512,
        "height": 512,
    },
}

# Tool descriptions used on hub cards. Kept short, source-claim-free —
# any sourced specifics live on the methodology pages those cards link to.
TOOL_DESCRIPTIONS = {
    "/":                       "Estimate your due date from your last period, conception date, or a known due date.",
    "/period-calculator":      "Predict your next period and see your cycle on a calendar.",
    "/ovulation-calculator":   "Estimate your ovulation day and fertile window from your LMP and cycle length.",
    "/conception-calculator":  "Estimate when you conceived from a due date or LMP, with cycle adjustment.",
    "/chinese-gender-chart":   "Lunar-age novelty chart for entertainment, not a clinical predictor.",
    "/baby-percentile":        "Estimate growth percentiles for weight, length, and head circumference, 0 to 5 years. See methodology for source details.",
    "/sleep-needs-by-age":     "Look up sleep ranges by age, 0 to 18 years. See methodology for source details.",
}

# Article descriptions for hub guides cards. Source names removed unless
# the linked article itself cites them visibly.
ARTICLE_DESCRIPTIONS = {
    "/articles/first-trimester-week-by-week":   "Symptoms, milestones, and what to ask your clinician through weeks 1 to 13.",
    "/articles/due-date-vs-conception-date":    "Why LMP-based due dates and conception-based estimates can point to different dates.",
    "/articles/chinese-gender-chart-accuracy":  "How accurate the Chinese Gender Chart is, and why it should be treated as entertainment.",
    "/articles/sleep-regressions-by-month":     "What sleep regressions are, what triggers them, and what actually helps.",
    "/articles/4-month-sleep-regression":       "How sleep architecture changes around 4 months and what helps.",
    "/articles/8-month-sleep-regression":       "Separation anxiety, motor milestones, and second-half-of-year sleep changes.",
    "/articles/baby-percentile-explained":      "How growth percentiles are calculated and why a single number is not a verdict.",
    "/articles/generations-by-year":            "Generation labels by birth year, with named-period boundaries explained.",
}

# Methodology card descriptions. Kept short and methodology-routed.
METHODOLOGY_DESCRIPTIONS = {
    "/methodology/":                           "See how DueDateLab calculates results and handles source notes.",
    "/methodology/period-calculator":          "Review assumptions, cycle inputs, and source notes for the Period Calculator.",
    "/methodology/ovulation-calculator":       "Review fertile-window assumptions and source notes for the Ovulation Calculator.",
    "/methodology/conception-calculator":      "Review conception-window assumptions and source notes for the Conception Calculator.",
    "/methodology/due-date-calculator":        "Review due-date assumptions, inputs, and source notes.",
    "/methodology/chinese-gender-chart":       "Review how the novelty chart is calculated and why it is not clinical.",
    "/methodology/baby-percentile":            "Review growth-percentile assumptions and source notes.",
    "/methodology/sleep-needs-by-age":         "Review sleep-range assumptions and source notes.",
}


def _hub_card(url, label, desc, badge=None):
    """One card in a hub-page section grid. Renders no <p> when desc is empty,
    so methodology cards do not emit a stray empty paragraph."""
    badge_html = ""
    if badge:
        cls = ""
        if badge == "Tool":
            cls = ""
        elif badge == "Article":
            cls = " badge-article"
        elif badge == "Entertainment":
            cls = " badge-entertainment"
        from html import escape as _esc
        badge_html = f'<span class="pl-hub-card-badge pl-badge{cls}">{_esc(badge)}</span>'
    from html import escape as _esc
    desc_html = f'<p>{_esc(desc)}</p>' if desc else ''
    return (
        f'<a class="pl-hub-card" href="{url}">'
        f'<div class="pl-hub-card-head"><h3>{_esc(label)}</h3>{badge_html}</div>'
        f'{desc_html}'
        f'<span class="pl-hub-card-cta">Open</span>'
        f'</a>'
    )


def _hub_section(title, items, kind):
    """One <section> with a grid of cards. items is a list of tuples
    (url, label) or (url, label, badge_override)."""
    cards = []
    for entry in items:
        if len(entry) == 3:
            url, label, badge = entry
        else:
            url, label = entry
            badge = "Tool" if kind == "tool" else "Article" if kind == "article" else None
        if kind == "tool":
            desc = TOOL_DESCRIPTIONS.get(url, "")
        elif kind == "article":
            desc = ARTICLE_DESCRIPTIONS.get(url, "")
        elif kind == "link":
            # Methodology cards: pull from the methodology dictionary so they
            # never render an empty <p>.
            desc = METHODOLOGY_DESCRIPTIONS.get(url, "")
        else:
            desc = ""
        cards.append(_hub_card(url, label, desc, badge=badge))
    cards_html = "".join(cards)
    return (
        f'<section class="pl-hub-section">'
        f'<h2>{html_escape(title)}</h2>'
        f'<div class="pl-hub-grid">{cards_html}</div>'
        f'</section>'
    )


def _breadcrumb_jsonld(items):
    """items: [(name, url), ...]. URLs are absolute."""
    return {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": i + 1,
                "name": name,
                "item": url,
            }
            for i, (name, url) in enumerate(items)
        ],
    }


def _collection_jsonld(name, url, description, has_part_urls):
    return {
        "@context": "https://schema.org",
        "@type": "CollectionPage",
        "name": name,
        "description": description,
        "url": url,
        "inLanguage": "en",
        "lastReviewed": "2026-04-25",
        "publisher": PUBLISHER,
        "hasPart": [
            {"@type": "WebPage", "url": SITE_BASE + u} for u in has_part_urls
        ],
    }


def _breadcrumb_dom(items):
    """items: [(label, url_or_none), ...]. Last item has url=None for current page."""
    parts = []
    for i, (label, url) in enumerate(items):
        if url:
            parts.append(f'<a href="{url}">{html_escape(label)}</a>')
        else:
            parts.append(f'<span aria-current="page">{html_escape(label)}</span>')
    return (
        '<nav class="pl-breadcrumb" aria-label="Breadcrumb">'
        + ' <span class="pl-breadcrumb-sep" aria-hidden="true">/</span> '.join(parts)
        + '</nav>'
    )


def render_hub(current_url, title_full, h1, intro, sections, breadcrumb_label):
    """Render a hub-page HTML document."""
    block = canonical_block(current_url)
    breadcrumbs_dom = _breadcrumb_dom([
        ("Home", "/"),
        (breadcrumb_label, None),
    ])
    canonical = SITE_BASE + current_url

    # Schema
    has_part = []
    for sec in sections:
        for entry in sec["items"]:
            has_part.append(entry[0])
    breadcrumb_schema = _breadcrumb_jsonld([
        ("Home", SITE_BASE + "/"),
        (breadcrumb_label, canonical),
    ])
    collection_schema = _collection_jsonld(
        name=h1,
        url=canonical,
        description=intro,
        has_part_urls=has_part,
    )

    sections_html = "".join(_hub_section(s["title"], s["items"], s["kind"]) for s in sections)

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<!-- pl-seo-block -->
<link rel="canonical" href="{canonical}"/>
<meta name="robots" content="index,follow"/>
<link rel="icon" href="/favicon.svg" type="image/svg+xml"/>
<link rel="icon" href="/favicon-32.png" type="image/png" sizes="32x32"/>
<link rel="icon" href="/favicon-16.png" type="image/png" sizes="16x16"/>
<link rel="apple-touch-icon" href="/apple-touch-icon-180.png"/>
<link rel="icon" href="/favicon.ico" sizes="any"/>
<link rel="manifest" href="/site.webmanifest"/>
<meta name="theme-color" content="#1A2E4A"/>
<meta property="og:type" content="website"/>
<meta property="og:title" content="{html_escape(title_full, quote=True)}"/>
<meta property="og:description" content="{html_escape(intro, quote=True)}"/>
<meta property="og:url" content="{canonical}"/>
<meta property="og:image" content="{SITE_BASE}/og-image.png"/>
<meta property="og:image:width" content="1200"/>
<meta property="og:image:height" content="630"/>
<meta property="og:image:alt" content="DueDateLab, free, private pregnancy and parenting calculators"/>
<meta property="og:site_name" content="DueDateLab"/>
<meta property="og:locale" content="en_US"/>
<meta property="og:locale:alternate" content="en_GB"/>
<meta property="og:locale:alternate" content="en_BE"/>
<meta name="twitter:card" content="summary_large_image"/>
<meta name="twitter:title" content="{html_escape(title_full, quote=True)}"/>
<meta name="twitter:description" content="{html_escape(intro, quote=True)}"/>
<meta name="twitter:image" content="{SITE_BASE}/og-image.png"/>
<script type="application/ld+json">{json.dumps(collection_schema, separators=(",", ":"))}</script>
<script type="application/ld+json">{json.dumps(breadcrumb_schema, separators=(",", ":"))}</script>
<!-- /pl-seo-block -->
<title>{html_escape(title_full)}</title>
<meta name="description" content="{html_escape(intro, quote=True)}"/>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/assets/styles.css?v=17">
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-4285310692091665" crossorigin="anonymous"></script>
</head>
<body>
{block["desktop_header"]}
{block["mobile_header"]}
{block["drawer"]}

<main class="pl-page pl-hub">
  <div class="pl-hub-header">
    {breadcrumbs_dom}
    <h1 class="pl-h1">{html_escape(h1)}</h1>
    <p class="pl-hub-intro">{html_escape(intro)}</p>
    <p class="pl-byline" style="font-size:13px;color:#5A6B82;margin:0;line-height:1.5;">Last updated <time datetime="2026-04-25">April 25, 2026</time></p>
  </div>

  {sections_html}
</main>

{block["footer"]}

<script src="/assets/app.js?v=15"></script>
</body>
</html>
"""


# ─── Hub specs ─────────────────────────────────────────────────
HUBS = [
    {
        "url": "/calculators/",
        "path": "calculators/index.html",
        "title": "All Calculators · DueDateLab",
        "h1": "All DueDateLab calculators",
        "intro": "Free, private calculators for cycle timing, pregnancy dates, and baby growth and sleep.",
        "breadcrumb_label": "All Calculators",
        "sections": [
            {
                "title": "Cycle and Fertility",
                "kind": "tool",
                "items": [
                    ("/period-calculator",     "Period Calculator"),
                    ("/ovulation-calculator",  "Ovulation Calculator"),
                    ("/conception-calculator", "Conception Calculator"),
                ],
            },
            {
                "title": "Pregnancy",
                "kind": "tool",
                "items": [
                    ("/",                     "Due Date Calculator"),
                    ("/chinese-gender-chart", "Chinese Gender Chart", "Entertainment"),
                ],
            },
            {
                "title": "Baby and Child",
                "kind": "tool",
                "items": [
                    ("/baby-percentile",     "Baby Percentile Calculator"),
                    ("/sleep-needs-by-age",  "Sleep Needs by Age"),
                ],
            },
            {
                "title": "Methodology",
                "kind": "link",
                "items": [
                    ("/methodology/", "Read how we calculate", None),
                ],
            },
        ],
    },
    {
        "url": "/cycle-and-fertility/",
        "path": "cycle-and-fertility/index.html",
        "title": "Cycle and Fertility Tools · DueDateLab",
        "h1": "Cycle and fertility",
        "intro": "Tools to estimate period timing, ovulation, fertile window, and conception timing. Each calculator links to its methodology.",
        "breadcrumb_label": "Cycle and Fertility",
        "sections": [
            {
                "title": "Tools",
                "kind": "tool",
                "items": [
                    ("/period-calculator",     "Period Calculator"),
                    ("/ovulation-calculator",  "Ovulation Calculator"),
                    ("/conception-calculator", "Conception Calculator"),
                ],
            },
            {
                "title": "Methodology",
                "kind": "link",
                "items": [
                    ("/methodology/period-calculator",     "Period Calculator methodology", None),
                    ("/methodology/ovulation-calculator",  "Ovulation Calculator methodology", None),
                    ("/methodology/conception-calculator", "Conception Calculator methodology", None),
                ],
            },
        ],
    },
    {
        "url": "/pregnancy/",
        "path": "pregnancy/index.html",
        "title": "Pregnancy Tools and Guides · DueDateLab",
        "h1": "Pregnancy",
        "intro": "Pregnancy tools and guides, including due date estimates and a Chinese Gender Chart clearly labelled as entertainment.",
        "breadcrumb_label": "Pregnancy",
        "sections": [
            {
                "title": "Tools",
                "kind": "tool",
                "items": [
                    ("/",                      "Due Date Calculator"),
                    ("/chinese-gender-chart",  "Chinese Gender Chart", "Entertainment"),
                ],
            },
            {
                "title": "Guides",
                "kind": "article",
                "items": [
                    ("/articles/first-trimester-week-by-week",  "First Trimester Week by Week"),
                    ("/articles/due-date-vs-conception-date",   "Due Date vs Conception Date"),
                    ("/articles/chinese-gender-chart-accuracy", "Chinese Gender Chart Accuracy"),
                ],
            },
            {
                "title": "Methodology",
                "kind": "link",
                "items": [
                    ("/methodology/due-date-calculator",  "Due Date Calculator methodology", None),
                    ("/methodology/chinese-gender-chart", "Chinese Gender Chart methodology", None),
                ],
            },
        ],
    },
    {
        "url": "/baby-child/",
        "path": "baby-child/index.html",
        "title": "Baby and Child Tools and Guides · DueDateLab",
        "h1": "Baby and child",
        "intro": "Baby and child tools plus sleep and growth guides. Each calculator links to its methodology and source notes.",
        "breadcrumb_label": "Baby and Child",
        "sections": [
            {
                "title": "Tools",
                "kind": "tool",
                "items": [
                    ("/baby-percentile",    "Baby Percentile Calculator"),
                    ("/sleep-needs-by-age", "Sleep Needs by Age"),
                ],
            },
            {
                "title": "Guides",
                "kind": "article",
                "items": [
                    ("/articles/baby-percentile-explained",   "Baby Percentile Explained"),
                    ("/articles/sleep-regressions-by-month",  "Sleep Regressions by Month"),
                    ("/articles/4-month-sleep-regression",    "4 Month Sleep Regression"),
                    ("/articles/8-month-sleep-regression",    "8 Month Sleep Regression"),
                ],
            },
            {
                "title": "Methodology",
                "kind": "link",
                "items": [
                    ("/methodology/baby-percentile",    "Baby Percentile methodology", None),
                    ("/methodology/sleep-needs-by-age", "Sleep Needs by Age methodology", None),
                ],
            },
        ],
    },
]


def main():
    for hub in HUBS:
        html = render_hub(
            current_url=hub["url"],
            title_full=hub["title"],
            h1=hub["h1"],
            intro=hub["intro"],
            sections=hub["sections"],
            breadcrumb_label=hub["breadcrumb_label"],
        )
        out_path = os.path.join(DIST, hub["path"])
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"  wrote {out_path}  ({len(html)} bytes)")


if __name__ == "__main__":
    main()
