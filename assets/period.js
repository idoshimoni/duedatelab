/* Period Calculator
   Inputs:
     LMP (first day of last menstrual period), required
     Cycle length, 21 to 45 days (ACOG's normal adult range), default 28
     Period length, 2 to 8 days, default 5

   Core formulas:
     Next period     = LMP + cycle
     Ovulation day   = LMP + (cycle - 14)        (Lenton 1984, ACOG)
     Fertile window  = [ovulation - 5, ovulation] (Wilcox 1995)

   Step 3.1 (2026-04-26-round1): SVG geometry now scales to the actual cycle
   length. stripMetrics(cycle) computes cellW = 672 / cycle from the strip
   anchor (left=24, width=672), so cell positions are correct for any cycle
   length 21..45. Day-tick labels and background cells regenerate dynamically.
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

  /* Strip metrics — scales cell width to the actual cycle length so the
     visual geometry agrees with the text and the calendar dates regardless
     of cycle length. The SVG anchors are: left=24, total cell-strip width
     = 672 (originally 28 * 24). */
  var SVG_NS = 'http://www.w3.org/2000/svg';
  function clampDay(day, cycle) {
    return Math.max(1, Math.min(cycle, day));
  }
  function stripMetrics(cycle) {
    var left = 24;
    var width = 672;
    var cellW = width / cycle;
    return { left: left, width: width, cellW: cellW };
  }
  function cellX(day, cycle) {
    var m = stripMetrics(cycle);
    var d = clampDay(day, cycle);
    return m.left + (d - 1) * m.cellW;
  }
  function cellCenterX(day, cycle) {
    var m = stripMetrics(cycle);
    return cellX(day, cycle) + (m.cellW / 2);
  }
  function cellSpan(startDay, endDay, cycle) {
    var m = stripMetrics(cycle);
    var start = clampDay(startDay, cycle);
    var end = clampDay(endDay, cycle);
    var x = cellX(start, cycle);
    var w = ((end - start) + 1) * m.cellW;
    return { x: x, w: w };
  }

  /* Mobile cycle-strip key — stacked legend shown on viewports <640px so
     inline labels above the strip don't collide. CSS hides this list at
     wider viewports; the cycle SVG carries the same information there. */
  function renderMobileKey(cycle, periodLen, fertileStart, fertileEnd, ovulation, nextPeriod) {
    var ul = document.getElementById('pe-cycle-mobile-key');
    if (!ul) return;
    ul.removeAttribute('hidden');
    ul.innerHTML =
      '<li><strong>Period:</strong> days 1–5</li>'.replace('1–5', '1–' + periodLen) +
      '<li><strong>Fertile window:</strong> days ' + fertileStart + '–' + fertileEnd + '</li>' +
      '<li><strong>Estimated ovulation:</strong> day ' + ovulation + '</li>' +
      '<li><strong>Next period:</strong> day ' + nextPeriod + '</li>';
  }

  /* Re-render the background cells + day-tick labels for the actual cycle.
     Replaces the static 1..28 grid baked into the SVG so cycles of any
     length (21..45) line up with the bands. */
  function renderCycleGrid(cycle) {
    var g = document.getElementById('pe-svg-grid');
    if (!g) return;
    while (g.firstChild) g.removeChild(g.firstChild);
    var m = stripMetrics(cycle);
    var rectW = Math.max(1, m.cellW - 2);
    var showEveryDay = cycle <= 32;
    for (var d = 1; d <= cycle; d++) {
      var x = m.left + (d - 1) * m.cellW;
      var stroke = (d <= 5 || (d >= 10 && d <= 15)) ? '#FFFFFF' : '#E6EAF1';
      var sw = (d <= 5 || (d >= 10 && d <= 15)) ? '2' : '1';
      var rect = document.createElementNS(SVG_NS, 'rect');
      rect.setAttribute('x', x);
      rect.setAttribute('y', 80);
      rect.setAttribute('width', rectW);
      rect.setAttribute('height', 48);
      rect.setAttribute('fill', 'none');
      rect.setAttribute('stroke', stroke);
      rect.setAttribute('stroke-width', sw);
      rect.setAttribute('rx', 4);
      g.appendChild(rect);
      if (!showEveryDay && d !== 1 && d % 5 !== 0 && d !== cycle) continue;
      var t = document.createElementNS(SVG_NS, 'text');
      t.setAttribute('x', x + rectW / 2);
      t.setAttribute('y', 159);
      t.setAttribute('text-anchor', 'middle');
      t.setAttribute('font-size', '11');
      t.setAttribute('fill', '#1A2E4A');
      t.setAttribute('font-weight', '500');
      t.textContent = String(d);
      g.appendChild(t);
    }
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

    /* Re-render the dynamic grid first so cells align with the user's cycle. */
    renderCycleGrid(cycle);

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

    /* Ovulation marker: cell centre at the ovulation cycle day. */
    var ovG = document.getElementById('pe-svg-ovulation');
    if (ovG) {
      var ovCx = cellCenterX(ovulationDay, cycle);
      var circle = ovG.querySelector('circle');
      if (circle) circle.setAttribute('cx', ovCx);
      ovG.querySelectorAll('text').forEach(function (t) { t.setAttribute('x', ovCx); });
    }

    /* Next-period marker: a cell-width rectangle pinned to the last cycle day
       (the user's "next period" sits the day after the cycle ends, but the
       in-strip visual is the right-most cycle day). */
    var nextG = document.getElementById('pe-svg-next');
    if (nextG) {
      var sm = stripMetrics(cycle);
      var nextRect = nextG.querySelector('rect');
      var nextCx = cellCenterX(cycle, cycle);
      if (nextRect) {
        nextRect.setAttribute('x', cellX(cycle, cycle) + 1);
        nextRect.setAttribute('width', Math.max(8, sm.cellW - 2));
      }
      nextG.querySelectorAll('text').forEach(function (t) { t.setAttribute('x', nextCx); });
    }

    /* Reposition inline marker labels so they stay above the right cells
       when the cycle scales. */
    var periodMidX = cellCenterX(Math.ceil(periodLen / 2), cycle);
    var fMid = Math.round((fertileStartDay + fertileEndDay) / 2);
    var fertileMidX = cellCenterX(fMid, cycle);
    var pTitle = document.getElementById('pe-svg-period-label');
    if (pTitle) pTitle.setAttribute('x', periodMidX);
    var fTitle = document.getElementById('pe-svg-fertile-label');
    if (fTitle) fTitle.setAttribute('x', fertileMidX);

    /* Date labels. */
    var pDates = document.getElementById('pe-svg-period-dates');
    if (pDates) {
      pDates.setAttribute('x', periodMidX);
      pDates.textContent = PL.shortDate(lmp) + ' – ' + PL.shortDate(currentPeriodEnd);
    }
    var fDates = document.getElementById('pe-svg-fertile-dates');
    if (fDates) {
      fDates.setAttribute('x', fertileMidX);
      fDates.textContent = PL.shortDate(fertileStart) + ' – ' + PL.shortDate(fertileEnd);
    }
    var ovDate = document.getElementById('pe-svg-ovulation-date');
    if (ovDate) ovDate.textContent = 'Day ' + ovulationDay + ' · ' + PL.shortDate(ovulation);
    var nDate = document.getElementById('pe-svg-next-date');
    if (nDate) nDate.textContent = 'Day ' + nextPeriodDay + ' · ' + PL.shortDate(nextPeriod);

    /* Mobile key list — populated after grid + bands so labels reflect inputs. */
    renderMobileKey(cycle, periodLen, fertileStartDay, fertileEndDay, ovulationDay, nextPeriodDay);

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

    /* Render. Hero shows the next-period window (start – end), matching the
       stat strip and the user's mental model of "when is my next period". */
    resultBig.textContent =
      PL.shortDate(nextPeriod) + ' – ' + PL.shortDate(nextPeriodEnd);
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
