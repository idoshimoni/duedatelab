"""
Topical metadata per URL. Source of truth for Related-grid generation.

Each URL gets:
- topics: topical/life-stage tags. Used to score related adjacency.
- page_type: content-type descriptor (tool | article | methodology | hub | company).
  Used only for card rendering and minor tie-break, NOT for scoring.
- title: short card label (<strong> or .pl-related-title text).
- desc: card subtitle (<span> or .pl-related-desc text).

The related-grid generator reads this, plus sitemap_urls.py, and
regenerates <div class="pl-related-grid"> blocks deterministically.

Topical tag vocabulary:
  Life-stage (audience-oriented):
    preconception    — TTC audience (ovulation, conception-date)
    pregnancy        — gestational / due-date audience
    infancy          — parent of 0 to 12 month old (growth, sleep)
    novelty          — entertainment (Chinese gender)
  Specific content-area:
    growth           — percentile, WHO curves
    sleep            — sleep-needs, sleep-regressions cluster
    dating           — due date, Naegele's rule
    sex-determination — Chinese gender, anatomy scan, NIPT

Scoring rule:
  score(target, candidate) = |topics(target) ∩ topics(candidate)|
  ties broken by: sister-pair convention > higher sitemap priority > alpha URL

page_type is NOT counted in the score, because "tool" or "article"
overlap is not meaningful topical adjacency. That was the design bug
fixed on 2026-04-24 after the first generator run ranked /chinese-gender-chart
above /articles/4-month-sleep-regression on /baby-percentile (both shared
"tool" but only the sleep article shares the infancy audience).
"""

URL_TOPICS = {
    "/": {
        "topics": ["pregnancy", "dating"],
        "page_type": "tool",
        "title": "Due Date Calculator",
        "desc": "When's baby due? Estimate from period or conception.",
    },
    "/chinese-gender-chart": {
        "topics": ["novelty", "sex-determination", "preconception"],
        "page_type": "tool",
        "title": "Chinese Gender Chart",
        "desc": "Boy or girl? Lunar-age novelty chart.",
    },
    "/sleep-needs-by-age": {
        "topics": ["infancy", "sleep"],
        "page_type": "tool",
        "title": "Sleep Needs by Age",
        "desc": "AAP-recommended sleep, 0 to 18 years.",
    },
    "/baby-percentile": {
        "topics": ["infancy", "growth"],
        "page_type": "tool",
        "title": "Baby Percentile",
        "desc": "WHO growth curves for weight and length.",
    },
    "/conception-calculator": {
        "topics": ["preconception", "pregnancy", "dating"],
        "page_type": "tool",
        "title": "Conception Calculator",
        "desc": "When did you conceive? 4 ways to estimate.",
    },
    "/ovulation-calculator": {
        "topics": ["preconception"],
        "page_type": "tool",
        "title": "Ovulation Calculator",
        "desc": "Luteal-phase-anchored prediction and fertile window.",
    },
    "/period-calculator": {
        "topics": ["preconception", "dating"],
        "page_type": "tool",
        "title": "Period Calculator",
        "desc": "Predict your next period from LMP and cycle length.",
    },

    # Articles
    "/articles/": {
        "topics": ["hub"],
        "page_type": "hub",
        "title": "All articles",
        "desc": "Browse every DueDateLab article.",
    },
    "/articles/due-date-vs-conception-date": {
        "topics": ["pregnancy", "dating", "preconception"],
        "page_type": "article",
        "title": "Due Date vs. Conception Date",
        "desc": "How each is calculated and why they differ.",
    },
    "/articles/first-trimester-week-by-week": {
        "topics": ["pregnancy"],
        "page_type": "article",
        "title": "First Trimester Week by Week",
        "desc": "What to expect through week 13.",
    },
    "/articles/chinese-gender-chart-accuracy": {
        "topics": ["novelty", "sex-determination"],
        "page_type": "article",
        "title": "Chinese Gender Chart Accuracy",
        "desc": "What the evidence actually shows.",
    },
    "/articles/sleep-regressions-by-month": {
        "topics": ["infancy", "sleep"],
        "page_type": "article",
        "title": "Sleep Regressions by Month",
        "desc": "Umbrella article: what to expect and what helps.",
    },
    "/articles/baby-percentile-explained": {
        "topics": ["infancy", "growth"],
        "page_type": "article",
        "title": "Baby Percentile Explained",
        "desc": "What the number really means.",
    },
    "/articles/4-month-sleep-regression": {
        "topics": ["infancy", "sleep"],
        "page_type": "article",
        "title": "4 Month Sleep Regression",
        "desc": "The 4-month change explained.",
    },
    "/articles/8-month-sleep-regression": {
        "topics": ["infancy", "sleep"],
        "page_type": "article",
        "title": "8 Month Sleep Regression",
        "desc": "Separation anxiety and sleep.",
    },

    # Methodology
    "/methodology/": {
        "topics": ["hub"],
        "page_type": "hub",
        "title": "All methodology pages",
        "desc": "Formulas and sources index.",
    },
    "/methodology/due-date-calculator": {
        "topics": ["pregnancy", "dating"],
        "page_type": "methodology",
        "title": "Due Date methodology",
        "desc": "Naegele, ACOG 700, ultrasound adjustment.",
    },
    "/methodology/conception-calculator": {
        "topics": ["preconception", "pregnancy", "dating"],
        "page_type": "methodology",
        "title": "Conception methodology",
        "desc": "LMP, EDD reverse, IVF transfer.",
    },
    "/methodology/ovulation-calculator": {
        "topics": ["preconception"],
        "page_type": "methodology",
        "title": "Ovulation methodology",
        "desc": "Wilcox 1995, Lenton 1984, cycle math.",
    },
    "/methodology/period-calculator": {
        "topics": ["preconception", "dating"],
        "page_type": "methodology",
        "title": "Period methodology",
        "desc": "Formulas, cycle range, and sources.",
    },
    "/methodology/baby-percentile": {
        "topics": ["infancy", "growth"],
        "page_type": "methodology",
        "title": "Baby Percentile methodology",
        "desc": "LMS method, WHO standards, 0 to 5 years.",
    },
    "/methodology/sleep-needs-by-age": {
        "topics": ["infancy", "sleep"],
        "page_type": "methodology",
        "title": "Sleep Needs methodology",
        "desc": "AAP-endorsed AASM ranges.",
    },
    "/methodology/chinese-gender-chart": {
        "topics": ["novelty", "sex-determination"],
        "page_type": "methodology",
        "title": "Chinese Gender Chart methodology",
        "desc": "Lunar math, Villamor 2010 accuracy.",
    },

    # Company pages (no related-grid)
    "/about":      {"topics": [], "page_type": "company", "title": "About",      "desc": ""},
    "/privacy":    {"topics": [], "page_type": "company", "title": "Privacy",    "desc": ""},
    "/terms":      {"topics": [], "page_type": "company", "title": "Terms",      "desc": ""},
    "/disclaimer": {"topics": [], "page_type": "company", "title": "Disclaimer", "desc": ""},
    "/contact":    {"topics": [], "page_type": "company", "title": "Contact",    "desc": ""},
}

