# dist/scripts

Site-maintenance scripts for the DueDateLab static site.

## What is here

- `sitemap_urls.py` — source of truth for sitemap.xml contents (URL, source HTML file, priority, changefreq). Edit this when adding or retiring a page.
- `refresh_dates.py` — updates freshness-date fields across all HTML and regenerates sitemap.xml. Idempotent.
- `pre-commit` — git hook. Calls `refresh_dates.py --staged` before every commit so dates never drift.
- `install_hooks.sh` — one-shot install step that copies `pre-commit` into `.git/hooks/pre-commit`.

## One-time setup on a fresh clone

```
bash scripts/install_hooks.sh
```

## Daily use

You do not run anything. Edit pages as usual, commit as usual. The hook calls `refresh_dates.py --staged`, which:

- Rewrites visible `Last updated`, JSON-LD `dateModified`, JSON-LD `lastReviewed`, `og:article:modified_time`, and visible `Last reviewed` `<time>` fields on every staged HTML file to today's date
- Regenerates `sitemap.xml` from `sitemap_urls.py` using the last-commit date of each source HTML as `<lastmod>`
- Re-stages any modified files so the commit captures the refreshed dates

## What is preserved

The script never touches `datePublished`, `article:published_time`, or visible `Published Month DD, YYYY` lines. The original publish date must not drift.

## Adding a new page

1. Drop the HTML in the right directory under `dist/`.
2. Open `scripts/sitemap_urls.py` and append an entry to `URL_MAP` (or to `EXCLUDED_FROM_SITEMAP` if it should not be indexed).
3. Commit. The hook will set the freshness dates, populate the sitemap, and set `<lastmod>` from git.

If you forget step 2, the next commit will fail with a clear `HTML file not mapped: ...` error before accepting the change.

## Manual refresh

You rarely need this, but:

```
python3 scripts/refresh_dates.py --all      # refresh every HTML in dist/
python3 scripts/refresh_dates.py --staged   # refresh only staged files (what the hook does)
python3 scripts/refresh_dates.py --check    # dry run; exit 1 if anything would change
```

## CI check (optional, recommended)

In CI, run:

```
python3 scripts/refresh_dates.py --check
```

A non-zero exit means someone pushed without the hook installed. That is the only failure mode this system cannot prevent on its own.
