# DueDateLab brand quickref

This is the short working reference for engineers touching the site. The
full guide lives in the design bot's brand.html; if anything here
contradicts the canonical brand.html, brand.html wins.

## Palette

| Token     | Hex       | Where it's used                              |
|-----------|-----------|----------------------------------------------|
| Navy      | `#1A2E4A` | Default text, headers, footer, body text     |
| Crimson   | `#EC0D5C` | Accent only: the dot, "Lab" in wordmark, CTA |
| Crimson+  | `#FDE6EE` | Soft crimson wash for backgrounds            |
| Bg        | `#F7F8FA` | Page background                              |
| White     | `#FFFFFF` | Reverse logo on navy, card backgrounds       |

Crimson is locked. Never recolor. Never use it for body text, links, or
decoration beyond the dot and the "Lab" syllable.

## Typography

Inter, weight 800 for the wordmark, letter-spacing `-0.3px`.
Header 28px desktop / 22px mobile. Body 20px / 16px. Footer 14px minimum.

## Logo

Canonical inline-SVG snippet (header, footer, any in-page use):

```html
<a class="ddl-logo" href="/" aria-label="DueDateLab home">
  <svg class="ddl-logo-mark" width="28" height="28" viewBox="0 0 64 64"
       aria-hidden="true" focusable="false">
    <path d="M8 46 Q 22 46, 28 32 T 50 14" stroke="currentColor"
          stroke-width="5" stroke-linecap="round" fill="none"/>
    <circle cx="50" cy="14" r="6" fill="#EC0D5C"/>
    <circle cx="8" cy="46" r="3.5" fill="currentColor"/>
  </svg>
  <span>DueDate<em>Lab</em></span>
</a>
```

`currentColor` flips the curve and small dot to whatever the parent text
color is. On the navy header/footer that resolves to white. On light
backgrounds it resolves to navy. The crimson dot stays crimson.

Clear space equals the mark height. Minimum wordmark width 14px.
Minimum mark (no wordmark) size 16px.

Do not:
- recolor the crimson accent
- apply gradients, outlines, drop shadows, or tints
- rotate, stretch, skew, or italicize
- place on busy photographs without a navy or white scrim

Reverse lockup (white stroke and small dot, crimson stays crimson) is
mandatory on any navy background.

## Asset inventory

Root (`/`):

- `favicon.svg` — 64x64 rounded-square, white bg, navy curve, crimson dot
- `favicon-16.png`, `favicon-32.png`, `favicon-48.png` — rasterized fallbacks
- `favicon.ico` — multi-resolution bundle (16/32/48)
- `favicon-navy.svg`, `favicon-navy-32.png` — navy variant for light UI
- `apple-touch-icon-180.png` — iOS home screen icon (180x180)
- `apple-touch-icon.svg` — SVG source
- `icon-192.png`, `icon-512.png` — PWA icons (referenced by site.webmanifest)
- `og-image.png` — 1200x630 social share card
- `site.webmanifest` — PWA manifest, theme-color `#1A2E4A`

`assets/`:

- `duedatelab-logo-horizontal.svg` — full wordmark for image contexts
  (email, OG fallbacks). Has inline `font-family` + `font-weight` so it
  renders standalone without a stylesheet.
- `duedatelab-logo-horizontal-reverse.svg` — white variant for dark backgrounds
- `duedatelab-logo-horizontal-1x.png`, `duedatelab-logo-horizontal-2x.png`
- `duedatelab-logo-horizontal-reverse-2x.png`
- `duedatelab-mark.svg`, `duedatelab-mark-reverse.svg` — mark only, no wordmark
- `duedatelab-mark-128.png`, `duedatelab-mark-512.png` — raster mark (JSON-LD publisher.logo uses the 512 variant)

## CSS reference

```css
.ddl-logo     { display: inline-flex; align-items: center; gap: 10px;
                font-weight: 800; font-size: 20px; line-height: 1;
                color: var(--navy); letter-spacing: -0.3px;
                text-decoration: none; }
.ddl-logo em  { font-style: normal; color: var(--crimson); }
.ddl-logo-mark{ flex: 0 0 auto; display: block; }
.ddl-logo-lg  { font-size: 22px; gap: 12px; }
.pl-header .ddl-logo, .pl-footer .ddl-logo { color: #fff; }
```

## Social and structured data

- `og:image` → `https://duedatelab.com/og-image.png` (1200x630)
- `og:image:alt` → "DueDateLab, Free, private pregnancy and parenting calculators"
- `twitter:card` → `summary_large_image`
- JSON-LD `publisher.logo.url` → `https://duedatelab.com/assets/duedatelab-mark-512.png`

## Analytics

Logo clicks fire a GA4 event `logo_click` with parameters
`link_location` (header or footer) and `page_path` (current URL path).
Register `link_location` as a custom dimension in GA4 Admin to filter
reports by source.
