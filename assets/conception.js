/* Conception Calculator — 4 modes.
   LMP: conception ≈ LMP + 14d (adjusted for cycle length).
   Ultrasound: conception ≈ scan date − (gestational age − 2 weeks).
   IVF: conception = transfer date − (5 if blastocyst, 3 if day-3). Due date = transfer + 266 - embryo age.
   Reverse (from birthday): conception ≈ birth − 266.
*/
(function () {
  'use strict';
  var form = document.getElementById('con-form');
  if (!form) return;
  var result = document.getElementById('con-result');
  var resultBig = document.getElementById('con-big');
  var resultExpl = document.getElementById('con-expl');
  var resultStats = document.getElementById('con-stats');
  var resultTrack = document.getElementById('con-track');
  var errMsg = document.getElementById('con-err');

  var fields = {
    lmp: document.getElementById('con-field-lmp'),
    us: document.getElementById('con-field-us'),
    ivf: document.getElementById('con-field-ivf'),
    birth: document.getElementById('con-field-birth'),
  };

  function setMode(m) {
    Object.keys(fields).forEach(function (k) { fields[k].classList.toggle('hidden', k !== m); });
  }
  form.querySelectorAll('input[name="conmode"]').forEach(function (r) {
    r.addEventListener('change', function () { setMode(r.value); });
  });
  setMode('lmp');

  form.addEventListener('submit', function (e) {
    e.preventDefault();
    errMsg.textContent = '';
    var mode = form.querySelector('input[name="conmode"]:checked').value;
    var conception, dueDate, lmp;

    if (mode === 'lmp') {
      var lmpVal = form.elements['lmp'].value;
      if (!lmpVal) { errMsg.textContent = 'Pick the first day of your last period.'; return; }
      lmp = new Date(lmpVal + 'T00:00:00');
      var cycle = parseInt(form.elements['cycle'].value, 10) || 28;
      conception = PL.addDays(lmp, 14 + (cycle - 28));
      dueDate = PL.addDays(lmp, 280 + (cycle - 28));
    } else if (mode === 'us') {
      var usVal = form.elements['usdate'].value;
      var gw = parseInt(form.elements['usweeks'].value, 10);
      var gd = parseInt(form.elements['usdays'].value, 10) || 0;
      if (!usVal) { errMsg.textContent = 'Pick the ultrasound date.'; return; }
      if (!(gw >= 4 && gw <= 42)) { errMsg.textContent = 'Gestational weeks must be 4–42.'; return; }
      var scanDate = new Date(usVal + 'T00:00:00');
      var gaDays = gw * 7 + gd;
      lmp = PL.addDays(scanDate, -gaDays);
      conception = PL.addDays(lmp, 14);
      dueDate = PL.addDays(lmp, 280);
    } else if (mode === 'ivf') {
      var tVal = form.elements['transfer'].value;
      var embryoAge = parseInt(form.elements['embryo'].value, 10);
      if (!tVal) { errMsg.textContent = 'Pick the transfer date.'; return; }
      var transfer = new Date(tVal + 'T00:00:00');
      conception = PL.addDays(transfer, -embryoAge);
      dueDate = PL.addDays(conception, 266);
      lmp = PL.addDays(conception, -14);
    } else if (mode === 'birth') {
      var bVal = form.elements['birth'].value;
      if (!bVal) { errMsg.textContent = 'Pick your child\u2019s birth date.'; return; }
      var birth = new Date(bVal + 'T00:00:00');
      conception = PL.addDays(birth, -266);
      lmp = PL.addDays(conception, -14);
      dueDate = birth;
    }

    if (!conception || isNaN(conception)) { errMsg.textContent = 'Couldn\u2019t calculate. Please check your inputs.'; return; }

    var today = new Date(); today.setHours(0,0,0,0);
    var fertileStart = PL.addDays(conception, -5);
    var fertileEnd = PL.addDays(conception, 1);

    resultBig.innerHTML = PL.formatDate(conception);
    resultExpl.innerHTML = 'Fertile window: <b>' + PL.shortDate(fertileStart) + '</b> – <b>' + PL.shortDate(fertileEnd) + '</b>.';

    resultStats.innerHTML =
      stat(PL.shortDate(conception), 'Conceived') +
      stat(PL.shortDate(dueDate), 'Due date') +
      stat(PL.shortDate(fertileStart) + ' – ' + PL.shortDate(fertileEnd), 'Fertile window');

    // Timeline: LMP (0) → conception (~14) → today → due (280)
    var daysFromLmp = PL.diffDays(today, lmp);
    var pct = Math.max(0, Math.min(100, (daysFromLmp / 280) * 100));
    var concPct = (PL.diffDays(conception, lmp) / 280) * 100;
    resultTrack.innerHTML =
      '<div class="pl-timeline-seg" style="left:0;width:' + pct + '%"></div>' +
      '<div class="pl-timeline-marker" style="left:' + concPct + '%; background:#1A2E4A;" title="Conception"></div>' +
      (daysFromLmp >= 0 && daysFromLmp <= 280 ? '<div class="pl-timeline-marker" style="left:' + pct + '%;" title="Today"></div>' : '');

    result.classList.remove('hidden');
    result.scrollIntoView({ behavior: 'smooth', block: 'start' });

    if (window.gtag) {
      window.gtag('event', 'calculator_submit', { tool: 'conception' });
      window.gtag('event', 'conception_estimated', {
        mode: mode
      });
    }
  });

  function stat(num, label) {
    return '<div class="pl-stat"><div class="pl-stat-num">' + num + '</div><div class="pl-stat-label">' + label + '</div></div>';
  }

  var tryagain = document.getElementById('con-tryagain');
  if (tryagain) tryagain.addEventListener('click', function (e) { e.preventDefault(); result.classList.add('hidden'); form.reset(); setMode('lmp'); window.PL.scrollToTop(); });
})();
