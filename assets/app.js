/* DueDateLab — shared UI behavior
   Header/drawer, cookie consent, GA4 loader (Consent Mode v2), share widget.
   Custom .pl-cookie banner restored 2026-05-01: Google Funding Choices CMP
   is gated on AdSense site approval which is still pending, so the FC banner
   never fires for users. The custom banner provides immediate consent UI for
   all visitors and gates GA4 collection per user choice. When AdSense
   approves and Funding Choices begins firing, this file can be revisited.
   No framework, no build. */
(function () {
  'use strict';

  // ── Config ───────────────────────────────────────────────
  var GA4_ID = 'G-PG9K79G7RK';
  var CONSENT_KEY = 'pl-consent';   // 'granted' | 'denied'
  var LEGACY_KEY  = 'pl-cookie';    // pre-2026-04-21 key, migrated once

  // ── Consent Mode v2 defaults (must run before gtag.js) ──
  window.dataLayer = window.dataLayer || [];
  function gtag(){ window.dataLayer.push(arguments); }
  window.gtag = gtag;

  gtag('consent', 'default', {
    ad_storage: 'denied',
    ad_user_data: 'denied',
    ad_personalization: 'denied',
    analytics_storage: 'denied',
    functionality_storage: 'granted',
    security_storage: 'granted',
    wait_for_update: 500
  });

  // ── Consent helpers ──────────────────────────────────────
  function readConsent() { return localStorage.getItem(CONSENT_KEY); }

  function applyGranted() {
    gtag('consent', 'update', {
      ad_storage: 'granted',
      ad_user_data: 'granted',
      ad_personalization: 'granted',
      analytics_storage: 'granted'
    });
    loadGA4();
  }

  function applyDenied() {
    gtag('consent', 'update', {
      ad_storage: 'denied',
      ad_user_data: 'denied',
      ad_personalization: 'denied',
      analytics_storage: 'denied'
    });
  }

  function grantConsent() {
    localStorage.setItem(CONSENT_KEY, 'granted');
    try { localStorage.removeItem(LEGACY_KEY); } catch (e) {}
    applyGranted();
  }

  function denyConsent() {
    localStorage.setItem(CONSENT_KEY, 'denied');
    try { localStorage.removeItem(LEGACY_KEY); } catch (e) {}
    applyDenied();
  }

  // Migrate legacy "pl-cookie = accepted" users once.
  if (!readConsent() && localStorage.getItem(LEGACY_KEY) === 'accepted') {
    grantConsent();
  }

  // ── GA4 loader (only fires after consent is granted) ─────
  function loadGA4() {
    if (window.__ga4Loaded) return;
    if (!GA4_ID || GA4_ID.indexOf('G-') !== 0) return;
    window.__ga4Loaded = true;

    gtag('js', new Date());
    gtag('config', GA4_ID, { anonymize_ip: true });

    var s = document.createElement('script');
    s.async = true;
    s.src = 'https://www.googletagmanager.com/gtag/js?id=' + encodeURIComponent(GA4_ID);
    document.head.appendChild(s);
  }

  // Apply stored consent immediately on load.
  if (readConsent() === 'granted') applyGranted();
  else if (readConsent() === 'denied') applyDenied();

  // ── Cookie banner ────────────────────────────────────────
  function initCookie() {
    var banner = document.querySelector('[data-cookie]');
    if (!banner) return;
    // If user has made a choice already, hide the banner.
    if (readConsent()) { banner.classList.add('hidden'); return; }

    banner.querySelectorAll('[data-cookie-dismiss]').forEach(function (el) {
      el.addEventListener('click', function () {
        if (el.classList.contains('accept')) grantConsent();
        else denyConsent();
        banner.classList.add('hidden');
      });
    });
  }

  // (Old initDrawer() removed: the OLD flat-nav drawer is replaced by the v4
  // canonical block's pl-mobile-header + pl-drawer disclosure pattern. The
  // hamburger + accordion handlers live in the v4 IIFE appended at the bottom
  // of this file.)

  // Shared namespace.
  window.PL = window.PL || {};

  // ── Share widget ────────────────────────────────────────
  // Share payload is composed at click time, not page load, so it reflects
  // whatever result is currently on screen. If the user hasn't run a
  // calculation yet (`.pl-result` hidden or missing), we fall back to the
  // page URL only. Calculator inputs never leave the browser, only the
  // result summary the user explicitly chose to share.
  //
  // On-screen copy addresses the viewer in second person ("You're about
  // 22 weeks along"). When shared, the recipient would read that as if it
  // were addressed to them. `personalize()` flips second person to first
  // person so the shared text reads like the sender is speaking about
  // themselves ("I'm about 22 weeks along").
  function personalize(t) {
    if (!t) return t;
    // Longer patterns first so contractions and "You are" don't collide
    // with the bare "You" rule.
    t = t.replace(/\bYou['\u2019]re\b/g, "I'm");
    t = t.replace(/\byou['\u2019]re\b/g, "I'm");
    t = t.replace(/\bYou are\b/g, "I am");
    t = t.replace(/\byou are\b/g, "I am");
    t = t.replace(/\bYour\b/g, "My");
    t = t.replace(/\byour\b/g, "my");
    t = t.replace(/\bYou\b/g, "I");
    t = t.replace(/\byou\b/g, "I");
    return t;
  }

  function getResultText() {
    var wrap = document.querySelector('.pl-result');
    if (!wrap || wrap.classList.contains('hidden')) return '';
    // Escape hatch: if the tool has built a full share sentence at compute
    // time (because its on-screen big/expl pair doesn't flow as plain text),
    // use that verbatim. Sleep Needs uses this because its big value is a
    // number with a small subtitle chip ("14-17 hours / 24h") that reads
    // awkwardly flattened.
    var override = wrap.getAttribute('data-share-override');
    if (override) return personalize(override);
    var big = wrap.querySelector('.pl-result-big');
    var expl = wrap.querySelector('.pl-result-expl');
    // Optional per-tool label. On the page, the headline gets visual
    // hierarchy from typography; in plain text it needs a short prefix
    // so the reader knows what the number or date represents.
    // Examples: "My due date: June 15, 2026" vs just "June 15, 2026".
    // Tools whose headline is already a complete thought (e.g. Chinese
    // Gender: "It's a boy") omit data-share-label.
    var label = wrap.getAttribute('data-share-label') || '';
    var parts = [];
    if (big) {
      var bt = (big.innerText || big.textContent || '').trim().replace(/\s+/g, ' ');
      if (bt) parts.push(label ? (label + ': ' + bt) : bt);
    }
    if (expl) {
      var et = (expl.innerText || expl.textContent || '').trim().replace(/\s+/g, ' ');
      if (et) parts.push(et);
    }
    return personalize(parts.join('. '));
  }

  function initShare() {
    // Copy link: URL only, so the user can paste into any message they want.
    document.querySelectorAll('[data-share-copy]').forEach(function (btn) {
      btn.addEventListener('click', function (e) {
        e.preventDefault();
        if (typeof window.gtag === 'function') {
          window.gtag('event', 'share_click', { method: 'copy', page_path: window.location.pathname });
        }
        navigator.clipboard && navigator.clipboard.writeText(window.location.href).then(function () {
          var prev = btn.getAttribute('title');
          btn.setAttribute('title', 'Copied!');
          btn.style.color = '#1E7F4F';
          setTimeout(function () { btn.setAttribute('title', prev); btn.style.color = ''; }, 1500);
        });
      });
    });
    // WhatsApp: prefill with result (if any) on two lines, then URL.
    document.querySelectorAll('[data-share-whatsapp]').forEach(function (a) {
      a.target = '_blank'; a.rel = 'noopener';
      // Fallback href for keyboard navigation / right-click copy.
      a.href = 'https://wa.me/?text=' + encodeURIComponent(window.location.href);
      a.addEventListener('click', function (e) {
        e.preventDefault();
        if (typeof window.gtag === 'function') {
          window.gtag('event', 'share_click', { method: 'whatsapp', page_path: window.location.pathname });
        }
        var r = getResultText();
        var payload = r ? (r + '\n\n' + window.location.href) : window.location.href;
        window.open('https://wa.me/?text=' + encodeURIComponent(payload), '_blank', 'noopener');
      });
    });
    // X: text param gets the result (or page title as fallback), url param gets the URL.
    document.querySelectorAll('[data-share-x]').forEach(function (a) {
      a.target = '_blank'; a.rel = 'noopener';
      a.href = 'https://twitter.com/intent/tweet?url=' + encodeURIComponent(window.location.href) + '&text=' + encodeURIComponent(document.title);
      a.addEventListener('click', function (e) {
        e.preventDefault();
        if (typeof window.gtag === 'function') {
          window.gtag('event', 'share_click', { method: 'x', page_path: window.location.pathname });
        }
        var text = getResultText() || document.title;
        var url = 'https://twitter.com/intent/tweet?url=' + encodeURIComponent(window.location.href) + '&text=' + encodeURIComponent(text);
        window.open(url, '_blank', 'noopener');
      });
    });
    // Save as PDF: opens the browser print dialog with a result-only view.
    // `body.pl-print-result-only` turns on the @media print rules that hide
    // header, form, nav, ads, FAQ, legal, footer, and the share buttons
    // themselves — so the saved PDF is just the headline result plus a
    // brand/URL footer. Class is removed on afterprint (and as a belt-and-
    // braces timeout) so the user's next regular Ctrl+P still prints the
    // full page.
    document.querySelectorAll('[data-share-image]').forEach(function (btn) {
      btn.addEventListener('click', function (e) {
        e.preventDefault();
        if (typeof window.gtag === 'function') {
          window.gtag('event', 'share_click', { method: 'pdf', page_path: window.location.pathname });
        }
        document.body.classList.add('pl-print-result-only');
        function cleanup() {
          document.body.classList.remove('pl-print-result-only');
          window.removeEventListener('afterprint', cleanup);
        }
        window.addEventListener('afterprint', cleanup);
        // Fallback: some mobile browsers don't fire afterprint reliably.
        setTimeout(cleanup, 5000);
        window.print();
      });
    });
  }

  // ── Logo click tracking ─────────────────────────────────
  // Fires a GA4 event when the DueDateLab logo is clicked, in either the
  // header or footer. Navigation to "/" is left to the anchor's native
  // behavior, so the event is a side effect, not a replacement. Consent
  // Mode v2 above governs whether this is a full or modeled ping.
  //   Targets both legacy ".pl-logo" and the new inline-SVG ".ddl-logo"
  //   so tracking works before and after the logo swap.
  function initLogoClick() {
    document.querySelectorAll('.pl-logo, .ddl-logo').forEach(function (a) {
      a.addEventListener('click', function () {
        if (typeof window.gtag !== 'function') return;
        var loc = a.closest('header') ? 'header'
                : a.closest('footer') ? 'footer'
                : 'other';
        window.gtag('event', 'logo_click', {
          link_location: loc,
          page_path: window.location.pathname
        });
      });
    });
  }

  // ── Outbound source click tracking ──────────────────────
  // Fires a GA4 event when a visitor clicks an outbound citation inside
  // .pl-sources (flagship tool <aside> or article <section>). Scope is
  // intentionally narrow: tracking every [target=_blank] anchor would
  // include nav/logo/share links and produce noisy data. The delegated
  // listener does not preventDefault so native navigation is untouched,
  // the event is a side effect. Consent Mode v2 defaults govern whether
  // this becomes a full or modeled ping.
  function initOutboundSourceClick() {
    document.addEventListener('click', function (e) {
      var t = e.target;
      var a = t && t.closest ? t.closest('.pl-sources a[target="_blank"]') : null;
      if (!a) return;
      if (typeof window.gtag !== 'function') return;
      var href = a.getAttribute('href') || '';
      var host = '';
      try { host = new URL(href, window.location.href).host; } catch (err) {}
      window.gtag('event', 'outbound_source_click', {
        source_url: href,
        source_host: host,
        page_path: window.location.pathname
      });
    });
  }

  // ── DOM ready ────────────────────────────────────────────
  function ready(fn) {
    if (document.readyState !== 'loading') fn();
    else document.addEventListener('DOMContentLoaded', fn);
  }
  ready(function () { initCookie(); initShare(); initLogoClick(); initOutboundSourceClick(); });

  // Optional: future "Manage consent" link can call this to reopen the banner.
  window.PL = window.PL || {};
  window.PL.resetConsent = function () {
    localStorage.removeItem(CONSENT_KEY);
    var banner = document.querySelector('[data-cookie]');
    if (banner) banner.classList.remove('hidden');
  };

  // ── Date helpers ─────────────────────────────────────────
  window.PL.formatDate = function (d) {
    if (!(d instanceof Date) || isNaN(d)) return '';
    return d.toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' });
  };
  window.PL.shortDate = function (d) {
    if (!(d instanceof Date) || isNaN(d)) return '';
    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };
  window.PL.addDays = function (d, n) { var x = new Date(d); x.setDate(x.getDate() + n); return x; };
  window.PL.diffDays = function (a, b) { return Math.round((a - b) / 86400000); };

  // ── Scroll helper ────────────────────────────────────────
  // Shared by every calculator's "Try again" button so the user is returned
  // to the top of the page on reset instead of being stranded mid-page where
  // the now-hidden result used to be. Uses rAF to let the DOM mutations that
  // immediately precede it (form.reset(), result.classList.add('hidden'))
  // commit first, otherwise mobile Safari cancels the smooth scroll when the
  // page height shrinks mid-animation.
  window.PL.scrollToTop = function () {
    requestAnimationFrame(function () {
      try {
        window.scrollTo({ top: 0, left: 0, behavior: 'smooth' });
      } catch (e) {
        window.scrollTo(0, 0);
      }
    });
  };
})();/* DueDateLab — nav interactions (v2)
 * W3C Disclosure Navigation pattern:
 *   - Hover + click + Enter/Space toggles
 *   - Esc closes and returns focus to controlling button
 *   - Outside click closes
 *   - focusout outside the nav region closes
 *   - NO focus trap, NO required arrow keys, NO role="menu"
 *
 * Tracking events (consent-mode-gated; none send user inputs):
 *   nav_click, dropdown_open, drawer_open, drawer_section_toggle,
 *   calculator_start, result_next_step_click, footer_click
 *
 * Existing events preserved unchanged:
 *   calculator_submit, share_click, outbound_source_click,
 *   methodology_view, scroll_90, logo_click
 */
(function () {
  'use strict';

  // ── Helpers ───────────────────────────────────────────────
  function track(name, params) {
    if (typeof window.gtag === 'function') {
      try { window.gtag('event', name, params || {}); } catch (e) {}
    }
  }
  function pageRelative(href) {
    if (!href) return '';
    try {
      var u = new URL(href, window.location.origin);
      return u.pathname + (u.search || '') + (u.hash || '');
    } catch (e) { return href; }
  }

  // ── Desktop dropdowns (W3C disclosure-navigation) ─────────
  var nav = document.querySelector('.pl-nav');
  var navItems = document.querySelectorAll('.pl-nav-item[data-pl-dropdown]');
  var openItem = null;

  function closeAll() {
    navItems.forEach(function (item) {
      var trigger = item.querySelector('.pl-nav-link');
      var panel = item.querySelector('.pl-dropdown');
      if (!trigger || !panel) return;
      trigger.setAttribute('aria-expanded', 'false');
      panel.hidden = true;
    });
    openItem = null;
  }

  function openDropdown(item) {
    if (openItem && openItem !== item) closeAll();
    var trigger = item.querySelector('.pl-nav-link');
    var panel = item.querySelector('.pl-dropdown');
    if (!trigger || !panel) return;
    if (trigger.getAttribute('aria-expanded') === 'true') return;
    trigger.setAttribute('aria-expanded', 'true');
    panel.hidden = false;
    openItem = item;
    track('dropdown_open', { nav_label: item.getAttribute('data-nav-label') || '' });
  }

  navItems.forEach(function (item) {
    var trigger = item.querySelector('.pl-nav-link');
    var panel = item.querySelector('.pl-dropdown');
    if (!trigger || !panel) return;

    // Hover (desktop only — pointer:fine)
    var hoverTimer;
    if (window.matchMedia && window.matchMedia('(hover: hover) and (pointer: fine)').matches) {
      item.addEventListener('mouseenter', function () {
        clearTimeout(hoverTimer);
        openDropdown(item);
      });
      item.addEventListener('mouseleave', function () {
        hoverTimer = setTimeout(function () {
          if (openItem === item) closeAll();
        }, 140);
      });
    }

    // Click toggles (button) — Enter/Space activate the click event natively
    trigger.addEventListener('click', function (e) {
      e.preventDefault();
      var isOpen = trigger.getAttribute('aria-expanded') === 'true';
      if (isOpen) closeAll();
      else openDropdown(item);
    });

    // Esc on trigger or panel closes and returns focus
    trigger.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && trigger.getAttribute('aria-expanded') === 'true') {
        closeAll();
        trigger.focus();
      }
    });
    panel.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') {
        closeAll();
        trigger.focus();
      }
      // No arrow-key handling — Tab traverses naturally (no focus trap).
    });
  });

  // Outside click closes
  document.addEventListener('click', function (e) {
    if (!openItem) return;
    if (!openItem.contains(e.target)) closeAll();
  });

  // Focus leaving the OPEN ITEM closes (not just leaving the whole nav).
  // Catches Tab-out from a dropdown to a sibling nav button.
  if (nav) {
    nav.addEventListener('focusout', function (e) {
      if (!openItem) return;
      var next = e.relatedTarget;
      if (!next || !openItem.contains(next)) closeAll();
    });

    // Global nav Esc: close any open dropdown and return focus to its trigger.
    nav.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && openItem) {
        var trigger = openItem.querySelector('.pl-nav-link');
        closeAll();
        if (trigger) trigger.focus();
      }
    });
  }

  // Top-level nav link clicks (direct links + dropdown-item links + CTAs)
  document.querySelectorAll('.pl-nav-list a[href]').forEach(function (a) {
    a.addEventListener('click', function () {
      track('nav_click', {
        nav_area: 'desktop',
        nav_label: a.getAttribute('data-nav-label') || '',
        destination_path: pageRelative(a.getAttribute('href')),
      });
    });
  });

  // ── Mobile drawer ─────────────────────────────────────────
  var drawer = document.querySelector('[data-pl-drawer]');
  var hamburger = document.querySelector('[data-pl-hamburger]');

  if (hamburger && drawer) {
    hamburger.addEventListener('click', function () {
      var willOpen = drawer.hidden;
      drawer.hidden = !willOpen;
      hamburger.setAttribute('aria-expanded', willOpen ? 'true' : 'false');
      if (willOpen) {
        track('drawer_open', { page_path: window.location.pathname });
      }
    });
  }

  // Accordion section headers
  document.querySelectorAll('.pl-drawer-section-header').forEach(function (header) {
    header.addEventListener('click', function () {
      var id = header.getAttribute('aria-controls');
      var panel = id && document.getElementById(id);
      if (!panel) return;
      var expanded = header.getAttribute('aria-expanded') === 'true';
      header.setAttribute('aria-expanded', expanded ? 'false' : 'true');
      panel.hidden = expanded;
      track('drawer_section_toggle', {
        section_label: header.getAttribute('data-section-label') || '',
        expanded: !expanded,
      });
    });
    header.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') {
        // Esc collapses an open section and returns focus to header
        if (header.getAttribute('aria-expanded') === 'true') {
          header.click();
        }
      }
    });
  });

  // Drawer link clicks (priority + sublinks)
  document.querySelectorAll('.pl-drawer a[href]').forEach(function (a) {
    a.addEventListener('click', function () {
      track('nav_click', {
        nav_area: 'drawer',
        nav_label: a.getAttribute('data-nav-label') || '',
        destination_path: pageRelative(a.getAttribute('href')),
      });
    });
  });

  // ── Footer link tracking ──────────────────────────────────
  document.querySelectorAll('.pl-footer a[href][data-footer-section]').forEach(function (a) {
    a.addEventListener('click', function () {
      track('footer_click', {
        footer_section: a.getAttribute('data-footer-section'),
        destination_path: pageRelative(a.getAttribute('href')),
      });
    });
  });

  // ── Calculator instrumentation hooks ──────────────────────
  // calculator_start — fire on first input touch on a calculator page.
  // The `tool` value is read from <body data-calculator="period|ovulation|...">.
  var calcTool = document.body && document.body.getAttribute('data-calculator');
  if (calcTool) {
    var calcStartFired = false;
    var onFirstTouch = function () {
      if (calcStartFired) return;
      calcStartFired = true;
      track('calculator_start', { tool: calcTool });
      document.removeEventListener('input', onFirstTouch, true);
      document.removeEventListener('change', onFirstTouch, true);
    };
    document.addEventListener('input', onFirstTouch, true);
    document.addEventListener('change', onFirstTouch, true);
  }

  // result_next_step_click — fire from result-panel next-step modules.
  // Modules opt in via [data-next-step-module] on the wrapper and
  // [data-next-step-link] on the anchor. Wired here for forward-compat;
  // the modules themselves land on calculator pages in a separate task.
  //
  // Privacy: when a module exposes a static `data-destination-path` placeholder
  // on the anchor (e.g. the Due Date → weeks-to-months deep-link card writes
  // `/pregnancy/weeks-to-months/week/` while the user-facing href is the exact
  // gestational-week leaf `/pregnancy/weeks-to-months/N/`), prefer that
  // placeholder over the href so the GA4 payload never carries a user-derived
  // value. Modules without `data-destination-path` keep the prior behavior
  // and read `href` directly.
  document.querySelectorAll('[data-next-step-module] a[data-next-step-link]').forEach(function (a) {
    a.addEventListener('click', function () {
      var module = a.closest('[data-next-step-module]');
      track('result_next_step_click', {
        tool: (module && module.getAttribute('data-tool')) || calcTool || '',
        destination_path: pageRelative(a.getAttribute('data-destination-path') || a.getAttribute('href')),
        module_label: (module && module.getAttribute('data-next-step-module')) || '',
      });
    });
  });

  // affiliate_click — fire when a visitor clicks an affiliate link.
  // Privacy-safe: only static metadata about the placement and merchant.
  // Never includes calculator inputs, results, due dates, weeks, or any
  // user-derived value. Per research-AI rollout review 2026-04-27.
  document.querySelectorAll('a[data-affiliate-link]').forEach(function (a) {
    a.addEventListener('click', function () {
      var href = a.getAttribute('href') || '';
      var destination_domain = '';
      try { destination_domain = new URL(href, window.location.origin).hostname; } catch (e) {}
      track('affiliate_click', {
        affiliate_program: 'amazon_associates',
        merchant: a.getAttribute('data-affiliate-link') || 'unknown',
        placement: a.getAttribute('data-affiliate-placement') || '',
        asin: a.getAttribute('data-affiliate-asin') || '',
        destination_domain: destination_domain,
      });
    });
  });

  // affiliate_card_view — fire once per page-load when an affiliate card
  // section becomes at least 50% visible in the viewport. Provides the
  // denominator for measuring affiliate CTR. Uses IntersectionObserver
  // and disconnects after first fire to avoid double-counting on scroll
  // back. Per research-AI round-3 placement review 2026-04-28: do not
  // move the card yet, instrument first.
  if (typeof IntersectionObserver === 'function') {
    document.querySelectorAll('.pl-affiliate-card[id]').forEach(function (card) {
      var fired = false;
      var anchor = card.querySelector('a[data-affiliate-link]');
      var placement = anchor ? (anchor.getAttribute('data-affiliate-placement') || '') : '';
      var asin = anchor ? (anchor.getAttribute('data-affiliate-asin') || '') : '';
      var observer = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (!fired && entry.isIntersecting && entry.intersectionRatio >= 0.5) {
            fired = true;
            track('affiliate_card_view', {
              affiliate_program: 'amazon_associates',
              merchant: 'amazon',
              placement: placement,
              asin: asin,
            });
            observer.disconnect();
          }
        });
      }, { threshold: 0.5 });
      observer.observe(card);
    });
  }

  // ── Preserved events (unchanged) ──────────────────────────
  // calculator_submit, share_click, outbound_source_click,
  // methodology_view, scroll_90, logo_click are wired in their existing
  // call sites and are intentionally left untouched here.
})();
