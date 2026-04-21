/* Due date from LMP — Naegele's rule (280 days from LMP).
   Also accepts conception date (+266 days) or known due date. */
(function () {
  'use strict';
  var form = document.getElementById('dd-form');
  if (!form) return;
  var result = document.getElementById('dd-result');
  var resultBig = document.getElementById('dd-big');
  var resultExpl = document.getElementById('dd-expl');
  var resultStats = document.getElementById('dd-stats');
  var resultTrack = document.getElementById('dd-track');
  var errMsg = document.getElementById('dd-err');
  var modeInputs = form.querySelectorAll('input[name="mode"]');
  var fieldLmp = document.getElementById('dd-field-lmp');
  var fieldConc = document.getElementById('dd-field-conc');
  var fieldDd = document.getElementById('dd-field-dd');
  var cycleInput = document.getElementById('dd-cycle');

  function setMode(m) {
    fieldLmp.classList.toggle('hidden', m !== 'lmp');
    fieldConc.classList.toggle('hidden', m !== 'conception');
    fieldDd.classList.toggle('hidden', m !== 'duedate');
    if (cycleInput) cycleInput.parentElement.classList.toggle('hidden', m !== 'lmp');
  }
  modeInputs.forEach(function (r) { r.addEventListener('change', function () { setMode(r.value); }); });
  setMode('lmp');

  form.addEventListener('submit', function (e) {
    e.preventDefault();
    errMsg.textContent = '';
    var mode = form.querySelector('input[name="mode"]:checked').value;
    var dueDate, conception, lmp;
    var today = new Date(); today.setHours(0,0,0,0);

    if (mode === 'lmp') {
      var lmpVal = form.elements['lmp'].value;
      if (!lmpVal) { errMsg.textContent = 'Pick the first day of your last period.'; return; }
      lmp = new Date(lmpVal + 'T00:00:00');
      var cycle = parseInt(cycleInput.value, 10) || 28;
      if (cycle < 20 || cycle > 45) { errMsg.textContent = 'Cycle length should be between 20 and 45 days.'; return; }
      dueDate = PL.addDays(lmp, 280 + (cycle - 28));
      conception = PL.addDays(lmp, 14 + (cycle - 28));
    } else if (mode === 'conception') {
      var cVal = form.elements['conception'].value;
      if (!cVal) { errMsg.textContent = 'Pick an estimated conception date.'; return; }
      conception = new Date(cVal + 'T00:00:00');
      dueDate = PL.addDays(conception, 266);
      lmp = PL.addDays(conception, -14);
    } else {
      var dVal = form.elements['duedate'].value;
      if (!dVal) { errMsg.textContent = 'Pick your due date.'; return; }
      dueDate = new Date(dVal + 'T00:00:00');
      conception = PL.addDays(dueDate, -266);
      lmp = PL.addDays(dueDate, -280);
    }

    if (isNaN(dueDate)) { errMsg.textContent = 'That date doesn\u2019t look right.'; return; }

    // How far along
    var daysPreg = PL.diffDays(today, lmp);
    var weeks = Math.floor(daysPreg / 7);
    var days = daysPreg - weeks * 7;
    var trimester = weeks < 13 ? 1 : (weeks < 27 ? 2 : 3);
    var daysToGo = PL.diffDays(dueDate, today);

    resultBig.textContent = PL.formatDate(dueDate);
    if (daysPreg < 0) {
      resultExpl.textContent = 'Estimated due date. Pregnancy starts once you miss your next period.';
    } else if (daysPreg > 294) {
      resultExpl.textContent = 'This date is in the past. Hope baby is here!';
    } else {
      resultExpl.textContent = 'You\u2019re about ' + weeks + ' weeks, ' + days + ' days along. Trimester ' + trimester + '.';
    }

    resultStats.innerHTML =
      stat(weeks + 'w ' + days + 'd', 'So far') +
      stat(Math.max(0, daysToGo) + ' days', 'To go') +
      stat('T' + trimester, 'Trimester') +
      stat(PL.shortDate(conception), 'Conceived ~');

    // Timeline
    var pct = Math.max(0, Math.min(100, (daysPreg / 280) * 100));
    resultTrack.innerHTML =
      '<div class="pl-timeline-seg" style="left:0;width:' + pct + '%"></div>' +
      '<div class="pl-timeline-marker" style="left:' + pct + '%"></div>';

    result.classList.remove('hidden');
    result.scrollIntoView({ behavior: 'smooth', block: 'start' });

    // GA4 event: only fires if gtag was loaded and consent is granted.
    if (window.gtag) {
      window.gtag('event', 'due_date_calculated', {
        mode: mode,
        trimester: trimester
      });
    }
  });

  function stat(num, label) {
    return '<div class="pl-stat"><div class="pl-stat-num">' + num + '</div><div class="pl-stat-label">' + label + '</div></div>';
  }

  var tryagain = document.getElementById('dd-tryagain');
  if (tryagain) tryagain.addEventListener('click', function (e) { e.preventDefault(); result.classList.add('hidden'); form.reset(); setMode('lmp'); form.scrollIntoView({behavior:'smooth'}); });
})();
