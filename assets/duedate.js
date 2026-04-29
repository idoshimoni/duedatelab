/* Due date from LMP — Naegele's rule (280 days from LMP).
   Also accepts conception date (+266 days) or known due date.

   Step 3 v3 (2026-04-26-round3): renderer rewritten to populate the new
   pl-result panel + pl-result-visual SVG timeline + pl-next-steps block.
   Computation is unchanged. */
(function () {
  'use strict';
  var form = document.getElementById('dd-form');
  if (!form) return;
  var result = document.getElementById('dd-result');
  var visual = document.getElementById('dd-visual');
  var nextSteps = document.getElementById('dd-next-steps');
  var affiliate = document.getElementById('dd-affiliate');

  // due_date_result_shown one-shot guard, per round-3.5 research-AI
  // review 2026-04-28 (Q2b must-fix). Fires once per page load on the
  // first successful Due Date result render, aligning with
  // affiliate_card_view which also fires once per page load. The
  // ratio affiliate_card_view / due_date_result_shown then measures
  // "fraction of page loads where a valid result was shown that
  // scrolled far enough to see the affiliate card."
  var dueDateResultShownFired = false;
  function trackDueDateResultShown() {
    if (dueDateResultShownFired) return;
    dueDateResultShownFired = true;
    // Privacy-safe: tool name only. No due date, LMP, cycle length,
    // week-along value, result text, or other user-derived value.
    if (typeof window.gtag === 'function') {
      try {
        window.gtag('event', 'due_date_result_shown', {
          tool: 'due-date'
        });
      } catch (e) {}
    }
  }
  var resultBig = document.getElementById('dd-big');
  var resultDay = document.getElementById('dd-day');
  var resultSub = document.getElementById('dd-sub');
  var statAlong = document.getElementById('dd-stat-along');
  var statTri = document.getElementById('dd-stat-trimester');
  var statTerm = document.getElementById('dd-stat-term');
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

  function hideResultBlocks() {
    if (result) result.classList.add('hidden');
    if (visual) visual.classList.add('hidden');
    if (nextSteps) nextSteps.classList.add('hidden');
    if (affiliate) affiliate.classList.add('hidden');
  }

  function setX(ids, x, attr) {
    ids.forEach(function (id) {
      var el = document.getElementById(id);
      if (el) el.setAttribute(attr, x);
    });
  }

  /* SVG positions for the Due Date timeline.
     Axis: x = 20 .. 700 (680px wide), representing weeks 0..40 from LMP.
     Today marker visible only when 0 <= daysPreg <= 280. */
  function populateSvg(data) {
    var lmp = data.lmp, dueDate = data.dueDate;
    var daysPreg = data.daysPreg, weeks = data.weeks, days = data.days;

    var lmpDate = document.getElementById('dd-svg-lmp-date');
    if (lmpDate) lmpDate.textContent = PL.shortDate(lmp);

    var dueLabel = document.getElementById('dd-svg-due-date');
    if (dueLabel) dueLabel.textContent = PL.shortDate(dueDate) + ' · estimate';

    var todayG = document.getElementById('dd-svg-today');
    if (todayG) {
      if (daysPreg >= 0 && daysPreg <= 280) {
        var weeksSinceLmp = daysPreg / 7;
        var todayX = 20 + (weeksSinceLmp / 40) * 680;
        todayG.style.display = '';
        setX(['dd-svg-today-halo', 'dd-svg-today-ring', 'dd-svg-today-dot', 'dd-svg-today-pulse'], todayX, 'cx');
        setX(['dd-svg-today-label', 'dd-svg-today-weeks'], todayX, 'x');
        var stem = document.getElementById('dd-svg-today-stem');
        if (stem) { stem.setAttribute('x1', todayX); stem.setAttribute('x2', todayX); }
        var todayWeeks = document.getElementById('dd-svg-today-weeks');
        if (todayWeeks) todayWeeks.textContent = weeks + 'w ' + days + 'd';
        /* Q1 (Step 3.2): when Today is too close to LMP (< 64px), the
           "Today / 0w 0d" labels collide with the "LMP / <date>" labels.
           Suppress the Today text labels in that range — the pulsing halo
           over the LMP marker still communicates the "you are here"
           position visually. The stem and marker geometry stay visible. */
        var todayLabel = document.getElementById('dd-svg-today-label');
        var todayWeeksEl = document.getElementById('dd-svg-today-weeks');
        var hideTodayLabels = (todayX - 20) < 64;
        if (todayLabel) todayLabel.style.display = hideTodayLabels ? 'none' : '';
        if (todayWeeksEl) todayWeeksEl.style.display = hideTodayLabels ? 'none' : '';
      } else {
        todayG.style.display = 'none';
      }
    }

    var srDesc = document.querySelector('#dd-tl-desc');
    if (srDesc) {
      srDesc.textContent =
        'Horizontal timeline. From left to right: LMP marker (' + PL.formatDate(lmp) + '), ' +
        'estimated fertile window in weeks 2 to 3, trimester 1 (weeks 1-13), ' +
        'trimester 2 (weeks 14-27), trimester 3 (weeks 28-40), and estimated due date (' +
        PL.formatDate(dueDate) + ')' +
        (daysPreg >= 0 && daysPreg <= 280 ? '. Today marker positioned at ' + weeks + ' weeks ' + days + ' days.' : '.');
    }
  }

  function populateFallbackTable(data) {
    var lmp = data.lmp, dueDate = data.dueDate, cycle = data.cycle;
    var tbody = document.querySelector('#dd-fallback-table tbody');
    if (!tbody) return;
    var conceptionStart = PL.addDays(lmp, 14 + (cycle - 28) - 3);
    var conceptionEnd   = PL.addDays(lmp, 14 + (cycle - 28) + 3);
    var t1End   = PL.addDays(lmp, 13 * 7 - 1);
    var t2Start = PL.addDays(lmp, 13 * 7);
    var t2End   = PL.addDays(lmp, 27 * 7 - 1);
    var t3Start = PL.addDays(lmp, 27 * 7);
    tbody.innerHTML =
      '<tr><td>LMP</td><td>0</td><td>' + PL.shortDate(lmp) + '</td></tr>' +
      '<tr><td>Estimated fertile window</td><td>2–3</td><td>' + PL.shortDate(conceptionStart) + ' – ' + PL.shortDate(conceptionEnd) + '</td></tr>' +
      '<tr><td>Trimester 1</td><td>1–13</td><td>' + PL.shortDate(lmp) + ' – ' + PL.shortDate(t1End) + '</td></tr>' +
      '<tr><td>Trimester 2</td><td>14–27</td><td>' + PL.shortDate(t2Start) + ' – ' + PL.shortDate(t2End) + '</td></tr>' +
      '<tr><td>Trimester 3</td><td>28–40</td><td>' + PL.shortDate(t3Start) + ' – ' + PL.shortDate(dueDate) + '</td></tr>' +
      '<tr><td>Estimated due date</td><td>40</td><td>' + PL.shortDate(dueDate) + '</td></tr>';
    var caption = document.getElementById('dd-fallback-caption');
    if (caption) caption.textContent = 'Estimated pregnancy timeline (40 weeks from LMP, ' + PL.shortDate(lmp) + ', ' + cycle + '-day cycle)';
  }

  form.addEventListener('submit', function (e) {
    e.preventDefault();
    errMsg.textContent = '';
    // Reset all panels before validation so a previous result doesn't linger.
    hideResultBlocks();

    var mode = form.querySelector('input[name="mode"]:checked').value;
    var dueDate, conception, lmp;
    var today = new Date(); today.setHours(0, 0, 0, 0);
    var cycle = 28;

    if (mode === 'lmp') {
      var lmpVal = form.elements['lmp'].value;
      if (!lmpVal) { errMsg.textContent = 'Pick the first day of your last period.'; return; }
      lmp = new Date(lmpVal + 'T00:00:00');
      cycle = parseInt(cycleInput.value, 10) || 28;
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

    if (isNaN(dueDate)) { errMsg.textContent = 'That date doesn’t look right.'; return; }

    var daysPreg = PL.diffDays(today, lmp);
    var weeks = Math.floor(Math.max(0, daysPreg) / 7);
    var days = Math.max(0, daysPreg) - weeks * 7;
    var trimester = weeks < 13 ? 1 : (weeks < 27 ? 2 : 3);

    /* Render — populate new structure (R15: all values computed from current
       inputs, no frozen mock dates). */
    resultBig.textContent = PL.formatDate(dueDate);
    if (resultDay) resultDay.textContent = dueDate.toLocaleDateString('en-US', { weekday: 'long' });

    if (resultSub) {
      if (mode === 'lmp') {
        resultSub.textContent = 'Based on a ' + PL.formatDate(lmp) + ' LMP and a ' + cycle + '-day cycle.';
      } else if (mode === 'conception') {
        resultSub.textContent = 'Based on an estimated conception date of ' + PL.formatDate(conception) + ' (LMP estimated as ' + PL.shortDate(lmp) + ').';
      } else {
        resultSub.textContent = 'Based on a known due date of ' + PL.formatDate(dueDate) + ' (LMP estimated as ' + PL.shortDate(lmp) + ').';
      }
    }

    if (statAlong) {
      if (daysPreg < 0) {
        statAlong.textContent = 'Not yet';
      } else if (daysPreg > 294) {
        statAlong.textContent = 'Past 42w';
      } else {
        statAlong.textContent = weeks + 'w ' + days + 'd';
      }
    }

    /* Dynamic weeks-to-months deep-link per round 1.5 reply Q6:
       deep-link the journey card to /pregnancy/weeks-to-months/N/ when
       gestational age is in [1, 42]. Hub fallback for out-of-range.

       Per round 4 reviewer F3 must-fix: user-facing href stays exact,
       but the analytics fields must NOT include the user-derived week
       number. The GA4 result_next_step_click handler reads
       data-destination-path, so we set that to a generic placeholder
       and bucket the deep-link as 'leaf' (no week suffix). */
    var w2mLink = document.getElementById('dd-w2m-link');
    if (w2mLink) {
      var displayedWeek = Math.max(1, weeks);
      if (daysPreg < 0 || daysPreg > 294 || displayedWeek > 42) {
        w2mLink.setAttribute('href', '/pregnancy/weeks-to-months/');
        w2mLink.setAttribute('data-destination-path', '/pregnancy/weeks-to-months/');
        w2mLink.setAttribute('data-w2m-deep-link', 'hub');
      } else {
        var leafHref = '/pregnancy/weeks-to-months/' + displayedWeek + '/';
        w2mLink.setAttribute('href', leafHref);
        // Analytics: generic placeholder, never the user-derived week.
        w2mLink.setAttribute('data-destination-path', '/pregnancy/weeks-to-months/week/');
        w2mLink.setAttribute('data-w2m-deep-link', 'leaf');
      }
    }
    if (statTri) statTri.textContent = (daysPreg < 0) ? '—' : ('Trimester ' + trimester);

    if (statTerm) {
      var term37 = PL.addDays(lmp, 37 * 7);
      var term42 = PL.addDays(lmp, 42 * 7 - 1);
      statTerm.textContent = PL.shortDate(term37) + ' – ' + PL.shortDate(term42);
    }

    populateSvg({ lmp: lmp, dueDate: dueDate, daysPreg: daysPreg, weeks: weeks, days: days, cycle: cycle });
    populateFallbackTable({ lmp: lmp, conception: conception, dueDate: dueDate, cycle: cycle });

    result.classList.remove('hidden');
    if (visual) visual.classList.remove('hidden');
    if (nextSteps) nextSteps.classList.remove('hidden');
    if (affiliate) affiliate.classList.remove('hidden');

    trackDueDateResultShown();
    result.scrollIntoView({ behavior: 'smooth', block: 'start' });

    /* GA4 event: only fires if gtag was loaded and consent is granted.
       Only the static `tool` string is sent. User inputs (LMP date, conception
       date, due date, cycle length, chosen mode, computed trimester) never
       leave the browser, honoring the methodology privacy claim. */
    if (window.gtag) {
      window.gtag('event', 'calculator_submit', { tool: 'due-date' });
    }
  });

  var tryagain = document.getElementById('dd-tryagain');
  if (tryagain) tryagain.addEventListener('click', function (e) {
    e.preventDefault();
    hideResultBlocks();
    form.reset();
    setMode('lmp');
    window.PL.scrollToTop();
  });
})();
