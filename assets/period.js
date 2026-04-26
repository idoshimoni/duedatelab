/* Period Calculator
   Inputs:
     LMP (first day of last menstrual period), required
     Cycle length, 21 to 45 days (ACOG's normal adult range), default 28
     Period length, 2 to 8 days, default 5

   Core formulas:
     Next period     = LMP + cycle
     Ovulation day   = LMP + (cycle - 14)        (Lenton 1984, ACOG)
     Fertile window  = [ovulation - 5, ovulation] (Wilcox 1995)

   Step 3 v3 (2026-04-26-round3): renderer rewritten for the new pl-result
   panel + cycle-strip SVG visual + pl-next-steps. Computation is unchanged.

   NOTE on variable cycle length: the SVG strip is statically authored as a
   28-cell layout. For cycles ≠ 28 we map cycleDay → cellIndex via
   round((cycleDay - 1) * 28 / cycle). The fallback table carries the precise
   dates regardless. The 28-cell visual is the verified mock; broader cycles
   (21-45) are an accepted approximation in the visual layer.
*/
(function () {
  'use strict';
  var form = document.getElementById('pe-form');
  if (!form) return;
  var result = document.getElementById('pe-result');
  var visual = document.getElementById('pe-visual');
  var nextSteps = document.getElementById('pe-next-steps');
  var resultBig = document.getElementById('pe-big');
  var resultSub = document.getElementById('pe-sub');
  var statWindow = document.getElementById('pe-stat-window');
  var statCycle = document.getElementById('pe-stat-cycle');
  var errMsg = document.getElementById('pe-err');

  /* Inclusive cycle-day numbering: Day 1 = LMP day, Day 2 = LMP + 1, etc. */
  function cycleDay(date, lmp) {
    return PL.diffDays(date, lmp) + 1;
  }

  function hideResultBlocks() {
    if (result) result.classList.add('hidden');
    if (visual) visual.classList.add('hidden');
    if (nextSteps) nextSteps.classList.add('hidden');
  }

  /* Map a cycle day (1..cycle) to an SVG cell index (0..27) on the
     28-cell static strip. */
  function cellIndex(cycleDayN, cycle) {
    return Math.round((cycleDayN - 1) * 28 / cycle);
  }
  /* Cell layout: startX = 24, cellWidth = 24 (22 + 2 gap) per SVG authoring.
     bandX = 24 + cellIndex(startDay) * 24
     bandW = (cellIndex(endDay+1) - cellIndex(startDay)) * 24 — this gives a
       width that snaps to cell boundaries. */
  function cellX(cycleDayN, cycle) { return 24 + cellIndex(cycleDayN, cycle) * 24; }
  function cellSpan(startDay, endDay, cycle) {
    var startX = cellX(startDay, cycle);
    var endX = 24 + cellIndex(endDay + 1, cycle) * 24;
    return { x: startX, w: Math.max(22, endX - startX) };
  }

  function populateSvg(data) {
    var cycle = data.cycle, periodLen = data.periodLen;
    var lmp = data.lmp, currentPeriodEnd = data.currentPeriodEnd;
    var fertileStart = data.fertileStart, fertileEnd = data.fertileEnd;
    var ovulation = data.ovulation, nextPeriod = data.nextPeriod;
    var fertileStartDay = data.fertileStartDay;
    var fertileEndDay = data.fertileEndDay;
    var ovulationDay = data.ovulationDay;
    var nextPeriodDay = data.nextPeriodDay;

    /* Period band: days 1..periodLen. */
    var pBand = document.getElementById('pe-svg-period-band');
    if (pBand) {
      var p = cellSpan(1, periodLen, cycle);
      pBand.setAttribute('x', p.x);
      pBand.setAttribute('width', p.w);
    }

    /* Fertile band: inclusive cycle days derived from computed dates. */
    var fBand = document.getElementById('pe-svg-fertile-band');
    if (fBand) {
      var f = cellSpan(fertileStartDay, fertileEndDay, cycle);
      fBand.setAttribute('x', f.x);
      fBand.setAttribute('width', f.w);
    }

    /* Ovulation marker: inclusive cycle day derived from computed date.
       cx = cellX + 11 (cell centre). */
    var ovG = document.getElementById('pe-svg-ovulation');
    if (ovG) {
      var ovCx = cellX(ovulationDay, cycle) + 11;
      var circle = ovG.querySelector('circle');
      if (circle) circle.setAttribute('cx', ovCx);
      ovG.querySelectorAll('text').forEach(function (t) { t.setAttribute('x', ovCx); });
    }

    /* Date labels. */
    var pDates = document.getElementById('pe-svg-period-dates');
    if (pDates) pDates.textContent = PL.shortDate(lmp) + ' – ' + PL.shortDate(currentPeriodEnd);
    var fDates = document.getElementById('pe-svg-fertile-dates');
    if (fDates) fDates.textContent = PL.shortDate(fertileStart) + ' – ' + PL.shortDate(fertileEnd);
    var ovDate = document.getElementById('pe-svg-ovulation-date');
    if (ovDate) ovDate.textContent = 'Day ' + ovulationDay + ' · ' + PL.shortDate(ovulation);
    var nDate = document.getElementById('pe-svg-next-date');
    if (nDate) nDate.textContent = 'Day ' + nextPeriodDay + ' · ' + PL.shortDate(nextPeriod);

    var srDesc = document.querySelector('#pe-cs-desc');
    if (srDesc) {
      srDesc.textContent = 'Cycle strip starting ' + PL.formatDate(lmp) + '. Period covers days 1 to ' +
        periodLen + '. Estimated fertile window covers days ' + fertileStartDay + ' to ' + fertileEndDay +
        '. Estimated ovulation on day ' + ovulationDay + ' (' + PL.formatDate(ovulation) + '). Next period estimated on ' +
        PL.formatDate(nextPeriod) + '.';
    }
  }

  function populateFallbackTable(data) {
    var cycle = data.cycle, periodLen = data.periodLen;
    var lmp = data.lmp, currentPeriodEnd = data.currentPeriodEnd;
    var fertileStart = data.fertileStart, fertileEnd = data.fertileEnd;
    var ovulation = data.ovulation, nextPeriod = data.nextPeriod;
    var fertileStartDay = data.fertileStartDay;
    var fertileEndDay = data.fertileEndDay;
    var ovulationDay = data.ovulationDay;
    var nextPeriodDay = data.nextPeriodDay;
    var tbody = document.querySelector('#pe-fallback-table tbody');
    if (tbody) {
      tbody.innerHTML =
        '<tr><td>Period</td><td>1–' + periodLen + '</td><td>' + PL.shortDate(lmp) + ' – ' + PL.shortDate(currentPeriodEnd) + '</td></tr>' +
        '<tr><td>Estimated fertile window</td><td>' + fertileStartDay + '–' + fertileEndDay + '</td><td>' + PL.shortDate(fertileStart) + ' – ' + PL.shortDate(fertileEnd) + '</td></tr>' +
        '<tr><td>Estimated ovulation</td><td>' + ovulationDay + '</td><td>' + PL.shortDate(ovulation) + '</td></tr>' +
        '<tr><td>Next period (estimate)</td><td>' + nextPeriodDay + '</td><td>' + PL.shortDate(nextPeriod) + '</td></tr>';
    }
    var caption = document.getElementById('pe-fallback-caption');
    if (caption) caption.textContent = 'Cycle starting ' + PL.shortDate(lmp) + ' (' + cycle + '-day cycle)';
  }

  form.addEventListener('submit', function (e) {
    e.preventDefault();
    errMsg.textContent = '';
    hideResultBlocks();

    var lmpVal = form.elements['lmp'].value;
    if (!lmpVal) {
      errMsg.textContent = 'Pick the first day of your last period.';
      return;
    }
    var cycle = parseInt(form.elements['cycle'].value, 10);
    if (!(cycle >= 21 && cycle <= 45)) {
      errMsg.textContent = 'Cycle length must be between 21 and 45 days.';
      return;
    }
    var periodLen = parseInt(form.elements['period'].value, 10);
    if (isNaN(periodLen)) periodLen = 5;
    if (periodLen < 2) periodLen = 2;
    if (periodLen > 8) periodLen = 8;

    var lmp = new Date(lmpVal + 'T00:00:00');
    if (isNaN(lmp)) {
      errMsg.textContent = 'Couldn’t read that date. Please re-enter.';
      return;
    }
    var today0 = new Date(); today0.setHours(0, 0, 0, 0);
    if (lmp > today0) {
      errMsg.textContent = 'That date is in the future. Please enter the first day of your last period.';
      return;
    }

    var nextPeriod       = PL.addDays(lmp, cycle);
    var currentPeriodEnd = PL.addDays(lmp, periodLen - 1);
    var nextPeriodEnd    = PL.addDays(nextPeriod, periodLen - 1);
    var ovulation        = PL.addDays(lmp, cycle - 14);
    var fertileStart     = PL.addDays(ovulation, -5);
    var fertileEnd       = ovulation;

    /* Inclusive cycle-day numbering for user-facing labels. */
    var fertileStartDay = cycleDay(fertileStart, lmp);
    var fertileEndDay   = cycleDay(fertileEnd, lmp);
    var ovulationDay    = cycleDay(ovulation, lmp);
    var nextPeriodDay   = cycleDay(nextPeriod, lmp);

    /* Render. */
    resultBig.textContent = PL.formatDate(nextPeriod);
    if (resultSub) {
      resultSub.textContent = 'Based on a ' + PL.formatDate(lmp) + ' LMP, a ' + cycle + '-day cycle, and a ' + periodLen + '-day period.';
    }
    if (statWindow) statWindow.textContent = PL.shortDate(nextPeriod) + ' – ' + PL.shortDate(nextPeriodEnd);
    if (statCycle) statCycle.textContent = cycle + ' days · ' + periodLen + '-day period';

    populateSvg({
      cycle: cycle, periodLen: periodLen,
      lmp: lmp, currentPeriodEnd: currentPeriodEnd,
      fertileStart: fertileStart, fertileEnd: fertileEnd,
      ovulation: ovulation, nextPeriod: nextPeriod,
      fertileStartDay: fertileStartDay, fertileEndDay: fertileEndDay,
      ovulationDay: ovulationDay, nextPeriodDay: nextPeriodDay
    });
    populateFallbackTable({
      cycle: cycle, periodLen: periodLen, lmp: lmp,
      currentPeriodEnd: currentPeriodEnd,
      fertileStart: fertileStart, fertileEnd: fertileEnd,
      ovulation: ovulation, nextPeriod: nextPeriod,
      fertileStartDay: fertileStartDay, fertileEndDay: fertileEndDay,
      ovulationDay: ovulationDay, nextPeriodDay: nextPeriodDay
    });

    /* Dynamic figcaption update — reflects the user's actual cycle length. */
    var cap = document.getElementById('pe-cs-title');
    if (cap) cap.textContent = 'Period and next-period estimate (' + cycle + '-day cycle)';

    result.classList.remove('hidden');
    if (visual) visual.classList.remove('hidden');
    if (nextSteps) nextSteps.classList.remove('hidden');
    result.scrollIntoView({ behavior: 'smooth', block: 'start' });

    /* GA4 event: only fires if gtag was loaded and consent is granted. */
    if (window.gtag) {
      window.gtag('event', 'calculator_submit', { tool: 'period' });
    }
  });

  var tryagain = document.getElementById('pe-tryagain');
  if (tryagain) tryagain.addEventListener('click', function (e) {
    e.preventDefault();
    hideResultBlocks();
    form.reset();
    window.PL.scrollToTop();
  });
})();
