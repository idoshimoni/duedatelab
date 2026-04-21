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
    btn.addEventListener('click', function () {
      var open = drawer.classList.toggle('open');
      btn.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
  }

  // Shared namespace.
  window.PL = window.PL || {};

  // ── Share widget ────────────────────────────────────────
  function initShare() {
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
    document.querySelectorAll('[data-share-whatsapp]').forEach(function (a) {
      a.href = 'https://wa.me/?text=' + encodeURIComponent(document.title + ' ' + window.location.href);
      a.target = '_blank'; a.rel = 'noopener';
    });
    document.querySelectorAll('[data-share-x]').forEach(function (a) {
      a.href = 'https://twitter.com/intent/tweet?url=' + encodeURIComponent(window.location.href) + '&text=' + encodeURIComponent(document.title);
      a.target = '_blank'; a.rel = 'noopener';
    });
    document.querySelectorAll('[data-share-image]').forEach(function (btn) {
      btn.addEventListener('click', function (e) {
        e.preventDefault();
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