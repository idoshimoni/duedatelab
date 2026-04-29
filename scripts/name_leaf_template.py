"""
HTML emitter for a single name leaf page (`/names/<slug>/`).

Reads a NameRecord (per `names_data_schema.py`) and emits the full HTML
document including:
- Canonical block (nav + drawer + footer) from canonical_block.py
- Breadcrumb DOM + BreadcrumbList JSON-LD
- WebPage / Article schema with lastReviewed
- H1 + short-answer block + fact card
- SSA popularity table (if available)
- Origin / usage / pronunciation modules (only when sourced fields exist)
- Variants / related-names / sibling-suggestions internal links
- Source list visible on the page
- Disclosure block per `feedback_names_no_scraping.md`

Per G2A pass criteria:
- One H1 per page
- Source list visible, not buried in JSON-LD
- No empty `<p></p>` when fields are missing (omit the section instead)
- BreadcrumbList JSON-LD mirrors visible breadcrumb DOM
- Internal links are slug references that must resolve in this batch
"""

import json
import os
import sys
from html import escape as html_escape

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from canonical_block import canonical_block
from names_data_schema import NameRecord, KNOWN_SOURCES

SITE_BASE = "https://duedatelab.com"


def _fact_card(rec: NameRecord) -> str:
    """Render the at-a-glance fact card. Only includes fields that are present
    AND sourced (per G1A). Empty card sections are omitted, not rendered as
    empty `<p>`."""
    rows = []
    rows.append(f'<dt>Gender</dt><dd>{html_escape(rec.gender_bucket.replace("-", " ").title())}</dd>')
    if rec.origins:
        origins_text = ", ".join(html_escape(o) for o in rec.origins)
        rows.append(f'<dt>Origin</dt><dd>{origins_text}</dd>')
    if rec.pronunciation:
        rows.append(f'<dt>Pronunciation</dt><dd>{html_escape(rec.pronunciation)}</dd>')
    if rec.ssa_latest_rank and rec.ssa_latest_year:
        rank_text = f'#{rec.ssa_latest_rank} in {rec.ssa_latest_year}'
        if rec.ssa_latest_count:
            rank_text += f' ({rec.ssa_latest_count:,} births)'
        rows.append(f'<dt>U.S. popularity</dt><dd>{html_escape(rank_text)} <small style="color:#5A6B82;">(Social Security Administration)</small></dd>')
    if not rows:
        return ""
    return f'<dl class="pl-name-fact-card">{"".join(rows)}</dl>'


def _short_answer(rec: NameRecord) -> str:
    """Render the short-answer block. Combines meaning + origin + caveat when
    available. If no sourced descriptive field exists, defaults to popularity-only."""
    parts = []
    if rec.meaning:
        meaning = html_escape(rec.meaning)
        if rec.meaning_provenance and rec.meaning_provenance.confidence == "uncertain":
            meaning += " <em style=\"color:#5A6B82;\">(meaning uncertain)</em>"
        parts.append(meaning)
    if rec.origins:
        parts.append("Origin: " + ", ".join(html_escape(o) for o in rec.origins))
    if not parts and rec.ssa_latest_rank and rec.ssa_latest_year:
        parts.append(
            f"Ranked #{rec.ssa_latest_rank} in U.S. baby names for {rec.ssa_latest_year} "
            f"(Social Security Administration data)."
        )
    if not parts:
        return ""
    body = ". ".join(parts)
    if not body.endswith("."):
        body += "."
    return (
        '<div class="pl-name-short-answer" role="note" aria-label="At a glance" '
        'style="background:#F5F7FB;border:1px solid #E4E8F1;border-radius:10px;'
        'padding:12px 16px;margin:16px 0;font-size:15px;line-height:1.5;color:#1F2937;">'
        f'{body}'
        '</div>'
    )


def _ssa_series_label(recorded_sex: str) -> str:
    """Render-friendly label for an SSA recorded-sex code. SSA's public series
    is recorded sex at birth, F or M; the page also shows the disclosure note."""
    return "Female" if recorded_sex == "F" else "Male" if recorded_sex == "M" else "Unknown"


