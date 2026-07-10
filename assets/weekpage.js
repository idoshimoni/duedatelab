/* Week-by-week page interactivity (Phase 2, 2026-07-09).
   Three features, all device-local, nothing leaves the browser:
   1. "Your week" banner — if the Due Date Calculator saved an LMP on
      this device, greet the reader with their current week and a jump
      link. Includes a visible "forget" control that clears the data.
   2. Midwife-questions checklist — tick state persists per week in
      localStorage.
   3. Week navigator — highlights the current page's week (set
      server-side via aria-current; JS only scrolls it into view).
   All storage access is wrapped in try/catch: private-mode failures
   degrade silently to a static page. */
(function () {
  'use strict';

  function store(key, val) {
    try {
      if (val === undefined) return window.localStorage.getItem(key);
      if (val === null) { window.localStorage.removeItem(key); return null; }
      window.localStorage.setItem(key, val);
      return val;
    } catch (e) { return null; }
  }

  var m = window.location.pathname.match(/\/(\d+)-weeks-pregnant/);
  var pageWeek = m ? parseInt(m[1], 10) : null;

  /* 1. Your-week banner */
  var banner = document.getElementById('wk-mine');
  var lmpIso = store('ddl_lmp');
  if (banner && lmpIso) {
    var lmp = new Date(lmpIso + 'T00:00:00');
    if (!isNaN(lmp)) {
      var today = new Date(); today.setHours(0, 0, 0, 0);
      var days = Math.round((today - lmp) / 86400000);
      var wk = Math.floor(days / 7);
      if (days >= 0 && days <= 294) {
        var html = '';
        if (pageWeek !== null && wk === pageWeek) {
          html = '<strong>This is your week.</strong> You are around ' + wk + ' weeks today.';
        } else if (wk >= 4 && wk <= 17) {
          html = 'You are around <strong>week ' + wk + '</strong> today — <a href="/pregnancy/week-by-week/' + wk + '-weeks-pregnant/">see your week →</a>';
        } else if (wk >= 1 && wk <= 42) {
          html = 'You are around <strong>week ' + wk + '</strong> today — <a href="/pregnancy/weeks-to-months/' + wk + '/">what that means in months →</a>';
        }
        if (html) {
          banner.innerHTML = html +
            ' <span class="pl-mine-meta">From your calculator entry, saved only on this device · <button type="button" id="wk-forget">forget</button></span>';
          banner.classList.remove('hidden');
          var forget = document.getElementById('wk-forget');
          if (forget) forget.addEventListener('click', function () {
            store('ddl_lmp', null);
            banner.classList.add('hidden');
          });
        }
      }
    }
  }

  /* 2. Checklist persistence */
  var list = document.querySelector('.pl-checklist');
  if (list && pageWeek !== null) {
    var key = 'ddl_check_w' + pageWeek;
    var saved = (store(key) || '').split(',');
    list.querySelectorAll('input[type="checkbox"]').forEach(function (cb) {
      if (saved.indexOf(cb.getAttribute('data-ck')) !== -1) cb.checked = true;
      cb.addEventListener('change', function () {
        var on = [];
        list.querySelectorAll('input[type="checkbox"]').forEach(function (c) {
          if (c.checked) on.push(c.getAttribute('data-ck'));
        });
        store(key, on.join(','));
      });
    });
  }

  /* 3. Scroll current week into view in the navigator */
  var current = document.querySelector('.pl-weekstrip-list a[aria-current="page"]');
  if (current && current.scrollIntoView) {
    try { current.scrollIntoView({ block: 'nearest', inline: 'center' }); } catch (e) {}
  }
})();
