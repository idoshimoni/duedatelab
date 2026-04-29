/* Weeks-to-Months Calculator (hub)
   Phase 2 Step 5 (Option B), per round 1.5 architecture lock.

   Inputs (mode = "weeks"):
     weeks  integer 1..42, required
     days   integer 0..6,  default 0

   Inputs (mode = "months"):
     fwm    decimal 0.25..10.5, required, step 0.25

   Convention (mirrors w2m_data_schema.py):
     FOUR_WEEK_MONTH_DAYS    = 28
     AVG_CALENDAR_MONTH_DAYS = 365.25 / 12 = 30.4375

   Privacy:
     No user-derived value (input or computed) is pushed to GA4.
     calculator_start fires from app.js on first input touch.
     calculator_submit and weeks_to_months_result_shown fire here
     with only { tool: "weeks-to-months" } as payload.
*/
(function () {
  'use strict';

  var FOUR_WEEK_MONTH_DAYS = 28;
  var AVG_CALENDAR_MONTH_DAYS = 30.4375;
  var MIN_WEEK = 1;
  var MAX_WEEK = 42;
  var MIN_FWM = 0.25;
  var MAX_FWM = 10.5;
  var TOOL = 'weeks-to-months';

  var form = document.getElementById('w2m-form');
  if (!form) return;

  var weeksField   = document.getElementById('w2m-weeks');
  var daysField    = document.getElementById('w2m-days');
  var fwmField     = document.getElementById('w2m-fwm');
  var fieldWeeksWrap  = document.getElementById('w2m-field-weeks');
  var fieldMonthsWrap = document.getElementById('w2m-field-months');
  var errEl    = document.getElementById('w2m-err');
  var result   = document.getElementById('w2m-result');
  var bigEl    = document.getElementById('w2m-big');
  var subEl    = document.getElementById('w2m-sub');
  var statCompletedEl = document.getElementById('w2m-stat-completed');
  var statCalendarEl  = document.getElementById('w2m-stat-calendar');
  var statDaysEl      = document.getElementById('w2m-stat-days');

  var resultShownFired = false;

  /* GA4 event helper. Privacy-safe: only static metadata, no user values. */
  function track(name) {
    if (window.gtag) {
      try { window.gtag('event', name, { tool: TOOL }); } catch (e) { /* silent */ }
    }
  }

  /* Number formatting helpers, mirror w2m_data_schema.py.
     7.0   -> "7"
     5.75  -> "5.75"
     0.5   -> "0.5"
     1.25  -> "1.25"
     7.107 -> "7.11"
  */
  function formatFourWeekMonths(fwm) {
    if (fwm === Math.floor(fwm)) return String(Math.floor(fwm));
    var s = fwm.toFixed(2);
    s = s.replace(/0+$/, '').replace(/\.$/, '');
    return s;
  }

  /* Singular when count is exactly 1.0, else plural. Matches the round-4
     fix-forward _four_week_unit() helper on the leaves. */
  function fourWeekUnit(count) {
    return count === 1 ? 'month' : 'months';
  }

  /* "1 four-week month"
     "7 four-week months"
     "5 four-week months + 3 weeks"
     "7 four-week months + 3 days"
     "0 four-week months + 2 weeks"
  */
  function formatCompletedRemainder(completed, remainingWeeks, remainingDays) {
    var monthWord = completed === 1 ? 'month' : 'months';
    var base = completed + ' four-week ' + monthWord;
    if (remainingWeeks === 0 && remainingDays === 0) return base;
    var parts = [base];
    if (remainingWeeks > 0) {
      parts.push(remainingWeeks + (remainingWeeks === 1 ? ' week' : ' weeks'));
    }
    if (remainingDays > 0) {
      parts.push(remainingDays + (remainingDays === 1 ? ' day' : ' days'));
    }
    return parts.join(' + ');
  }

  /* Hero from weeks input. Drops the "or N four-week months + 0 weeks"
     clause when input is exactly a whole-month week (4, 8, 12, ...) with
     0 days, matching the leaf hero pattern. */
  function formatHeroFromWeeks(input, calc) {
    var weekWord = input.weeks === 1 ? 'week' : 'weeks';
    var dayWord  = input.days === 1 ? 'day' : 'days';
    var inputStr = input.days > 0
      ? input.weeks + ' ' + weekWord + ' + ' + input.days + ' ' + dayWord
      : input.weeks + ' ' + weekWord;
    var fwmStr = formatFourWeekMonths(calc.fwm);
    var unit   = fourWeekUnit(calc.fwm);
    var calStr = calc.calendarMonths.toFixed(1);
    if (input.days === 0 && input.weeks % 4 === 0) {
      return inputStr + ' = ' + fwmStr + ' four-week pregnancy ' + unit +
        '. That is about ' + calStr + ' average calendar months and ' +
        calc.totalDays + ' days since LMP.';
    }
    var remainder = formatCompletedRemainder(calc.completed, calc.remainingWeeks, calc.remainingDays);
    return inputStr + ' = ' + fwmStr + ' four-week pregnancy ' + unit +
      ', or ' + remainder +
      '. That is about ' + calStr + ' average calendar months and ' +
      calc.totalDays + ' days since LMP.';
  }

  /* Hero from four-week-months input. */
  function formatHeroFromMonths(input, calc) {
    var fwmStr = formatFourWeekMonths(input.fwm);
    var unit   = fourWeekUnit(input.fwm);
    var calStr = calc.calendarMonths.toFixed(1);
    var weekWord = calc.weeks === 1 ? 'week' : 'weeks';
    var weeksDays;
    if (calc.remainderDays === 0) {
      weeksDays = calc.weeks + ' ' + weekWord;
    } else {
      var dayWord = calc.remainderDays === 1 ? 'day' : 'days';
      weeksDays = calc.weeks + ' ' + weekWord + ' + ' + calc.remainderDays + ' ' + dayWord;
    }
    return fwmStr + ' four-week pregnancy ' + unit + ' = ' + weeksDays +
      '. That is about ' + calStr + ' average calendar months and ' +
      calc.totalDays + ' days since LMP.';
  }

  /* --- Compute --- */
  function computeFromWeeks(weeks, days) {
    var totalDays = weeks * 7 + days;
    var fwm = totalDays / FOUR_WEEK_MONTH_DAYS;
    var completed = Math.floor(totalDays / FOUR_WEEK_MONTH_DAYS);
    var afterCompletedDays = totalDays - completed * FOUR_WEEK_MONTH_DAYS;
    var remainingWeeks = Math.floor(afterCompletedDays / 7);
    var remainingDays  = afterCompletedDays - remainingWeeks * 7;
    var calendarMonths = totalDays / AVG_CALENDAR_MONTH_DAYS;
    return {
      totalDays: totalDays,
      fwm: fwm,
      completed: completed,
      remainingWeeks: remainingWeeks,
      remainingDays: remainingDays,
      calendarMonths: calendarMonths
    };
  }

  function computeFromMonths(fwm) {
    /* fwm * 28 may have float drift for steps like 0.25 (28*0.25=7 exact)
       and 0.75 (28*0.75=21 exact). For odd inputs we round to the nearest
       day so the totalDays display stays clean. */
    var totalDays = Math.round(fwm * FOUR_WEEK_MONTH_DAYS);
    var weeks = Math.floor(totalDays / 7);
    var remainderDays = totalDays - weeks * 7;
    var calendarMonths = totalDays / AVG_CALENDAR_MONTH_DAYS;
    return {
      totalDays: totalDays,
      weeks: weeks,
      remainderDays: remainderDays,
      calendarMonths: calendarMonths
    };
  }

  /* --- Validation --- */
  function readWeeksInput() {
    var w = parseInt(weeksField.value, 10);
    var d = parseInt(daysField.value, 10);
    if (isNaN(d)) d = 0;
    if (isNaN(w)) return { error: 'Please enter the number of weeks pregnant (1 to 42).' };
    if (w < MIN_WEEK || w > MAX_WEEK) return { error: 'Weeks must be between 1 and 42.' };
    if (d < 0 || d > 6) return { error: 'Days must be between 0 and 6.' };
    return { weeks: w, days: d };
  }

  function readMonthsInput() {
    var m = parseFloat(fwmField.value);
    if (isNaN(m)) return { error: 'Please enter the number of four-week pregnancy months (0.25 to 10.5).' };
    if (m < MIN_FWM || m > MAX_FWM) return { error: 'Four-week pregnancy months must be between 0.25 and 10.5.' };
    return { fwm: m };
  }

  /* --- Render --- */
  function showError(msg) {
    if (errEl) errEl.textContent = msg;
  }
  function clearError() {
    if (errEl) errEl.textContent = '';
  }

  function renderFromWeeks(input, calc) {
    bigEl.textContent = formatHeroFromWeeks(input, calc);
    if (subEl) subEl.textContent = '';
    statCompletedEl.textContent = formatCompletedRemainder(calc.completed, calc.remainingWeeks, calc.remainingDays);
    statCalendarEl.textContent = '~' + calc.calendarMonths.toFixed(1) + ' calendar months';
    statDaysEl.textContent = calc.totalDays + ' days';
  }

  function renderFromMonths(input, calc) {
    bigEl.textContent = formatHeroFromMonths(input, calc);
    if (subEl) subEl.textContent = '';
    var weekWord = calc.weeks === 1 ? 'week' : 'weeks';
    var summary = calc.weeks + ' ' + weekWord;
    if (calc.remainderDays > 0) {
      summary += ' + ' + calc.remainderDays + (calc.remainderDays === 1 ? ' day' : ' days');
    }
    statCompletedEl.textContent = summary;
    statCalendarEl.textContent = '~' + calc.calendarMonths.toFixed(1) + ' calendar months';
    statDaysEl.textContent = calc.totalDays + ' days';
  }

  function showResult() {
    if (result) result.classList.remove('hidden');
    if (!resultShownFired) {
      track('weeks_to_months_result_shown');
      resultShownFired = true;
    }
  }

  /* --- Mode toggle --- */
  function setMode(mode) {
    if (mode === 'weeks') {
      fieldWeeksWrap.classList.remove('hidden');
      fieldMonthsWrap.classList.add('hidden');
    } else {
      fieldWeeksWrap.classList.add('hidden');
      fieldMonthsWrap.classList.remove('hidden');
    }
    clearError();
  }

  function currentMode() {
    var checked = form.querySelector('input[name="w2mmode"]:checked');
    return (checked && checked.value) || 'weeks';
  }

  /* --- Submit --- */
  function onSubmit(e) {
    e.preventDefault();
    var mode = currentMode();
    if (mode === 'weeks') {
      var inputW = readWeeksInput();
      if (inputW.error) { showError(inputW.error); return; }
      clearError();
      track('calculator_submit');
      var calcW = computeFromWeeks(inputW.weeks, inputW.days);
      renderFromWeeks(inputW, calcW);
      showResult();
    } else {
      var inputM = readMonthsInput();
      if (inputM.error) { showError(inputM.error); return; }
      clearError();
      track('calculator_submit');
      var calcM = computeFromMonths(inputM.fwm);
      renderFromMonths(inputM, calcM);
      showResult();
    }
  }

  /* --- Wire up --- */
  form.addEventListener('submit', onSubmit);
  Array.prototype.forEach.call(form.querySelectorAll('input[name="w2mmode"]'), function (r) {
    r.addEventListener('change', function () { setMode(r.value); });
  });
})();
