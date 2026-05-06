"""
Source of truth for which URLs appear in sitemap.xml.

Each entry maps a public URL to the HTML source file it is rendered
from, plus the sitemap priority and changefreq hints. The refresh
script reads this, looks up each source file's last-commit date in
git, and writes sitemap.xml.

To add a new URL: append an entry here. To retire one: remove it.
Never hand-edit sitemap.xml.

source_file is the path relative to the dist/ directory. Use
"dir/index.html" for directory URLs that resolve to index.html.
"""

SITE_BASE = "https://duedatelab.com"

URL_MAP = [
    # IA hubs (PI2 from 2026-04-25 IA restructure)
    {"url": "/calculators/",                    "source": "calculators/index.html",                      "priority": "0.8", "changefreq": "monthly"},
    {"url": "/cycle-and-fertility/",            "source": "cycle-and-fertility/index.html",              "priority": "0.7", "changefreq": "monthly"},
    {"url": "/pregnancy/",                      "source": "pregnancy/index.html",                        "priority": "0.7", "changefreq": "monthly"},
    {"url": "/baby-child/",                     "source": "baby-child/index.html",                       "priority": "0.7", "changefreq": "monthly"},

    # Home + flagship tools
    {"url": "/",                                "source": "index.html",                                  "priority": "1.0", "changefreq": "weekly"},
    {"url": "/chinese-gender-chart",            "source": "chinese-gender-chart.html",                   "priority": "0.9", "changefreq": "monthly"},
    {"url": "/sleep-needs-by-age",              "source": "sleep-needs-by-age.html",                     "priority": "0.9", "changefreq": "monthly"},
    {"url": "/baby-percentile",                 "source": "baby-percentile.html",                        "priority": "0.9", "changefreq": "monthly"},
    {"url": "/conception-calculator",           "source": "conception-calculator.html",                  "priority": "0.9", "changefreq": "monthly"},
    {"url": "/ovulation-calculator",            "source": "ovulation-calculator.html",                   "priority": "0.9", "changefreq": "monthly"},
    {"url": "/period-calculator",               "source": "period-calculator.html",                      "priority": "0.9", "changefreq": "monthly"},

    # Articles
    {"url": "/articles/",                                         "source": "articles/index.html",                              "priority": "0.8", "changefreq": "weekly"},
    {"url": "/articles/due-date-vs-conception-date",              "source": "articles/due-date-vs-conception-date.html",        "priority": "0.7", "changefreq": "monthly"},
    {"url": "/articles/spotting-during-ovulation",                "source": "articles/spotting-during-ovulation.html",          "priority": "0.7", "changefreq": "monthly"},
    {"url": "/articles/implantation-bleeding",                    "source": "articles/implantation-bleeding.html",              "priority": "0.7", "changefreq": "monthly"},
    {"url": "/articles/first-trimester-week-by-week",             "source": "articles/first-trimester-week-by-week.html",       "priority": "0.7", "changefreq": "monthly"},
    {"url": "/articles/chinese-gender-chart-accuracy",            "source": "articles/chinese-gender-chart-accuracy.html",      "priority": "0.7", "changefreq": "monthly"},
    {"url": "/articles/sleep-regressions-by-month",               "source": "articles/sleep-regressions-by-month.html",         "priority": "0.7", "changefreq": "monthly"},
    {"url": "/articles/baby-percentile-explained",                "source": "articles/baby-percentile-explained.html",          "priority": "0.7", "changefreq": "monthly"},
    {"url": "/articles/4-month-sleep-regression",                 "source": "articles/4-month-sleep-regression.html",           "priority": "0.7", "changefreq": "monthly"},
    {"url": "/articles/8-month-sleep-regression",                 "source": "articles/8-month-sleep-regression.html",           "priority": "0.7", "changefreq": "monthly"},
    {"url": "/articles/generations-by-year",                      "source": "articles/generations-by-year.html",                "priority": "0.6", "changefreq": "monthly"},

    # Step 5: /pregnancy/weeks-to-months/ hub + 42 per-week conversion leaves
    {"url": "/pregnancy/weeks-to-months/",                        "source": "pregnancy/weeks-to-months/index.html",             "priority": "0.7", "changefreq": "monthly"},
    {"url": "/pregnancy/weeks-to-months/23/",                     "source": "pregnancy/weeks-to-months/23/index.html",          "priority": "0.5", "changefreq": "monthly"},
    {"url": "/pregnancy/weeks-to-months/27/",                     "source": "pregnancy/weeks-to-months/27/index.html",          "priority": "0.5", "changefreq": "monthly"},
    {"url": "/pregnancy/weeks-to-months/28/",                     "source": "pregnancy/weeks-to-months/28/index.html",          "priority": "0.5", "changefreq": "monthly"},
    {"url": "/pregnancy/weeks-to-months/42/",                     "source": "pregnancy/weeks-to-months/42/index.html",          "priority": "0.5", "changefreq": "monthly"},

    # Methodology
    {"url": "/methodology/",                                      "source": "methodology/index.html",                           "priority": "0.8", "changefreq": "monthly"},
    {"url": "/methodology/due-date-calculator",                   "source": "methodology/due-date-calculator.html",             "priority": "0.8", "changefreq": "monthly"},
    {"url": "/methodology/conception-calculator",                 "source": "methodology/conception-calculator.html",           "priority": "0.8", "changefreq": "monthly"},
    {"url": "/methodology/ovulation-calculator",                  "source": "methodology/ovulation-calculator.html",            "priority": "0.8", "changefreq": "monthly"},
    {"url": "/methodology/period-calculator",                     "source": "methodology/period-calculator.html",               "priority": "0.8", "changefreq": "monthly"},
    {"url": "/methodology/baby-percentile",                       "source": "methodology/baby-percentile.html",                 "priority": "0.8", "changefreq": "monthly"},
    {"url": "/methodology/sleep-needs-by-age",                    "source": "methodology/sleep-needs-by-age.html",              "priority": "0.8", "changefreq": "monthly"},
    {"url": "/methodology/chinese-gender-chart",                  "source": "methodology/chinese-gender-chart.html",            "priority": "0.8", "changefreq": "monthly"},

    # Company
    {"url": "/about",                "source": "about.html",                "priority": "0.5", "changefreq": "yearly"},
    {"url": "/editorial-policy",     "source": "editorial-policy.html",     "priority": "0.5", "changefreq": "yearly"},
    {"url": "/privacy",              "source": "privacy.html",              "priority": "0.4", "changefreq": "yearly"},
    {"url": "/terms",                "source": "terms.html",                "priority": "0.4", "changefreq": "yearly"},
    {"url": "/disclaimer",           "source": "disclaimer.html",           "priority": "0.4", "changefreq": "yearly"},
    {"url": "/affiliate-disclosure", "source": "affiliate-disclosure.html", "priority": "0.4", "changefreq": "yearly"},
    {"url": "/contact",              "source": "contact.html",              "priority": "0.4", "changefreq": "yearly"},

    # Pregnancy week-by-week (Step 8 Batch 1A + 1B) — hub + leaves for weeks 4-17
    {"url": "/pregnancy/week-by-week/",                       "source": "pregnancy/week-by-week/index.html",                       "priority": "0.8", "changefreq": "monthly"},
    {"url": "/pregnancy/week-by-week/4-weeks-pregnant/",      "source": "pregnancy/week-by-week/4-weeks-pregnant/index.html",      "priority": "0.7", "changefreq": "monthly"},
    {"url": "/pregnancy/week-by-week/5-weeks-pregnant/",      "source": "pregnancy/week-by-week/5-weeks-pregnant/index.html",      "priority": "0.7", "changefreq": "monthly"},
    {"url": "/pregnancy/week-by-week/6-weeks-pregnant/",      "source": "pregnancy/week-by-week/6-weeks-pregnant/index.html",      "priority": "0.7", "changefreq": "monthly"},
    {"url": "/pregnancy/week-by-week/7-weeks-pregnant/",      "source": "pregnancy/week-by-week/7-weeks-pregnant/index.html",      "priority": "0.7", "changefreq": "monthly"},
    {"url": "/pregnancy/week-by-week/8-weeks-pregnant/",      "source": "pregnancy/week-by-week/8-weeks-pregnant/index.html",      "priority": "0.7", "changefreq": "monthly"},
    {"url": "/pregnancy/week-by-week/9-weeks-pregnant/",      "source": "pregnancy/week-by-week/9-weeks-pregnant/index.html",      "priority": "0.7", "changefreq": "monthly"},
    {"url": "/pregnancy/week-by-week/10-weeks-pregnant/",     "source": "pregnancy/week-by-week/10-weeks-pregnant/index.html",     "priority": "0.7", "changefreq": "monthly"},
    {"url": "/pregnancy/week-by-week/11-weeks-pregnant/",     "source": "pregnancy/week-by-week/11-weeks-pregnant/index.html",     "priority": "0.7", "changefreq": "monthly"},
    {"url": "/pregnancy/week-by-week/12-weeks-pregnant/",     "source": "pregnancy/week-by-week/12-weeks-pregnant/index.html",     "priority": "0.7", "changefreq": "monthly"},
    {"url": "/pregnancy/week-by-week/13-weeks-pregnant/",     "source": "pregnancy/week-by-week/13-weeks-pregnant/index.html",     "priority": "0.7", "changefreq": "monthly"},
    {"url": "/pregnancy/week-by-week/14-weeks-pregnant/",     "source": "pregnancy/week-by-week/14-weeks-pregnant/index.html",     "priority": "0.7", "changefreq": "monthly"},
    {"url": "/pregnancy/week-by-week/15-weeks-pregnant/",     "source": "pregnancy/week-by-week/15-weeks-pregnant/index.html",     "priority": "0.7", "changefreq": "monthly"},
    {"url": "/pregnancy/week-by-week/16-weeks-pregnant/",     "source": "pregnancy/week-by-week/16-weeks-pregnant/index.html",     "priority": "0.7", "changefreq": "monthly"},
    {"url": "/pregnancy/week-by-week/17-weeks-pregnant/",     "source": "pregnancy/week-by-week/17-weeks-pregnant/index.html",     "priority": "0.7", "changefreq": "monthly"},
]

