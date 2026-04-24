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
    {"url": "/articles/first-trimester-week-by-week",             "source": "articles/first-trimester-week-by-week.html",       "priority": "0.7", "changefreq": "monthly"},
    {"url": "/articles/chinese-gender-chart-accuracy",            "source": "articles/chinese-gender-chart-accuracy.html",      "priority": "0.7", "changefreq": "monthly"},
    {"url": "/articles/sleep-regressions-by-month",               "source": "articles/sleep-regressions-by-month.html",         "priority": "0.7", "changefreq": "monthly"},
    {"url": "/articles/baby-percentile-explained",                "source": "articles/baby-percentile-explained.html",          "priority": "0.7", "changefreq": "monthly"},
    {"url": "/articles/4-month-sleep-regression",                 "source": "articles/4-month-sleep-regression.html",           "priority": "0.7", "changefreq": "monthly"},
    {"url": "/articles/8-month-sleep-regression",                 "source": "articles/8-month-sleep-regression.html",           "priority": "0.7", "changefreq": "monthly"},

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
    {"url": "/about",        "source": "about.html",        "priority": "0.5", "changefreq": "yearly"},
    {"url": "/privacy",      "source": "privacy.html",      "priority": "0.4", "changefreq": "yearly"},
    {"url": "/terms",        "source": "terms.html",        "priority": "0.4", "changefreq": "yearly"},
    {"url": "/disclaimer",   "source": "disclaimer.html",   "priority": "0.4", "changefreq": "yearly"},
    {"url": "/contact",      "source": "contact.html",      "priority": "0.4", "changefreq": "yearly"},
]

# HTML files that exist in dist/ but are explicitly NOT listed in the
# sitemap. If you add an HTML file to dist/, it must either be in
# URL_MAP above or here, or the refresh script will error.
EXCLUDED_FROM_SITEMAP = {
    "404.html",
}
