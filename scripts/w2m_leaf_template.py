"""
Per-week leaf HTML template for /pregnancy/weeks-to-months/N/.

Phase 2 Step 5 (Option B), per round 1.5 research-AI consult.
Renders one HTML file from a W2MRecord. Visual + structural parity
with the existing 7 calculator pages: same canonical block via
refresh_canonical_block.py, same CSS classes from styles.css?v=24,
same byline + share + sources patterns.

The canonical header/drawer/footer are stub-marked here and populated
in-place by scripts/refresh_canonical_block.py at build time. Same
pattern as affiliate-disclosure.html.

Per round 1.5 must-fix list:
  - URL relationship frozen (self-canonical, no canonicalize-to-hub)
  - Edge-week copy: weeks 1-3 LMP note, weeks 41-42 no medical claims
  - Thin-page guard: direct answer + convention + mini-table + chart
    link + methodology link + adjacent links
  - Unique title/H1/meta/canonical/breadcrumb per leaf
  - WebPage + BreadcrumbList only, no FAQPage
"""

from __future__ import annotations
import json
from datetime import date

from w2m_data_schema import (
    W2MRecord,
    build_all_records,
    descriptive_adjacent_anchor_text,
    AVG_CALENDAR_MONTH_DAYS,
    FOUR_WEEK_MONTH_DAYS,
)
from canonical_block import canonical_block


# Static asset versions, kept in sync with the rest of dist/.
STYLES_VERSION = "v=24"
APP_JS_VERSION = "v=19"


def _all_records_by_week() -> dict[int, W2MRecord]:
    return {r.week: r for r in build_all_records()}


def _mini_table_rows(records_by_week: dict[int, W2MRecord], target_week: int) -> str:
    """Render the mini-table: target ± 2 surrounding weeks.

    For weeks 1-2 and 41-42, the window clips to available weeks rather
    than going out of range.
    """
    span = []
    for w in range(target_week - 2, target_week + 3):
        if w in records_by_week:
            span.append(records_by_week[w])
    rows = []
    for r in span:
        emphasis = ' class="is-target"' if r.week == target_week else ''
        week_word = "week" if r.week == 1 else "weeks"
        rows.append(
            f'        <tr{emphasis}><td>{r.week}{r.table_tag_html}</td>'
            f'<td>{r.four_week_months_str}</td>'
            f'<td>~{r.calendar_months_str}</td>'
            f'<td>{r.days_since_lmp}</td></tr>'
        )
    return "\n".join(rows)


def _adjacent_links_block(record: W2MRecord) -> str:
    """Render prev/next adjacent-week navigation links.

    Per round 2 Q8 must-fix: descriptive anchor text ("22 weeks pregnant
    in months") rather than generic "Previous" or "← Week 22".
    """
    parts = []
    if record.prev_week is not None:
        text = descriptive_adjacent_anchor_text(record.prev_week)
        parts.append(
            f'<a class="pl-w2m-adj-link" href="/pregnancy/weeks-to-months/'
            f'{record.prev_week}/" rel="prev">&larr; {text}</a>'
        )
    if record.next_week is not None:
        text = descriptive_adjacent_anchor_text(record.next_week)
        parts.append(
            f'<a class="pl-w2m-adj-link" href="/pregnancy/weeks-to-months/'
            f'{record.next_week}/" rel="next">{text} &rarr;</a>'
        )
    return ' &middot; '.join(parts) if parts else ''


def _lmp_note_block(record: W2MRecord) -> str:
    """Edge-week LMP note for weeks 1-3 only.

    Per round 3 must-fix F1 (2026-04-29): use the safe templated copy
    that does not make a week-specific biological timing claim. The
    earlier version said "Week N is counted before conception has
    typically occurred" which overstated pre-conception timing for
    week 3 (where conception often has occurred in a typical cycle).

    The replacement copy is identical across weeks 1, 2, 3 and avoids
    any week-specific timing assertion.
    """
    if not record.is_lmp_counted:
        return ""
    return (
        '  <section class="pl-explain pl-w2m-lmp-note" style="background:#FFF8E6;'
        'border:1px solid #F0D987;border-radius:8px;padding:14px 16px;margin:18px 0;">\n'
        '    <p style="margin:0;"><strong>Note about early weeks:</strong> '
        'Pregnancy weeks are counted from the first day of your last menstrual '
        'period (LMP), not from the day of conception. Early pregnancy counts '
        'therefore include days before conception has occurred or before it can '
        'be confirmed. This is the standard clinical convention for dating, '
        'used because LMP is easier to know than the exact day of conception.</p>\n'
        '  </section>\n'
    )


