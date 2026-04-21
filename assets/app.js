/* DueDateLab — shared UI behavior
   Header/drawer, cookie banner, share widget. No framework, no build. */
(function () {
  'use strict';

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
    if (localStorage.getItem('pl-cookie') === 'accepted') { banner.classList.add('hidden'); return; }
    banner.querySelectorAll('[data-cookie-dismiss]').forEach(function (el) {
      el.addEventListener('click', function () {
        localStorage.setItem('pl-cookie', 'accepted');
        banner.classList.add('hidden');
      });
    });
  }

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

  // Expose helpers
  window.PL = window.PL || {};
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
