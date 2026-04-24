/* Period Calculator
   Inputs:
     LMP (first day of last menstrual period), required
     Cycle length, 21 to 45 days (ACOG's normal adult range), default 28
     Period length, 2 to 8 days, default 5 (informational, not used in math)

   Core formulas:
     Next period     = LMP + cycle
     Ovulation day   = LMP + (cycle - 14)
       Luteal phase is stable at ~14 days; cycle variability sits in the
       follicular phase (Lenton BJOG 1984, ACOG).

     Fertile window  = [ovulation - 5, ovulation]  (6 days ending on ovulation,
       Wilcox NEJM 1995)

     Next 3 cycles   = shift LMP forward by cycle x 1, 2, 3

   This tool is calendar-based prediction for natural cycles. It is not
   reliable on hormonal contraception and does not adjust for PCOS,
   thyroid disease, breastfeeding, perimenopause, or recent contraceptive
   changes.
*/
(function () {
  'use strict';
  var form = document.getElementById('pe-form');
  if (!form) return;
  var result = document.getElementById('pe-result');
  var resultBig = document.getElementById('pe-big');
  var resultExpl = document.getElementById('pe-expl');
  var resultStats = document.getElementById('pe-stats');
  var resultTrack = document.getElementById('pe-track');
  var resultNext = document.getElementById('pe-next');
  var errMsg = document.getElementById('pe-err');

  form.addEventListener('submit', function (e) {
    e.preventDefault();
    errMsg.textContent = '';

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
      errMsg.textContent = 'Couldn\u2019t read that date. Please re-enter.';
      return;
    }
    // Reject future LMP dates (almost always a typo).
    var today0 = new Date(); today0.setHours(0, 0, 0, 0);
    if (lmp > today0) {
      errMsg.textContent = 'That date is in the future. Please enter the first day of your last period.';
      return;
    }

    var nextPeriod   = PL.addDays(lmp, cycle);
    var periodEnd    = PL.addDays(nextPeriod, periodLen - 1);
    var ovulation    = PL.addDays(lmp, cycle - 14);
    var fertileStart = PL.addDays(ovulation, -5);
    var fertileEnd   = ovulation;  // Wilcox 1995: 6-day window ending on ovulation day

    // Days until next period (can be negative if it's already past)
    var today = new Date(); today.setHours(0, 0, 0, 0);
    var daysUntil = PL.diffDays(nextPeriod, today);

    // Primary result
    resultBig.innerHTML = PL.formatDate(nextPeriod);
    if (daysUntil > 0) {
      resultExpl.innerHTML =
        '<b>' + daysUntil + '</b> day' + (daysUntil === 1 ? '' : 's') + ' from now. ' +
        'Expected to end around <b>' + PL.shortDate(periodEnd) + '</b>.';
    } else if (daysUntil === 0) {
      resultExpl.innerHTML = 'Predicted for today. Expected to end around <b>' + PL.shortDate(periodEnd) + '</b>.';
    } else if (Math.abs(daysUntil) > cycle + 14) {
      // LMP is more than ~1.5 cycles in the past — likely a year typo.
      resultExpl.innerHTML = '<b>' + Math.abs(daysUntil) + '</b> days ago. That is far in the past, so this result is historical rather than a useful forecast. Double-check the year on the LMP input and re-run if needed.';
    } else {
      resultExpl.innerHTML = 'Predicted <b>' + Math.abs(daysUntil) + '</b> day' + (Math.abs(daysUntil) === 1 ? '' : 's') + ' ago. If it has not arrived, consider a home pregnancy test or a clinician visit.';
    }

    // Stats grid
    resultStats.innerHTML =
      stat(PL.shortDate(nextPeriod), 'Next period') +
      stat(PL.shortDate(ovulation), 'Ovulation') +
      stat(PL.shortDate(fertileStart) + ' \u2013 ' + PL.shortDate(fertileEnd), 'Fertile window') +
      stat(cycle + 'd', 'Cycle length');

    // Cycle-day timeline: LMP (0) -> ovulation (cycle - 14) -> next period (cycle)
    var daysFromLmp = PL.diffDays(today, lmp);
    var todayPct = Math.max(0, Math.min(100, (daysFromLmp / cycle) * 100));
    var ovPct = ((cycle - 14) / cycle) * 100;

    resultTrack.innerHTML =
      '<div class="pl-timeline-seg" style="left:0;width:' + todayPct + '%"></div>' +
      '<div class="pl-timeline-marker" style="left:' + ovPct + '%;background:#EC0D5C;" title="Ovulation"></div>' +
      (daysFromLmp >= 0 && daysFromLmp <= cycle
        ? '<div class="pl-timeline-marker" style="left:' + todayPct + '%;" title="Today"></div>'
        : '');

    // Next 3 predicted cycles (useful for planning)
    var nextRows = '';
    for (var i = 1; i <= 3; i++) {
      var np = PL.addDays(lmp, cycle * (i + 1));
      var pe = PL.addDays(np, periodLen - 1);
      var ov = PL.addDays(np, -14);
      nextRows +=
        '<tr>' +
        '<td>' + PL.shortDate(np) + ' \u2013 ' + PL.shortDate(pe) + '</td>' +
        '<td>' + PL.shortDate(ov) + '</td>' +
        '</tr>';
    }
    if (resultNext) {
      resultNext.innerHTML =
        '<table class="pl-next-table"><caption>Next 3 predicted cycles</caption>' +
        '<thead><tr><th scope="col">Period</th><th scope="col">Ovulation</th></tr></thead>' +
        '<tbody>' + nextRows + '</tbody></table>';
    }

    result.classList.remove('hidden');
    result.scrollIntoView({ behavior: 'smooth', block: 'start' });

    // GA4 event: only fires if gtag was loaded and consent is granted.
    // `calculator_submit` is the unified cross-tool key event. Only the static
    // `tool` string is sent. User inputs (LMP, cycle length, period length)
    // are not included in any analytics event, honoring the methodology page's
    // "inputs never leave the browser" privacy claim.
    if (window.gtag) {
      window.gtag('event', 'calculator_submit', { tool: 'period' });
    }
  });

  function stat(num, label) {
    return '<div class="pl-stat"><div class="pl-stat-num">' + num + '</div><div class="pl-stat-label">' + label + '</div></div>';
  }

  var tryagain = document.getElementById('pe-tryagain');
  if (tryagain) tryagain.addEventListener('click', function (e) {
    e.preventDefault();
    result.classList.add('hidden');
    form.reset();
    window.PL.scrollToTop();
  });
})();