INCLUDED_FOR_RELATED = {
    # index.html intentionally excluded: home page grid is curated for
    # flagship-tool discovery, not topical drill-down. See EXCLUDED_FROM_RELATED.
    "chinese-gender-chart.html",
    "sleep-needs-by-age.html",
    "baby-percentile.html",
    "conception-calculator.html",
    "ovulation-calculator.html",
    "period-calculator.html",

    "articles/due-date-vs-conception-date.html",
    "articles/first-trimester-week-by-week.html",
    "articles/chinese-gender-chart-accuracy.html",
    "articles/sleep-regressions-by-month.html",
    "articles/baby-percentile-explained.html",
    "articles/4-month-sleep-regression.html",
    "articles/8-month-sleep-regression.html",

    "methodology/due-date-calculator.html",
    "methodology/conception-calculator.html",
    "methodology/ovulation-calculator.html",
    "methodology/period-calculator.html",
    "methodology/baby-percentile.html",
    "methodology/sleep-needs-by-age.html",
    "methodology/chinese-gender-chart.html",
}

# Pages explicitly skipped: 404 has a hand-curated quick-nav grid
# (4 top tools), not a topic-adjacency set. articles/index and
# methodology/index are hub pages with bespoke "Tools referenced"
# blocks — left untouched to avoid breaking curator intent.
EXCLUDED_FROM_RELATED = {
    "404.html",
    "articles/index.html",
    "methodology/index.html",
    # Home page is curated for flagship-tool discovery. Topic-adjacency
    # scoring collapses it to a single cluster (e.g. all dating pages),
    # which hurts cross-tool discovery from the landing page.
    "index.html",
}

RELATED_CARD_COUNT = 4

# Sister-page convention: every tool ↔ methodology pair links to its
# sister as the first related card. Preserves existing navigation.
SISTER_PAGES = {
    "/": "/methodology/due-date-calculator",
    "/chinese-gender-chart": "/methodology/chinese-gender-chart",
    "/sleep-needs-by-age": "/methodology/sleep-needs-by-age",
    "/baby-percentile": "/methodology/baby-percentile",
    "/conception-calculator": "/methodology/conception-calculator",
    "/ovulation-calculator": "/methodology/ovulation-calculator",
    "/period-calculator": "/methodology/period-calculator",
    "/methodology/due-date-calculator": "/",
    "/methodology/chinese-gender-chart": "/chinese-gender-chart",
    "/methodology/sleep-needs-by-age": "/sleep-needs-by-age",
    "/methodology/baby-percentile": "/baby-percentile",
    "/methodology/conception-calculator": "/conception-calculator",
    "/methodology/ovulation-calculator": "/ovulation-calculator",
    "/methodology/period-calculator": "/period-calculator",
}