def _ld_jsonld(record: W2MRecord) -> str:
    """Render the WebPage + BreadcrumbList JSON-LD blocks.

    Per round 1.5 reply: WebPage + BreadcrumbList only, no FAQPage,
    no HowTo, no Product, no MedicalWebPage.

    Per round 2 Q9 must-fix: each block carries a unique @id derived
    from the canonical URL (#webpage and #breadcrumb fragments).
    """
    today = date.today().isoformat()
    webpage = {
        "@context": "https://schema.org",
        "@type": "WebPage",
        "@id": f"{record.canonical_url}#webpage",
        "name": record.title.replace(" | DueDateLab", ""),
        "description": record.meta_description,
        "url": record.canonical_url,
        "inLanguage": "en",
        "datePublished": today,
        "dateModified": today,
        "lastReviewed": today,
        "isPartOf": {
            "@type": "WebSite",
            "name": "DueDateLab",
            "url": "https://duedatelab.com/",
        },
        "publisher": {
            "@type": "Organization",
            "name": "DueDateLab",
            "url": "https://duedatelab.com/",
            "logo": {
                "@type": "ImageObject",
                "url": "https://duedatelab.com/assets/duedatelab-mark-512.png",
                "width": 512,
                "height": 512,
            },
            "foundingDate": "2026",
            "foundingLocation": {
                "@type": "Place",
                "address": {
                    "@type": "PostalAddress",
                    "addressCountry": "BE",
                },
            },
            "contactPoint": {
                "@type": "ContactPoint",
                "contactType": "editorial",
                "email": "hello@duedatelab.com",
                "availableLanguage": ["en"],
            },
            "sameAs": [],
        },
    }
    breadcrumb = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "@id": f"{record.canonical_url}#breadcrumb",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "DueDateLab",
             "item": "https://duedatelab.com/"},
            {"@type": "ListItem", "position": 2, "name": "Pregnancy",
             "item": "https://duedatelab.com/pregnancy/"},
            {"@type": "ListItem", "position": 3, "name": "Pregnancy Weeks to Months",
             "item": "https://duedatelab.com/pregnancy/weeks-to-months/"},
            {"@type": "ListItem", "position": 4, "name": record.breadcrumb_position3_name,
             "item": record.canonical_url},
        ],
    }
    return (
        f'<script type="application/ld+json">{json.dumps(webpage, separators=(",", ":"))}</script>\n'
        f'<script type="application/ld+json">{json.dumps(breadcrumb, separators=(",", ":"))}</script>'
    )