# HTML files that exist in dist/ but are explicitly NOT listed in the
# sitemap. If you add an HTML file to dist/, it must either be in
# URL_MAP above or here, or the refresh script will error.
EXCLUDED_FROM_SITEMAP = {
    "404.html",
    # Step 4 names-cluster staging directories — gated on G1A/G2A licensing
    # review before any names page can ship. Excluded from sitemap until
    # then so they don't get indexed.
    "names-pilot-staging/charlotte/index.html",
    "names-pilot-staging/liam/index.html",
    "names-pilot-staging/olivia/index.html",
    "names-staging/charlotte/index.html",
    "names-staging/liam/index.html",
    "names-staging/olivia/index.html",
    # W2M silent-tail leaves — noindex,follow on 38 leaves with zero GSC
    # impressions in the first 6 days post-launch (2026-04-29 deploy).
    # Removed from sitemap 2026-05-05 per AdSense resubmit prep, R2 reviewer
    # SHIP-WITH-PATCHES disposition. Hub + Weeks 23/27/28/42 stay indexed.
    "pregnancy/weeks-to-months/1/index.html",
    "pregnancy/weeks-to-months/2/index.html",
    "pregnancy/weeks-to-months/3/index.html",
    "pregnancy/weeks-to-months/4/index.html",
    "pregnancy/weeks-to-months/5/index.html",
    "pregnancy/weeks-to-months/6/index.html",
    "pregnancy/weeks-to-months/7/index.html",
    "pregnancy/weeks-to-months/8/index.html",
    "pregnancy/weeks-to-months/9/index.html",
    "pregnancy/weeks-to-months/10/index.html",
    "pregnancy/weeks-to-months/11/index.html",
    "pregnancy/weeks-to-months/12/index.html",
    "pregnancy/weeks-to-months/13/index.html",
    "pregnancy/weeks-to-months/14/index.html",
    "pregnancy/weeks-to-months/15/index.html",
    "pregnancy/weeks-to-months/16/index.html",
    "pregnancy/weeks-to-months/17/index.html",
    "pregnancy/weeks-to-months/18/index.html",
    "pregnancy/weeks-to-months/19/index.html",
    "pregnancy/weeks-to-months/20/index.html",
    "pregnancy/weeks-to-months/21/index.html",
    "pregnancy/weeks-to-months/22/index.html",
    "pregnancy/weeks-to-months/24/index.html",
    "pregnancy/weeks-to-months/25/index.html",
    "pregnancy/weeks-to-months/26/index.html",
    "pregnancy/weeks-to-months/29/index.html",
    "pregnancy/weeks-to-months/30/index.html",
    "pregnancy/weeks-to-months/31/index.html",
    "pregnancy/weeks-to-months/32/index.html",
    "pregnancy/weeks-to-months/33/index.html",
    "pregnancy/weeks-to-months/34/index.html",
    "pregnancy/weeks-to-months/35/index.html",
    "pregnancy/weeks-to-months/36/index.html",
    "pregnancy/weeks-to-months/37/index.html",
    "pregnancy/weeks-to-months/38/index.html",
    "pregnancy/weeks-to-months/39/index.html",
    "pregnancy/weeks-to-months/40/index.html",
    "pregnancy/weeks-to-months/41/index.html",
}
