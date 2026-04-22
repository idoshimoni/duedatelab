/* Ovulation Calculator
   Inputs:
     LMP (first day of last menstrual period), required
     Cycle length, 21 to 35 days (ACOG regular-cycle range), default 28

   Core formulas:
     Ovulation day   = LMP + (cycle − 14)
       Luteal phase is stable at ~14 days; cycle variability sits in the
       follicular phase (ACOG, NICE NG201). So a 28-day cycle ovulates on
       day 14, a 32-day cycle ovulates on day 18.

     Fertile window  = [ovulation − 5, ovulation + 1]  (6 days)
       Sperm survive up to 5 days, egg viability ~24 hours.
       Reference: Wilcox, Weinberg, Baird, NEJM 1995;333:1517.

     Peak fertility  = [ovulation − 2, ovulation]      (3 days)
       Highest daily conception probability per Wilcox 1995
       (roughly 25 to 33% per day of intercourse in this window).

     Next period     = LMP + cycle
     Next 3 fertile windows = shift ovulation by cycle × 1, 2, 3
*/
(function () {
  'use strict';
  var form = document.getElementById('ov-form');
  if (!form) return;
  var result = document.getElementById('ov-result');
  var resultBig = document.getElementById('ov-big');
  var resultExpl = document.getElementById('ov-expl');
  var resultStats = document.getElementById('ov-stats');
  var resultTrack = document.getElementById('ov-track');
  var resultNext = document.getElementById('ov-next');
  var errMsg = document.getElementById('ov-err');

  form.addEventListener('submit', function (e) {
    e.preventDefault();
    errMsg.textContent = '';

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
      errMsg.textContent = 'Couldn\u2019t read that date. Please re-enter.';
      return;
    }

    var ovulation   = PL.addDays(lmp, cycle - 14);
    var fertileStart = PL.addDays(ovulation, -5);
    var fertileEnd   = PL.addDays(ovulation, 1);
    var peakStart    = PL.addDays(ovulation, -2);
    var peakEnd      = ovulation;
    var nextPeriod   = PL.addDays(lmp, cycle);

    // Primary result
    resultBig.innerHTML = PL.formatDate(ovulation);
    resultExpl.innerHTML =
      'Fertile window: <b>' + PL.shortDate(fertileStart) +
      '</b> \u2013 <b>' + PL.shortDate(fertileEnd) + '</b>. ' +
      'Peak fertility: <b>' + PL.shortDate(peakStart) +
      '</b> \u2013 <b>' + PL.shortDate(peakEnd) + '</b>.';

    // Stats grid
    resultStats.innerHTML =
      stat(PL.shortDate(ovulation), 'Ovulation') +
      stat(PL.shortDate(peakStart) + ' \u2013 ' + PL.shortDate(peakEnd), 'Peak fertility') +
      stat(PL.shortDate(fertileStart) + ' \u2013 ' + PL.shortDate(fertileEnd), 'Fertile window') +
      stat(PL.shortDate(nextPeriod), 'Next period');

    // Cycle-day timeline: LMP (0) → ovulation (cycle − 14) → next period (cycle)
    var today = new Date(); today.setHours(0, 0, 0, 0);
    var daysFromLmp = PL.diffDays(today, lmp);
    var todayPct = Math.max(0, Math.min(100, (daysFromLmp / cycle) * 100));
    var ovPct = ((cycle - 14) / cycle) * 100;
    var fwStartPct = Math.max(0, ((cycle - 14 - 5) / cycle) * 100);
    var fwEndPct = Math.min(100, ((cycle - 14 + 1) / cycle) * 100);

    resultTrack.innerHTML =
      '<div class="pl-timeline-seg" style="left:' + fwStartPct + '%;width:' + (fwEndPct - fwStartPct) + '%;background:#FFE4EC;"></div>' +
      '<div class="pl-timeline-seg" style="left:0;width:' + todayPct + '%"></div>' +
      '<div class="pl-timeline-marker" style="left:' + ovPct + '%;background:#EC0D5C;" title="Ovulation"></div>' +
      (daysFromLmp >= 0 && daysFromLmp <= cycle
        ? '<div class="pl-timeline-marker" style="left:' + todayPct + '%;" title="Today"></div>'
        : '');

    // Next 3 predicted fertile windows (useful for TTC planning)
    var nextRows = '';
    for (var i = 1; i <= 3; i++) {
      var ov = PL.addDays(ovulation, cycle * i);
      var fs = PL.addDays(ov, -5);
      var fe = PL.addDays(ov, 1);
      nextRows +=
        '<tr>' +
        '<td>' + PL.shortDate(ov) + '</td>' +
        '<td>' + PL.shortDate(fs) + ' \u2013 ' + PL.shortDate(fe) + '</td>' +
        '</tr>';
    }
    if (resultNext) {
      resultNext.innerHTML =
        '<table class="pl-next-table"><caption>Next 3 predicted cycles</caption>' +
        '<thead><tr><th scope="col">Ovulation</th><th scope="col">Fertile window</th></tr></thead>' +
        '<tbody>' + nextRows + '</tbody></table>';
    }

    result.classList.remove('hidden');
    result.scrollIntoView({ behavior: 'smooth', block: 'start' });

    if (window.gtag) {
      window.gtag('event', 'ovulation_estimated', {
        cycle_length: cycle
      });
    }
  });

  function stat(num, label) {
    return '<div class="pl-stat"><div class="pl-stat-num">' + num + '</div><div class="pl-stat-label">' + label + '</div></div>';
  }

  var tryagain = document.getElementById('ov-tryagain');
  if (tryagain) tryagain.addEventListener('click', function (e) {
    e.preventDefault();
    result.classList.add('hidden');
    form.reset();
    window.PL.scrollToTop();
  });
})();