def _ssa_popularity_table(rec: NameRecord) -> str:
    """Render the SSA popularity year table if data is present. Emits an empty
    string if the dataset has no SSA years.

    Per C3 of round-3 review: a dual-series name (e.g. Avery) appears in both
    the female and male SSA series. The table now carries an explicit "SSA series"
    column so each row is unambiguous, and rows are ordered with the primary
    series first within each year. Single-series names render the same column
    without ambiguity."""
    if not rec.ssa_us_top1000_years:
        return ""
    primary = rec.primary_ssa_recorded_sex
    # Sort newest year first; within a year, primary series first, then the other.
    def sort_key(y):
        primary_priority = 0 if y.recorded_sex == primary else 1
        return (-y.year, primary_priority, y.recorded_sex)
    years = sorted(rec.ssa_us_top1000_years, key=sort_key)
    rows = []
    for y in years[:20]:  # Cap at 20 rows so a dual-series name can still show ~10 years
        rank = y.rank if y.rank > 0 else "-"
        count = f"{y.count:,}" if y.count else "-"
        rows.append(
            f'<tr>'
            f'<td>{y.year}</td>'
            f'<td>{html_escape(_ssa_series_label(y.recorded_sex))}</td>'
            f'<td>{rank}</td>'
            f'<td>{count}</td>'
            f'</tr>'
        )
    return (
        '<section class="pl-name-popularity">'
        f'<h2>U.S. popularity for {html_escape(rec.name)}</h2>'
        '<p>Data from the U.S. Social Security Administration. Top-1000 only. '
        'Series labels reflect the sex recorded on Social Security card applications for U.S. births.</p>'
        '<table style="width:100%;border-collapse:collapse;margin:12px 0;">'
        '<thead style="background:#F3F4F6;">'
        '<tr><th scope="col" style="padding:8px;text-align:left;border-bottom:2px solid #E4E8F1;">Year</th>'
        '<th scope="col" style="padding:8px;text-align:left;border-bottom:2px solid #E4E8F1;">SSA series</th>'
        '<th scope="col" style="padding:8px;text-align:left;border-bottom:2px solid #E4E8F1;">Rank</th>'
        '<th scope="col" style="padding:8px;text-align:left;border-bottom:2px solid #E4E8F1;">Births</th></tr>'
        '</thead>'
        f'<tbody>{"".join(rows)}</tbody>'
        '</table>'
        '</section>'
    )


def _meaning_section(rec: NameRecord) -> str:
    """Dedicated meaning section. Per C4 of round-3 review: a generic fact card
    cannot satisfy a title/H1 promising "meaning"; the page must carry a real
    descriptive section sourced via meaning_provenance."""
    if not rec.meaning:
        return ""
    return (
        '<section class="pl-name-meaning">'
        f'<h2>Meaning of {html_escape(rec.name)}</h2>'
        f'<p>{html_escape(rec.meaning)}</p>'
        '</section>'
    )


def _origin_section(rec: NameRecord) -> str:
    """Dedicated origin section. Per C4 of round-3 review: see _meaning_section.
    Origins are emitted only when origins_provenance is present at G1A time."""
    if not rec.origins:
        return ""
    origins_text = ", ".join(rec.origins) if isinstance(rec.origins, (list, tuple)) else str(rec.origins)
    return (
        '<section class="pl-name-origin">'
        f'<h2>Origin of {html_escape(rec.name)}</h2>'
        f'<p>{html_escape(origins_text)}</p>'
        '</section>'
    )


def _cultural_notes_section(rec: NameRecord) -> str:
    """Dedicated cultural notes section, sourced via cultural_notes_provenance."""
    if not rec.cultural_notes:
        return ""
    return (
        '<section class="pl-name-cultural">'
        f'<h2>Cultural notes for {html_escape(rec.name)}</h2>'
        f'<p>{html_escape(rec.cultural_notes)}</p>'
        '</section>'
    )


def _related_links_section(rec: NameRecord, all_slugs: set, strict: bool = True) -> str:
    """Render variants + related + sibling sections.

    Per R5 of Step 2 review: by default (`strict=True`) the renderer raises
    a ValueError when a referenced slug is not in `all_slugs`, so the build
    step fails the batch instead of silently dropping intended links. The
    builder calls with `strict=False` only for explicitly-allowed
    forward-reference cases (and must list those allowances in the gate-pass
    manifest)."""
    sections = []
    for label, slugs in [
        ("Variants", rec.variants),
        ("Related names", rec.related_names),
        ("Sibling suggestions", rec.sibling_suggestions),
    ]:
        unresolved = [s for s in slugs if s not in all_slugs]
        if unresolved and strict:
            raise ValueError(
                f"NameRecord({rec.slug}): unresolved slug references in {label}: {unresolved}. "
                f"Add these slugs to the batch, remove them from the record, or pass --allow-unresolved-refs."
            )
        valid = [s for s in slugs if s in all_slugs]
        if not valid:
            continue
        items = "".join(
            f'<li><a href="/names/{html_escape(s)}/">{html_escape(s.replace("-", " ").title())}</a></li>'
            for s in valid
        )
        sections.append(
            f'<section class="pl-name-related"><h2>{label}</h2><ul>{items}</ul></section>'
        )
    return "".join(sections)


