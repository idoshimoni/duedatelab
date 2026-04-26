/* Ovulation Calculator
   Inputs:
     LMP (first day of last menstrual period), required
     Cycle length, 21 to 35 days (ACOG regular-cycle range), default 28

   Core formulas:
     Ovulation day   = LMP + (cycle − 14)        (Lenton 1984, ACOG)
     Fertile window  = [ovulation − 5, ovulation] (Wilcox 1995)
     Peak fertility  = [ovulation − 2, ovulation] (Wilcox 1995, highest daily probability)

   Step 3.1 (2026-04-26-round1): SVG geometry now scales to the actual cycle
   length. stripMetrics(cycle) computes cellW = 672 / cycle from the strip
   anchor (left=24, width=672), so cell positions are correct for any cycle
   length 21..35. Day-tick labels and background cells regenerate dynamically.
*/
(function () {
  'use strict';
  var form = document.getElementById('ov-form');
  if (!form) return;
  var result = document.getElementById('ov-result');
  var visual = document.getElementById('ov-visual');
  var nextSteps = document.getElementById('ov-next-steps');
  var resultBig = document.getElementById('ov-big');
  var resultSub = document.getElementById('ov-sub');
  var statWindow = document.getElementById('ov-stat-window');
  var statPeak = document.getElementById('ov-stat-peak');
  var errMsg = document.getElementById('ov-err');

  /* Inclusive cycle-day numbering: Day 1 = LMP day, Day 2 = LMP + 1, etc. */
  function cycleDay(date, lmp) {
    return PL.diffDays(date, lmp) + 1;
  }

  function hideResultBlocks() {
    if (result) result.classList.add('hidden');
    if (visual) visual.classList.add('hidden');
    if (nextSteps) nextSteps.classList.add('hidden');
  }

  /* Strip metrics — see period.js. Same anchor (left=24, width=672). */
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

  function renderMobileKey(cycle, fertileStart, fertileEnd, ovulation) {
    var ul = document.getElementById('ov-cycle-mobile-key');
    if (!ul) return;
    ul.removeAttribute('hidden');
    ul.innerHTML =
      '<li><strong>Period:</strong> days 1–5</li>' +
      '<li><strong>Fertile window:</strong> days ' + fertileStart + '–' + fertileEnd + '</li>' +
      '<li><strong>Estimated ovulation:</strong> day ' + ovulation + '</li>';
  }

  function renderCycleGrid(cycle) {
    var g = document.getElementById('ov-svg-grid');
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
    var cycle = data.cycle;
    var ovulation = data.ovulation;
    var fertileStart = data.fertileStart, fertileEnd = data.fertileEnd;
    var fertileStartDay = data.fertileStartDay;
    var fertileEndDay = data.fertileEndDay;
    var ovulationDay = data.ovulationDay;

    renderCycleGrid(cycle);

    /* Period band: hard-coded 5 cells (no period-length input on this calc). */
    var pBand = document.getElementById('ov-svg-period-band');
    if (pBand) {
      var p = cellSpan(1, 5, cycle);
      pBand.setAttribute('x', p.x);
      pBand.setAttribute('width', p.w);
    }

    /* Fertile band + outline: inclusive cycle days derived from computed dates. */
    var f = cellSpan(fertileStartDay, fertileEndDay, cycle);
    var fBand = document.getElementById('ov-svg-fertile-band');
    if (fBand) { fBand.setAttribute('x', f.x); fBand.setAttribute('width', f.w); }
    var fOutline = document.getElementById('ov-svg-fertile-outline');
    if (fOutline) { fOutline.setAttribute('x', f.x); fOutline.setAttribute('width', f.w); }

    /* Ovulation marker: cell centre at the ovulation cycle day. */
    var ovG = document.getElementById('ov-svg-ovulation');
    if (ovG) {
      var ovCx = cellCenterX(ovulationDay, cycle);
      var circle = ovG.querySelector('circle');
      if (circle) circle.setAttribute('cx', ovCx);
      ovG.querySelectorAll('text').forEach(function (t) { t.setAttribute('x', ovCx); });
    }

    /* Reposition inline labels above the moving bands. */
    var periodMidX = cellCenterX(3, cycle);
    var fMid = Math.round((fertileStartDay + fertileEndDay) / 2);
    var fertileMidX = cellCenterX(fMid, cycle);
    var pTitle = document.getElementById('ov-svg-period-label');
    if (pTitle) pTitle.setAttribute('x', periodMidX);
    var fTitle = document.getElementById('ov-svg-fertile-label');
    if (fTitle) fTitle.setAttribute('x', fertileMidX);

    var fDates = document.getElementById('ov-svg-fertile-dates');
    if (fDates) {
      fDates.setAttribute('x', fertileMidX);
      fDates.textContent = PL.shortDate(fertileStart) + ' – ' + PL.shortDate(fertileEnd) + ' · estimate';
    }
    var ovDate = document.getElementById('ov-svg-ovulation-date');
    if (ovDate) ovDate.textContent = 'Day ' + ovulationDay + ' · ' + PL.shortDate(ovulation);

    renderMobileKey(cycle, fertileStartDay, fertileEndDay, ovulationDay);

    var srDesc = document.querySelector('#ov-cs-desc');
    if (srDesc) {
      srDesc.textContent = 'Cycle strip starting ' + PL.formatDate(data.lmp) + '. Period covers days 1 to 5. Estimated fertile window covers days ' +
        fertileStartDay + ' to ' + fertileEndDay + ' (' + PL.formatDate(fertileStart) + ' – ' + PL.formatDate(fertileEnd) + '). Estimated ovulation on day ' +
        ovulationDay + ' (' + PL.formatDate(ovulation) + ').';
    }
  }

  function populateFallbackTable(data) {
    var cycle = data.cycle, lmp = data.lmp, ovulation = data.ovulation;
    var fertileStart = data.fertileStart, fertileEnd = data.fertileEnd;
    var fertileStartDay = data.fertileStartDay;
    var fertileEndDay = data.fertileEndDay;
    var ovulationDay = data.ovulationDay;
    var tbody = document.querySelector('#ov-fallback-table tbody');
    if (tbody) {
      tbody.innerHTML =
        '<tr><td>Period</td><td>1–5</td><td>' + PL.shortDate(lmp) + ' – ' + PL.shortDate(PL.addDays(lmp, 4)) + '</td></tr>' +
        '<tr><td>Estimated fertile window</td><td>' + fertileStartDay + '–' + fertileEndDay + '</td><td>' + PL.shortDate(fertileStart) + ' – ' + PL.shortDate(fertileEnd) + '</td></tr>' +
        '<tr><td>Estimated ovulation</td><td>' + ovulationDay + '</td><td>' + PL.shortDate(ovulation) + '</td></tr>';
    }
    var caption = document.getElementById('ov-fallback-caption');
    if (caption) caption.textContent = 'Fertile window for a ' + cycle + '-day cycle starting ' + PL.shortDate(lmp);
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
    if (!(cycle >= 21 && cycle <= 35)) {
      errMsg.textContent = 'Cycle length must be between 21 and 35 days.';
      return;
    }
    var lmp = new Date(lmpVal + 'T00:00:00');
    if (isNaN(lmp)) {
      errMsg.textContent = 'Couldn’t read that date. Please re-enter.';
      return;
    }

    var ovulation    = PL.addDays(lmp, cycle - 14);
    var fertileStart = PL.addDays(ovulation, -5);
    var fertileEnd   = ovulation;

    /* Inclusive cycle-day numbering for user-facing labels. */
    var fertileStartDay = cycleDay(fertileStart, lmp);
    var fertileEndDay   = cycleDay(fertileEnd, lmp);
    var ovulationDay    = cycleDay(ovulation, lmp);

    resultBig.textContent = 'Days ' + fertileStartDay + '–' + fertileEndDay + ' of your cycle';
    if (resultSub) {
      resultSub.textContent = 'Based on a ' + PL.formatDate(lmp) + ' LMP and a ' + cycle + '-day cycle. For a ' + cycle + '-day cycle, this estimate places ovulation around the middle of the cycle. Ovulation can shift by several days.';
    }
    if (statWindow) statWindow.textContent = PL.shortDate(fertileStart) + ' – ' + PL.shortDate(fertileEnd);
    if (statPeak) statPeak.textContent = PL.shortDate(ovulation);

    populateSvg({
      cycle: cycle, lmp: lmp, ovulation: ovulation,
      fertileStart: fertileStart, fertileEnd: fertileEnd,
      fertileStartDay: fertileStartDay, fertileEndDay: fertileEndDay,
      ovulationDay: ovulationDay
    });
    populateFallbackTable({
      cycle: cycle, lmp: lmp, ovulation: ovulation,
      fertileStart: fertileStart, fertileEnd: fertileEnd,
      fertileStartDay: fertileStartDay, fertileEndDay: fertileEndDay,
      ovulationDay: ovulationDay
    });

    /* Dynamic figcaption update — reflects the user's actual cycle length. */
    var cap = document.getElementById('ov-cs-title');
    if (cap) cap.textContent = 'Fertile window and estimated ovulation (' + cycle + '-day cycle)';

    result.classList.remove('hidden');
    if (visual) visual.classList.remove('hidden');
    if (nextSteps) nextSteps.classList.remove('hidden');
    result.scrollIntoView({ behavior: 'smooth', block: 'start' });

    /* Only the static `tool` string is sent. User inputs (LMP, cycle length)
       never leave the browser, honoring the methodology privacy claim. */
    if (window.gtag) {
      window.gtag('event', 'calculator_submit', { tool: 'ovulation' });
    }
  });

  var tryagain = document.getElementById('ov-tryagain');
  if (tryagain) tryagain.addEventListener('click', function (e) {
    e.preventDefault();
    hideResultBlocks();
    form.reset();
    window.PL.scrollToTop();
  });
})();