def render_leaf(record: W2MRecord, build_mode: str = "production") -> str:
    """Render a complete HTML page for one per-week leaf.

    Args:
        record: deterministic W2MRecord generated by w2m_data_schema.
        build_mode: "production" (robots index,follow) or "staging"
            (robots noindex,nofollow). Per round 2 Q11 must-fix,
            staging leaves carry noindex,nofollow as a belt-and-suspenders
            protection in case a staging file accidentally lands on the
            live deploy. Sitemap exclusion is the primary protection.

    Returns:
        Full HTML document as a string.
    """
    if build_mode not in ("production", "staging"):
        raise ValueError(f"build_mode must be 'production' or 'staging', got {build_mode!r}")
    robots_content = "noindex,nofollow" if build_mode == "staging" else "index,follow"

    today_iso = date.today().isoformat()
    today_human = date.today().strftime("%B %-d, %Y")

    records_by_week = _all_records_by_week()
    mini_table = _mini_table_rows(records_by_week, record.week)
    adj_links = _adjacent_links_block(record)
    lmp_note = _lmp_note_block(record)
    jsonld = _ld_jsonld(record)
    week_word = "week" if record.week == 1 else "weeks"
    # Per round 4 reviewer F2 must-fix: singularize the big-number unit
    # label when the count is exactly 1 (week 4).
    big_unit = "four-week pregnancy month" if record.four_week_months == 1.0 else "four-week pregnancy months"

    # Inline the canonical nav/drawer/footer at render time so each leaf
    # is self-contained and visually identical to the rest of the site
    # without a separate post-process step. canonical_block reads the
    # current URL only for `aria-current="page"` matching; leaf URLs are
    # not in the nav, so no current-page styling triggers.
    canon = canonical_block(f"/pregnancy/weeks-to-months/{record.week}/")
    desktop_header = canon["desktop_header"]
    mobile_header = canon["mobile_header"]
    drawer = canon["drawer"]
    footer = canon["footer"]

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<!-- pl-seo-block -->
<link rel="canonical" href="{record.canonical_url}"/>
<meta name="robots" content="{robots_content}"/>
<link rel="icon" href="/favicon.svg" type="image/svg+xml"/>
<link rel="icon" href="/favicon-32.png" type="image/png" sizes="32x32"/>
<link rel="icon" href="/favicon-16.png" type="image/png" sizes="16x16"/>
<link rel="apple-touch-icon" href="/apple-touch-icon-180.png"/>
<link rel="icon" href="/favicon.ico" sizes="any"/>
<link rel="manifest" href="/site.webmanifest"/>
<meta name="theme-color" content="#1A2E4A"/>
<meta property="og:type" content="website"/>
<meta property="og:title" content="{record.title}"/>
<meta property="og:description" content="{record.meta_description}"/>
<meta property="og:url" content="{record.canonical_url}"/>
<meta property="og:image" content="https://duedatelab.com/og-image.png"/>
<meta property="og:image:width" content="1200"/>
<meta property="og:image:height" content="630"/>
<meta property="og:image:alt" content="DueDateLab — Free, private pregnancy and parenting calculators"/>
<meta property="og:site_name" content="DueDateLab"/>
<meta property="og:locale" content="en_US"/>
<meta property="og:locale:alternate" content="en_GB"/>
<meta property="og:locale:alternate" content="en_BE"/>
<meta name="twitter:card" content="summary_large_image"/>
<meta name="twitter:title" content="{record.title}"/>
<meta name="twitter:description" content="{record.meta_description}"/>
<meta name="twitter:image" content="https://duedatelab.com/og-image.png"/>
{jsonld}
<!-- /pl-seo-block -->
<title>{record.title}</title>
<meta name="description" content="{record.meta_description}"/>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/assets/styles.css?{STYLES_VERSION}">
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-4285310692091665" crossorigin="anonymous"></script>
</head>
<body data-calculator="weeks-to-months-leaf" data-w2m-week="{record.week}">
{desktop_header}{mobile_header}
{drawer}
<main class="pl-page">
  <div class="pl-card">
    <h1 class="pl-h1">{record.h1}</h1>
    <p class="pl-byline" style="font-size:13px;color:#5A6B82;margin:0 0 14px;line-height:1.5;">Written by <strong style="font-weight:600;color:#1A2E4A;">DueDateLab Editorial Team</strong> &middot; Last updated <time datetime="{today_iso}">{today_human}</time></p>
    <p class="pl-sub">A direct conversion using DueDateLab's transparent four-week pregnancy-month convention, with an average calendar-month comparison alongside.</p>
  </div>

  <section class="pl-result" id="w2m-leaf-result" aria-labelledby="w2m-leaf-result-h">
    <p class="pl-result-eyebrow">
      <span class="pl-result-eyebrow-rule" aria-hidden="true"></span>
      <span class="pl-result-eyebrow-label"><strong>DueDateLab</strong> &mdash; Weeks to Months &middot; Week {record.week}</span>
    </p>
    <h2 class="pl-result-h" id="w2m-leaf-result-h">Conversion</h2>
    <output class="pl-result-big">{record.four_week_months_str}</output>
    <p class="pl-result-sub">{big_unit}</p>
    <div class="pl-result-stats">
      <div class="pl-result-stat">
        <span class="pl-result-stat-label">Completed</span>
        <span class="pl-result-stat-value">{record.completed_remainder_str}</span>
      </div>
      <div class="pl-result-stat">
        <span class="pl-result-stat-label">Calendar comparison</span>
        <span class="pl-result-stat-value">~{record.calendar_months_str} average calendar months</span>
      </div>
      <div class="pl-result-stat">
        <span class="pl-result-stat-label">Days since LMP</span>
        <span class="pl-result-stat-value">{record.days_since_lmp} days</span>
      </div>
    </div>
    <p class="pl-result-disclaimer">
      {record.hero_answer}
    </p>
  </section>

