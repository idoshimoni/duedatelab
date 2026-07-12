// Cloudflare Pages middleware: hostname-canonicalization guard.
//
// The Pages project `duedatelab-v2` exposes a default `*.pages.dev` URL
// alongside the custom domains. Without this middleware that preview URL
// is publicly reachable, crawler-indexable, and serves the production
// AdSense + GA4 tags on a non-canonical hostname.
//
// This middleware fires on every edge request before any static asset is
// served. If the hostname is not in the allow-list, it returns a 301
// redirect to the same path on duedatelab.com, preserving query string
// and fragment. Idempotent for duedatelab.com and www.duedatelab.com,
// which fall through to next() and are served normally.
//
// Effects:
//   - duedatelab-v2.pages.dev/*           -> 301 https://duedatelab.com/*
//   - <commit>.duedatelab-v2.pages.dev/*  -> 301 https://duedatelab.com/*
//   - duedatelab.com/*                    -> served as before
//   - www.duedatelab.com/*                -> served as before (Cloudflare
//                                            page rule still handles the
//                                            www -> apex consolidation if
//                                            it is configured separately)

const ALLOWED_HOSTS = new Set([
  'duedatelab.com',
  'www.duedatelab.com',
]);

const CANONICAL_HOST = 'duedatelab.com';

export const onRequest = async ({ request, next }) => {
  const url = new URL(request.url);

  // Hostnames are case-insensitive per RFC 3986 / RFC 1035. Normalize
  // before the Set lookup so a request like `Duedatelab.com` is treated
  // the same as `duedatelab.com`.
  const hostname = url.hostname.toLowerCase();

  if (ALLOWED_HOSTS.has(hostname)) {
    // Retired Names clusters (production + pilot-staging): force a genuine
    // 410 Gone at the edge for every retired path and both slash variants.
    // Origin already returns 404 for these, but we guarantee a terminal,
    // cache-immune non-200 before next() consults any (stale) asset cache,
    // which also speeds Google's de-indexing of cached copies. `no-store`
    // keeps this response itself out of any cache.
    const p = url.pathname;
    if (
      p.startsWith('/names-pilot-staging/') ||
      p === '/names' || p.startsWith('/names/') ||
      p === '/methodology/names' || p.startsWith('/methodology/names/')
    ) {
      return new Response('410 Gone', {
        status: 410,
        headers: {
          'content-type': 'text/plain; charset=utf-8',
          'cache-control': 'no-store',
        },
      });
    }
    return next();
  }

  // Non-canonical host. 301 to the same path on the canonical domain.
  url.protocol = 'https:';
  url.hostname = CANONICAL_HOST;
  url.port = '';

  // 301 (Permanent) so search engines consolidate signal to the canonical
  // domain. Use 308 instead if a future POST endpoint should preserve
  // method semantics; today the site is static so 301 is correct.
  return Response.redirect(url.toString(), 301);
};
