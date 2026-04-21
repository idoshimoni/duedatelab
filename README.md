# DueDateLab — Phase 1 production build

Five evidence-based pregnancy &amp; parenting calculators. Plain HTML + CSS + vanilla JS. No build step, no framework.

## File structure

```
dist/
├── index.html                    # Due Date calculator (doubles as the hub / homepage)
├── chinese-gender-chart.html
├── sleep-needs-by-age.html
├── baby-percentile.html
├── conception-calculator.html
├── about.html
├── privacy.html
├── terms.html
├── disclaimer.html
├── contact.html
├── 404.html
├── ads.txt                       # Placeholder until AdSense approval
├── robots.txt                    # Allows everything, points at sitemap
├── sitemap.xml                   # 10 public URLs, lastmod 2026-04-21
└── assets/
    ├── styles.css                # All styles. Brand tokens at the top in :root.
    ├── favicon.svg               # Navy + crimson "D" mark
    ├── app.js                    # Shared: drawer toggle, cookie banner, share widget
    ├── duedate.js                # Naegele's rule (280 days from LMP)
    ├── chinese-gender.js         # Lunar-age × lunar-month lookup
    ├── sleep.js                  # AAP/AASM age-bucket recommendations
    ├── percentile.js             # WHO LMS growth curves, 0–60 months
    └── conception.js             # 4-mode engine (LMP, ultrasound, IVF, reverse)
```

## Running locally

**Simplest:** open `dist/index.html` directly in a browser. Everything works from `file://` — no server required.

**Recommended for correct relative paths / favicons / future service workers:** serve the `dist/` folder statically.

```bash
# Python
cd dist && python3 -m http.server 8000

# Node
npx serve dist

# Any static host — drop the dist/ folder as-is
# (Vercel, Netlify, GitHub Pages, S3 + CloudFront, Cloudflare Pages)
```

Then visit `http://localhost:8000`.

## Dependencies

The only external dependency is **Google Fonts — Inter** (weights 400/500/600/700/800), loaded from `fonts.googleapis.com` via a `<link>` tag in each page's `<head>`.

If you need to self-host or run offline, download the Inter font family and swap the `<link>` for local `@font-face` declarations in `styles.css`.

No JS dependencies. No analytics library included — add your own where the `<!-- analytics -->` comment slot goes (or just drop a tag into each page's `<head>`).

## Brand tokens

All brand tokens live in `assets/styles.css` under the `:root` block at the top of the file. **Do not introduce new brand colors** — the brief locks the palette to navy + crimson + white. Support colors (backgrounds, borders, soft tints) are derived.

```css
:root {
  /* LOCKED brand tokens (brief §2.4) */
  --navy:    #1A2E4A;   /* primary — headers, text, structure */
  --crimson: #EC0D5C;   /* accent — CTAs, markers, wordmark accent dot, active state */
  --white:   #FFFFFF;

  /* Derived support palette — safe to adjust */
  --bg:           #F7F8FA;
  --surface:      #FFFFFF;
  --text:         #1A2E4A;  /* = navy */
  --text-soft:    #5A6B82;
  --border:       #E6EAF1;
  --crimson-dark: #C80A4E;  /* hover */
  --crimson-soft: #FDE6EE;  /* result-card background, chart row highlight */
}
```

### Usage rules
- **Navy** carries all structural/informational weight (header, body text, stat numbers).
- **Crimson** is rationed — use it only for CTAs, the active nav state, the chart prediction cell, the result-card top border, and the accent dot in the `DueDateLab` wordmark.
- **Inter** is the only typeface. Weights in use: 400, 500, 600, 700, 800.

## Calculator accuracy notes

- **Due date / conception:** Naegele's rule (40 weeks from LMP), adjusted linearly for cycle length. Matches every mainstream OB calculator.
- **Chinese Gender Chart:** Traditional 18–45 × 1–12 lookup. ~50% accurate by design — it's a novelty tool, not a predictor.
- **Sleep Needs:** AAP 2016 consensus statement (endorsed by AASM), bucketed by age.
- **Baby Percentile:** WHO Child Growth Standards, LMS values for weight-for-age and length-for-age, 0–24 months, both sexes. Z-scores converted to percentiles via Abramowitz & Stegun normal-CDF approximation.

## Legal / policy pages

Phase 1 ships with AdSense-compliant pages for:

- `about.html` — editorial standards, who we are
- `privacy.html` — GDPR/CCPA-aware, includes the Google AdSense disclosures reviewers check for
- `terms.html` — Terms of Service
- `disclaimer.html` — medical disclaimer (YMYL signal for AdSense)
- `contact.html` — contact methods, operating location, email-gated postal forwarding

**Before launch:** review every policy with a lawyer in your jurisdiction. The copy is a reasonable starting point, not legal advice.

## Sources

Each calculator links its primary sources in a dedicated `Sources` block below the explainer (ACOG, WHO, AAP, AASM, CDC, NICHD). The WHO LMS values in `percentile.js` were verified against the published tables (https://www.who.int/tools/child-growth-standards/standards) to 4 decimal places for 0 to 60 months, both sexes, weight-for-age and length/height-for-age.

## What's intentionally missing

- Analytics tag (add your own, GA4 or Plausible)
- Ad network snippets (placeholder slots render as dashed boxes)
- `ads.txt` publisher line (file exists at root with a placeholder comment; swap in the real `google.com, pub-XXXXXXXXXXXXXXXX, DIRECT, f08c47fec0942fa0` line once AdSense approves)
- `apple-touch-icon.png` (180 x 180) and `og-image.png` (1200 x 630) social/app icons, referenced by the SEO block in every page `<head>` but not yet committed. Produce in phase 2 with the design skill.

## Browser support

Modern evergreen browsers. Uses `fetch`, `classList`, `querySelectorAll`, `<input type="date">`, CSS custom properties, CSS grid. IE11 is not supported.
