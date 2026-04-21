/* Sleep Needs by Age — AAP recommendations (hours/24h). */
(function () {
  'use strict';
  // AAP/AASM consensus: [ageLabel, min-max total, min-max nap, naps/day, nightLength]
  var BUCKETS = [
    { lo: 0, hi: 3, label: '0–3 months (newborn)', total: '14–17', night: '8–9', naps: '3–5', napTotal: '6–8' },
    { lo: 4, hi: 11, label: '4–11 months (infant)', total: '12–16', night: '9–11', naps: '2–3', napTotal: '3–5' },
    { lo: 12, hi: 24, label: '1–2 years (toddler)', total: '11–14', night: '10–12', naps: '1–2', napTotal: '1–3' },
    { lo: 25, hi: 60, label: '3–5 years (preschool)', total: '10–13', night: '10–11', naps: '0–1', napTotal: '0–2' },
    { lo: 61, hi: 144, label: '6–12 years (school age)', total: '9–12', night: '9–12', naps: '0', napTotal: '0' },
    { lo: 145, hi: 216, label: '13–18 years (teen)', total: '8–10', night: '8–10', naps: '0', napTotal: '0' },
  ];

  function bucketFor(months) {
    for (var i = 0; i < BUCKETS.length; i++) if (months >= BUCKETS[i].lo && months <= BUCKETS[i].hi) return BUCKETS[i];
    return null;
  }

  var form = document.getElementById('sleep-form');
  if (!form) return;
  var result = document.getElementById('sleep-result');
  var resultBig = document.getElementById('sleep-big');
  var resultExpl = document.getElementById('sleep-expl');
  var resultStats = document.getElementById('sleep-stats');
  var errMsg = document.getElementById('sleep-err');

  form.addEventListener('submit', function (e) {
    e.preventDefault();
    errMsg.textContent = '';
    var unit = form.elements['unit'].value;
    var val = parseFloat(form.elements['age'].value);
    if (!val && val !== 0) { errMsg.textContent = 'Enter your child\u2019s age.'; return; }
    var months = unit === 'years' ? val * 12 : val;
    if (months < 0 || months > 216) { errMsg.textContent = 'Age must be between 0 months and 18 years.'; return; }
    var b = bucketFor(months);
    if (!b) { errMsg.textContent = 'Couldn\u2019t find a match for that age.'; return; }

    resultBig.innerHTML = b.total + ' <span style="font-size:0.45em;font-weight:600;color:#5A6B82;">hours / 24h</span>';
    resultExpl.textContent = b.label + '. AAP-recommended total including naps.';
    resultStats.innerHTML =
      stat(b.night + 'h', 'Overnight') +
      stat(b.napTotal + 'h', 'Naps') +
      stat(b.naps, 'Naps/day');

    // Share text: flip bucket label ("0-3 months (newborn)") so the category
    // leads, then state the recommendation. Reads better on WhatsApp / X
    // than the visual big + subtitle pair, where "14-17 hours / 24h" looks
    // like a fraction once flattened.
    var m = b.label.match(/^(.+?) \((.+?)\)$/);
    var catLabel = m ? (m[2].charAt(0).toUpperCase() + m[2].slice(1)) + ' (' + m[1] + ')' : b.label;
    var napsClause = b.naps === '0' ? '' : ', including naps';
    result.setAttribute('data-share-override',
      catLabel + ': ' + b.total + ' hours of sleep per day' + napsClause + ' (AAP).');

    result.classList.remove('hidden');
    result.scrollIntoView({ behavior: 'smooth', block: 'start' });

    if (window.gtag) {
      window.gtag('event', 'sleep_needs_viewed', {
        age_bucket: b.label
      });
    }
  });

  function stat(num, label) {
    return '<div class="pl-stat"><div class="pl-stat-num">' + num + '</div><div class="pl-stat-label">' + label + '</div></div>';
  }

  var tryagain = document.getElementById('sleep-tryagain');
  if (tryagain) tryagain.addEventListener('click', function (e) { e.preventDefault(); result.classList.add('hidden'); form.reset(); form.scrollIntoView({behavior:'smooth'}); });
})();
