/* Conception Calculator — 4 modes.
   LMP: conception ≈ LMP + 14d (adjusted for cycle length).
   Ultrasound: conception ≈ scan date − (gestational age − 2 weeks).
   IVF: conception = transfer date − embryo age. Due date = transfer + 266 - embryo age.
   Reverse (from birthday): conception ≈ birth − 266.

   Step 3.1 (2026-04-26-round1): SVG geometry now scales to the actual cycle
   length. stripMetrics(cycle) computes cellW = 672 / cycle from the strip
   anchor (left=24, width=672), so cell positions are correct for any cycle
   length. Day-tick labels and background cells regenerate dynamically.
*/
(function () {
  'use strict';
  var form = document.getElementById('con-form');
  if (!form) return;
  var result = document.getElementById('con-result');
  var visual = document.getElementById('con-visual');
  var nextSteps = document.getElementById('con-next-steps');
  var resultBig = document.getElementById('con-big');
  var resultSub = document.getElementById('con-sub');
  var statPeak = document.getElementById('con-stat-peak');
  var statDue = document.getElementById('con-stat-due');
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

  function renderMobileKey(cycle, windowStart, windowEnd, peak) {
    var ul = document.getElementById('con-cycle-mobile-key');
    if (!ul) return;
    ul.removeAttribute('hidden');
    ul.innerHTML =
      '<li><strong>Period:</strong> days 1–5</li>' +
      '<li><strong>Conception window:</strong> days ' + windowStart + '–' + windowEnd + '</li>' +
      '<li><strong>Most likely day:</strong> day ' + peak + '</li>';
  }

  function renderCycleGrid(cycle) {
    var g = document.getElementById('con-svg-grid');
    if (!g) return;
    while (g.firstChild) g.removeChild(g.firstChild);
    var m = stripMetrics(cycle);
    var rectW = Math.max(1, m.cellW - 2);
    var showEveryDay = cycle <= 32;
    for (var d = 1; d <= cycle; d++) {
      var x = m.left + (d - 1) * m.cellW;
      var stroke = (d <= 5 || (d >= 10 && d <= 17)) ? '#FFFFFF' : '#E6EAF1';
      var sw = (d <= 5 || (d >= 10 && d <= 17)) ? '2' : '1';
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

  function formatDateRange(start, end) {
    /* If same month + year, "11–17 January 2026"; otherwise full both ends. */
    if (start.getFullYear() === end.getFullYear() && start.getMonth() === end.getMonth()) {
      var monthYear = start.toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
      return start.getDate() + '–' + end.getDate() + ' ' + monthYear;
    }
    return PL.formatDate(start) + ' – ' + PL.formatDate(end);
  }

  function populateSvg(data) {
    var cycle = data.cycle;
    var conception = data.conception;
    var fertileStart = data.fertileStart, fertileEnd = data.fertileEnd;
    var windowStartDay = data.windowStartDay;
    var windowEndDay = data.windowEndDay;
    var peakDay = data.peakDay;

    renderCycleGrid(cycle);

    /* Period band: 5 cells (we don't capture period length on this calc). */
    var pBand = document.getElementById('con-svg-period-band');
    if (pBand) {
      var p = cellSpan(1, 5, cycle);
      pBand.setAttribute('x', p.x);
      pBand.setAttribute('width', p.w);
    }

    /* Conception window: inclusive cycle days derived from computed dates. */
    var f = cellSpan(windowStartDay, windowEndDay, cycle);
    var fBand = document.getElementById('con-svg-conception-band');
    if (fBand) { fBand.setAttribute('x', f.x); fBand.setAttribute('width', f.w); }
    var fOutline = document.getElementById('con-svg-conception-outline');
    if (fOutline) { fOutline.setAttribute('x', f.x); fOutline.setAttribute('width', f.w); }

    /* Most-likely-day (open ring): cell centre at the peak cycle day. */
    var pkG = document.getElementById('con-svg-peak');
    if (pkG) {
      var pkCx = cellCenterX(peakDay, cycle);
      var circle = pkG.querySelector('circle');
      if (circle) circle.setAttribute('cx', pkCx);
      pkG.querySelectorAll('text').forEach(function (t) { t.setAttribute('x', pkCx); });
    }

    /* Reposition inline labels above the moving bands. */
    var periodMidX = cellCenterX(3, cycle);
    var fMid = Math.round((windowStartDay + windowEndDay) / 2);
    var fertileMidX = cellCenterX(fMid, cycle);
    var pTitle = document.getElementById('con-svg-period-label');
    if (pTitle) pTitle.setAttribute('x', periodMidX);
    var fTitle = document.getElementById('con-svg-conception-label');
    if (fTitle) fTitle.setAttribute('x', fertileMidX);

    var dates = document.getElementById('con-svg-conception-dates');
    if (dates) {
      dates.setAttribute('x', fertileMidX);
      dates.textContent = PL.shortDate(fertileStart) + ' – ' + PL.shortDate(fertileEnd) + ' · estimate';
    }
    var pkDate = document.getElementById('con-svg-peak-date');
    if (pkDate) pkDate.textContent = 'Day ' + peakDay + ' · ' + PL.shortDate(conception);

    renderMobileKey(cycle, windowStartDay, windowEndDay, peakDay);

    var srDesc = document.querySelector('#con-cs-desc');
    if (srDesc) {
      srDesc.textContent = 'Cycle strip showing the period that started this cycle (days 1 to 5), the estimated conception window (' +
        PL.formatDate(fertileStart) + ' to ' + PL.formatDate(fertileEnd) + ', cycle days ' + windowStartDay + '–' + windowEndDay +
        '), and the most-likely conception day on ' + PL.formatDate(conception) + ' (cycle day ' + peakDay + ').';
    }
  }

  function populateFallbackTable(data) {
    var cycle = data.cycle, lmp = data.lmp, conception = data.conception, dueDate = data.dueDate;
    var fertileStart = data.fertileStart, fertileEnd = data.fertileEnd;
    var windowStartDay = data.windowStartDay;
    var windowEndDay = data.windowEndDay;
    var peakDay = data.peakDay;
    var tbody = document.querySelector('#con-fallback-table tbody');
    if (tbody) {
      tbody.innerHTML =
        '<tr><td>Period</td><td>1–5</td><td>' + PL.shortDate(lmp) + ' – ' + PL.shortDate(PL.addDays(lmp, 4)) + '</td></tr>' +
        '<tr><td>Estimated conception window</td><td>' + windowStartDay + '–' + windowEndDay + '</td><td>' + PL.shortDate(fertileStart) + ' – ' + PL.shortDate(fertileEnd) + '</td></tr>' +
        '<tr><td>Most likely conception day</td><td>' + peakDay + '</td><td>' + PL.shortDate(conception) + '</td></tr>' +
        '<tr><td>Related due date (estimate)</td><td>—</td><td>' + PL.shortDate(dueDate) + '</td></tr>';
    }
    var caption = document.getElementById('con-fallback-caption');
    if (caption) caption.textContent = 'Estimated conception window for a ' + cycle + '-day cycle starting ' + PL.shortDate(lmp);
  }

  form.addEventListener('submit', function (e) {
    e.preventDefault();
    errMsg.textContent = '';
    hideResultBlocks();

    var mode = form.querySelector('input[name="conmode"]:checked').value;
    var conception, dueDate, lmp;
    var cycle = 28;

    if (mode === 'lmp') {
      var lmpVal = form.elements['lmp'].value;
      if (!lmpVal) { errMsg.textContent = 'Pick the first day of your last period.'; return; }
      lmp = new Date(lmpVal + 'T00:00:00');
      cycle = parseInt(form.elements['cycle'].value, 10) || 28;
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
      if (!bVal) { errMsg.textContent = 'Pick your child’s birth date.'; return; }
      var birth = new Date(bVal + 'T00:00:00');
      conception = PL.addDays(birth, -266);
      lmp = PL.addDays(conception, -14);
      dueDate = birth;
    }

    if (!conception || isNaN(conception)) { errMsg.textContent = 'Couldn’t calculate. Please check your inputs.'; return; }

    var fertileStart = PL.addDays(conception, -5);
    var fertileEnd = PL.addDays(conception, 1);

    /* Inclusive cycle-day numbering for user-facing labels. */
    var windowStartDay = cycleDay(fertileStart, lmp);
    var windowEndDay   = cycleDay(fertileEnd, lmp);
    var peakDay        = cycleDay(conception, lmp);

    /* Big result: a calendar range. */
    resultBig.textContent = formatDateRange(fertileStart, fertileEnd);

    if (resultSub) {
      var subBase;
      if (mode === 'lmp') {
        subBase = 'Based on a ' + PL.formatDate(lmp) + ' LMP and a ' + cycle + '-day cycle. ';
      } else if (mode === 'us') {
        subBase = 'Based on the ultrasound dating you entered (LMP estimated as ' + PL.shortDate(lmp) + '). ';
      } else if (mode === 'ivf') {
        subBase = 'Based on the IVF transfer date and embryo age you entered. ';
      } else {
        subBase = 'Working backward from the birth date you entered (LMP estimated as ' + PL.shortDate(lmp) + '). ';
      }
      resultSub.textContent = subBase + 'Conception timing is estimated from the fertile window and the uncertainty around ovulation day. This range is a planning estimate, not proof of the conception date.';
    }
    if (statPeak) statPeak.textContent = PL.formatDate(conception);
    if (statDue) statDue.textContent = PL.formatDate(dueDate) + ' (estimate)';

    populateSvg({
      cycle: cycle, conception: conception,
      fertileStart: fertileStart, fertileEnd: fertileEnd,
      windowStartDay: windowStartDay, windowEndDay: windowEndDay, peakDay: peakDay
    });
    populateFallbackTable({
      cycle: cycle, lmp: lmp, conception: conception, dueDate: dueDate,
      fertileStart: fertileStart, fertileEnd: fertileEnd,
      windowStartDay: windowStartDay, windowEndDay: windowEndDay, peakDay: peakDay
    });

    /* Dynamic figcaption update — reflects the user's actual cycle length. */
    var cap = document.getElementById('con-cs-title');
    if (cap) cap.textContent = 'Estimated conception window (' + cycle + '-day cycle)';

    result.classList.remove('hidden');
    if (visual) visual.classList.remove('hidden');
    if (nextSteps) nextSteps.classList.remove('hidden');
    result.scrollIntoView({ behavior: 'smooth', block: 'start' });

    /* Only the static `tool` string is sent. User inputs and the chosen mode
       never leave the browser, honoring the methodology privacy claim. */
    if (window.gtag) {
      window.gtag('event', 'calculator_submit', { tool: 'conception' });
    }
  });

  var tryagain = document.getElementById('con-tryagain');
  if (tryagain) tryagain.addEventListener('click', function (e) {
    e.preventDefault();
    hideResultBlocks();
    form.reset();
    setMode('lmp');
    window.PL.scrollToTop();
  });
})();
