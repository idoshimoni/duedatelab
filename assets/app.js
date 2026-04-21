/* DueDateLab — shared UI behavior
   Header/drawer, cookie consent, GA4 loader (Consent Mode v2), share widget.
   No framework, no build. */
(function () {
  'use strict';

  // ── Config ───────────────────────────────────────────
  // Replace with real Measurement ID once the GA4 property is created.
  var GA4_ID = 'G-PG9K79G7RK';
  var CONSENT_KEY = 'pl-consent';   // 'granted' | 'denied'
  var LEGACY_KEY  = 'pl-cookie';    // old key, migrated once then removed

  // ── Consent Mode v2 defaults (must run before gtag.js) ───
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

  // ── Consent helpers ──────────────────────────────────
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

  // ── GA4 loader (only fires after consent is granted) ───
  function loadGA4() {
    if (window.__ga4Loaded) return;
    if (!GA4_ID || GA4_ID.indexOf('G-') !== 0 || GA4_ID === 'G-PG9K79G7RK') return;
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

  // ── Mobile drawer ────────────────────────────────────
  function initDrawer() {
    var btn = document.querySelector('[data-drawer-toggle]');
    var drawer = document.querySelector('[data-drawer]');
    if (!btn || !drawer) return;
    btn.addEventListener('click', function () {
      var open = drawer.classList.toggle('open');
      btn.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
  }

  // ── Cookie banner ────────────────────────────────────
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

  // Expose helpers (shared namespace)
  window.PL = window.PL || {};

  // Optional: future "Manage consent" link can call this to reopen the banner.
  window.PL.resetConsent = function () {
    localStorage.removeItem(CONSENT_KEY);
    var banner = document.querySelector('[data-cookie]');
    if (banner) banner.classList.remove('hidden');
  };

  // ── Share widget ─────────────────────────────────────
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

  // ── DOM ready ────────────────────────────────────────
  function ready(fn) {
    if (document.readyState !== 'loading') fn();
    else document.addEventListener('DOMContentLoaded', fn);
  }
  ready(function () { initDrawer(); initCookie(); initShare(); });

  // ── Date helpers ─────────────────────────────────────
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