def _sources_section(rec: NameRecord) -> str:
    """Render the visible source list. SSA is implied if popularity is present.
    Other fields contribute their FieldProvenance source_url + source_id."""
    seen = set()
    items = []
    if rec.ssa_us_top1000_years or rec.ssa_latest_rank:
        ssa = KNOWN_SOURCES["SSA"]
        items.append(
            f'<li><a href="{ssa["url"]}" target="_blank" rel="noopener">'
            f'{html_escape(ssa["label"])}</a> — {html_escape(ssa["scope"])}</li>'
        )
        seen.add(ssa["url"])
    for pv_attr in ("meaning_provenance", "origins_provenance",
                    "pronunciation_provenance", "cultural_notes_provenance"):
        pv = getattr(rec, pv_attr, None)
        if not pv or pv.source_url in seen:
            continue
        seen.add(pv.source_url)
        label = KNOWN_SOURCES.get(pv.source_id, {}).get("label", pv.source_id)
        items.append(
            f'<li><a href="{html_escape(pv.source_url)}" target="_blank" rel="noopener">'
            f'{html_escape(label)}</a> — {html_escape(pv.notes or "field source")}</li>'
        )
    if not items:
        return ""
    return (
        '<aside class="pl-sources">'
        '<h3>Sources</h3>'
        f'<ul>{"".join(items)}</ul>'
        '<p class="pl-source-note">Meanings and origins can vary by tradition. '
        'See methodology for our source-discipline standards.</p>'
        '</aside>'
    )


def _disclosure_block(rec: NameRecord) -> str:
    """Per `feedback_names_no_scraping.md`: pages should disclose that meanings
    can vary by tradition where relevant. Always shown for names with origin
    or meaning fields. Per R review §4.5: disclosure links to the methodology
    hub so the curator's source-discipline standards are reachable."""
    if not (rec.meaning or rec.origins or rec.cultural_notes):
        return ""
    return (
        '<div class="pl-name-disclosure" style="font-size:13px;color:#5A6B82;'
        'margin:16px 0;padding:12px;border-left:3px solid #E6EAF1;">'
        'Name meanings and origins are conventional summaries, not strict scientific '
        'classifications. Different traditions and references may give different '
        'meanings or origins for the same name. See our '
        '<a href="/methodology/" style="color:#C80A4E;">methodology</a> '
        'for source-discipline standards.'
        '</div>'
    )


def _page_topic(rec: NameRecord) -> str:
    """Per R2 of Step 2 review: branch the page title/H1 to match what's actually
    on the page. SSA-only pages can't claim 'meaning, origin, and popularity'."""
    has_descriptive = bool(rec.meaning or rec.origins or rec.pronunciation or rec.cultural_notes)
    has_ssa = bool(rec.ssa_us_top1000_years or rec.ssa_latest_rank)
    if has_descriptive and has_ssa:
        return f"{rec.name} name meaning, origin, and popularity"
    if has_descriptive:
        return f"{rec.name} name meaning and origin"
    if has_ssa:
        return f"{rec.name} baby name popularity"
    raise ValueError(f"NameRecord({rec.slug}): no publishable page topic (no descriptive fields, no SSA)")


def _ssa_disclosure_note(rec: NameRecord) -> str:
    """Per round-4 review §Patch 1: SSA's public name data is sourced from
    Social Security card applications for U.S. births, not from vital-records
    birth-certificate registries. Series are grouped by the sex recorded on
    the SS-5 application, which is not a statement about gender identity."""
    if not (rec.ssa_us_top1000_years or rec.ssa_latest_rank):
        return ""
    return (
        '<p class="pl-ssa-note" style="font-size:12px;color:#5A6B82;margin:8px 0 0;font-style:italic;">'
        'SSA name data comes from Social Security card applications for U.S. births '
        'and is grouped by the sex recorded on the application; it is not a statement about gender identity.'
        '</p>'
    )


def _jsonld(rec: NameRecord) -> str:
    """Emit BreadcrumbList + WebPage JSON-LD blocks."""
    canonical_url = f"{SITE_BASE}/names/{rec.slug}/"
    breadcrumb = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{SITE_BASE}/"},
            {"@type": "ListItem", "position": 2, "name": "Names", "item": f"{SITE_BASE}/names/"},
            {"@type": "ListItem", "position": 3, "name": rec.name, "item": canonical_url},
        ],
    }
    title = _page_topic(rec)
    # Lead with the name + gender bucket so descriptions are unique even when
    # two rows share the same SSA rank.
    description_parts = [
        f"{rec.name} is a {rec.gender_bucket.replace('-', ' ')} name."
    ]
    if rec.meaning:
        description_parts.append(rec.meaning)
    if rec.origins:
        description_parts.append("Origin: " + ", ".join(rec.origins) + ".")
    if rec.ssa_latest_rank and rec.ssa_latest_year:
        description_parts.append(f"Ranked #{rec.ssa_latest_rank} in U.S. baby names for {rec.ssa_latest_year}.")
    description = " ".join(description_parts)

    webpage = {
        "@context": "https://schema.org",
        "@type": "WebPage",
        "name": title,
        "description": description,
        "url": canonical_url,
        "inLanguage": "en",
        "lastReviewed": rec.last_reviewed,
        "publisher": {
            "@type": "Organization",
            "name": "DueDateLab",
            "url": f"{SITE_BASE}/",
        },
    }
    return (
        f'<script type="application/ld+json">{json.dumps(breadcrumb, separators=(",", ":"))}</script>'
        f'<script type="application/ld+json">{json.dumps(webpage, separators=(",", ":"))}</script>'
    )


