/* DueDateLab — shared UI behavior
   Header/drawer, Consent Mode v2 defaults, GA4 loader, share widget.
   Consent UI is handled by Google's CMP (configured in AdSense), not by this
   file. The custom .pl-cookie banner has been removed to avoid double-render
   with Google's CMP on EEA/UK/CH traffic.
   No framework, no build. */
(function () {
  'use strict';

  var GA4_ID = 'G-PG9K79G7RK';

  // ── Consent Mode v2 defaults (must run before gtag.js) ──
  // Google's CMP will issue gtag('consent', 'update', ...) based on the user's
  // choice. Until then, personalized ads and analytics stay denied.
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

  // ── GA4 loader ──────────────────────────────────────────
  // gtag/js loads on every page. Consent Mode v2 defaults above keep
  // measurement gated until the CMP (or user) updates consent.
  (function loadGA4() {
    if (!GA4_ID || GA4_ID.indexOf('G-') !== 0) return;
    gtag('js', new Date());
    gtag('config', GA4_ID, { anonymize_ip: true });
    var s = document.createElement('script');
    s.async = true;
    s.src = 'https://www.googletagmanager.com/gtag/js?id=' + encodeURIComponent(GA4_ID);
    document.head.appendChild(s);
  })();

  // ── Mobile drawer ───────────────────────────────────────
  function initDrawer() {
    var btn = document.querySelector('[data-drawer-toggle]');
    var drawer = document.querySelector('[data-drawer]');
    if (!btn || !drawer) return;
    function closeDrawer() {
      drawer.classList.remove('open');
      btn.setAttribute('aria-expanded', 'false');
    }
    btn.addEventListener('click', function (e) {
      e.stopPropagation();
      var open = drawer.classList.toggle('open');
      btn.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
    // Close on link click (drawer dismisses when navigating)
    drawer.addEventListener('click', function (e) {
      if (e.target && e.target.tagName === 'A') closeDrawer();
    });
    // Close on outside tap
    document.addEventListener('click', function (e) {
      if (!drawer.classList.contains('open')) return;
      if (drawer.contains(e.target) || btn.contains(e.target)) return;
      closeDrawer();
    });
    // Close on Esc
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') closeDrawer();
    });
  }

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
    var big = wrap.querySelector('.pl-result-big');
    var expl = wrap.querySelector('.pl-result-expl');
    var parts = [];
    if (big) {
      var bt = (big.innerText || big.textContent || '').trim().replace(/\s+/g, ' ');
      if (bt) parts.push(bt);
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

  // ── DOM ready ────────────────────────────────────────────
  function ready(fn) {
    if (document.readyState !== 'loading') fn();
    else document.addEventListener('DOMContentLoaded', fn);
  }
  ready(function () { initDrawer(); initShare(); });

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
})();