{lmp_note}  <section class="pl-explain">
    <h2>Surrounding weeks</h2>
    <p>How this week sits in context, with two weeks on each side. The full chart from week 1 to week 42 is on the <a href="/pregnancy/weeks-to-months/">hub page</a>.</p>
    <table class="pl-w2m-chart">
      <caption class="pl-sr-only">Week {record.week} pregnancy weeks-to-months conversion with surrounding weeks for context</caption>
      <thead>
        <tr>
          <th scope="col">Week</th>
          <th scope="col">Four-week pregnancy months</th>
          <th scope="col">Calendar-month comparison</th>
          <th scope="col">Days since LMP</th>
        </tr>
      </thead>
      <tbody>
{mini_table}
      </tbody>
    </table>
    <p class="pl-w2m-adj" style="margin:14px 0 0;font-size:14px;color:#5A6B82;">{adj_links}</p>
  </section>

  <section class="pl-explain">
    <h2>Why "months" is approximate</h2>
    <p>Pregnancies are dated in <b>weeks</b>, counted from the first day of the last menstrual period. Months are a user-facing summary. There is no single clinical definition of a pregnancy month. DueDateLab uses a transparent four-week convention because it produces clean conversions: 1 month = 4 weeks = 28 days. The calendar-month comparison column uses an average calendar month of {AVG_CALENDAR_MONTH_DAYS} days (365.25 ÷ 12), so the same week comes out a little smaller in calendar months. Both numbers are correct; they describe the same span using different month definitions.</p>
    <p>For a calendar date for the birth, use the <a href="/">Due Date Calculator</a>. For the formula and the full week-by-week chart, see the <a href="/methodology/weeks-to-months">methodology</a>.</p>
  </section>

  <aside class="pl-sources">
    <h3>Sources</h3>
    <ul>
      <li><a href="https://www.acog.org/clinical/clinical-guidance/committee-opinion/articles/2017/05/methods-for-estimating-the-due-date" target="_blank" rel="noopener">ACOG: Methods for Estimating the Due Date (Committee Opinion 700)</a></li>
      <li><a href="https://www.nhs.uk/pregnancy/finding-out/due-date-calculator/" target="_blank" rel="noopener">NHS: Pregnancy due date calculator (week-based dating)</a></li>
    </ul>
    <p class="pl-source-note">Pregnancy is dated in weeks from LMP per ACOG and NHS guidance. The four-week pregnancy-month and calendar-month figures on this page are arithmetic conversions, not clinical measurements.</p>
  </aside>

  <section class="pl-related">
    <h2 class="pl-related-h">Related tools and reading</h2>
    <div class="pl-related-grid c4">
      <a class="pl-related-card" href="/pregnancy/weeks-to-months/"><div class="pl-related-title">Full weeks-to-months chart</div><p class="pl-related-desc">Calculator plus the complete week 1 to week 42 reference table.</p></a>
      <a class="pl-related-card" href="/methodology/weeks-to-months"><div class="pl-related-title">Weeks-to-months methodology</div><p class="pl-related-desc">The convention, the formula, and why month answers differ across sites.</p></a>
      <a class="pl-related-card" href="/"><div class="pl-related-title">Due Date Calculator</div><p class="pl-related-desc">Estimate a calendar date for the birth from LMP, conception, or a known due date.</p></a>
      <a class="pl-related-card" href="/articles/first-trimester-week-by-week"><div class="pl-related-title">First Trimester Week by Week</div><p class="pl-related-desc">What changes from week 1 through week 13.</p></a>
    </div>
  </section>
</main>
{footer}
<script src="/assets/app.js?{APP_JS_VERSION}"></script>
</body>
</html>
"""