def _breadcrumb_dom(rec: NameRecord) -> str:
    """Visible breadcrumb. Mirrors the BreadcrumbList JSON-LD."""
    return (
        '<nav class="pl-breadcrumb" aria-label="Breadcrumb">'
        '<a href="/">Home</a>'
        ' <span class="pl-breadcrumb-sep" aria-hidden="true">/</span> '
        '<a href="/names/">Names</a>'
        ' <span class="pl-breadcrumb-sep" aria-hidden="true">/</span> '
        f'<span aria-current="page">{html_escape(rec.name)}</span>'
        '</nav>'
    )


def render_name_leaf(rec: NameRecord, all_slugs: set, strict: bool = True) -> str:
    """Render the full HTML document for a name leaf page.

    `all_slugs` is the set of slugs in the current batch.

    Per R5 of Step 2 review: when `strict=True` (default), any unresolved
    related/variant/sibling slug raises ValueError so the build fails the
    batch instead of silently dropping intended links."""
    block = canonical_block(f"/names/{rec.slug}/")
    page_topic = _page_topic(rec)
    title_full = f"{page_topic} | DueDateLab"
    canonical_url = f"{SITE_BASE}/names/{rec.slug}/"
    # Lead with the name + gender bucket so descriptions are unique even when
    # two rows share the same SSA rank.
    description_parts = [
        f"{rec.name} is a {rec.gender_bucket.replace('-', ' ')} name."
    ]
    if rec.meaning:
        description_parts.append(rec.meaning)
    if rec.origins:
        description_parts.append("Origin: " + ", ".join(rec.origins) + ".")
    if rec.ssa_latest_rank and rec.ssa_latest_year:
        description_parts.append(f"Ranked #{rec.ssa_latest_rank} in U.S. baby names for {rec.ssa_latest_year}.")
    description = " ".join(description_parts)

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<!-- pl-seo-block -->
<link rel="canonical" href="{canonical_url}"/>
<meta name="robots" content="index,follow"/>
<link rel="icon" href="/favicon.svg" type="image/svg+xml"/>
<link rel="apple-touch-icon" href="/apple-touch-icon-180.png"/>
<link rel="manifest" href="/site.webmanifest"/>
<meta name="theme-color" content="#1A2E4A"/>
<meta property="og:type" content="article"/>
<meta property="og:title" content="{html_escape(title_full, quote=True)}"/>
<meta property="og:description" content="{html_escape(description, quote=True)}"/>
<meta property="og:url" content="{canonical_url}"/>
<meta property="og:site_name" content="DueDateLab"/>
<meta name="twitter:card" content="summary"/>
<meta name="twitter:title" content="{html_escape(title_full, quote=True)}"/>
<meta name="twitter:description" content="{html_escape(description, quote=True)}"/>
{_jsonld(rec)}
<!-- /pl-seo-block -->
<title>{html_escape(title_full)}</title>
<meta name="description" content="{html_escape(description, quote=True)}"/>
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

<main class="pl-page pl-name-leaf">
  {_breadcrumb_dom(rec)}
  <h1 class="pl-h1">{html_escape(page_topic)}</h1>
  <p class="pl-byline" style="font-size:13px;color:#5A6B82;margin:0 0 14px;line-height:1.5;">Last reviewed <time datetime="{rec.last_reviewed}">{rec.last_reviewed}</time></p>
  {_short_answer(rec)}
  {_fact_card(rec)}
  {_meaning_section(rec)}
  {_origin_section(rec)}
  {_cultural_notes_section(rec)}
  {_ssa_popularity_table(rec)}
  {_ssa_disclosure_note(rec)}
  {_related_links_section(rec, all_slugs, strict=strict)}
  {_sources_section(rec)}
  {_disclosure_block(rec)}
</main>

{block["footer"]}

<script src="/assets/app.js?v=15"></script>
</body>
</html>
"""
