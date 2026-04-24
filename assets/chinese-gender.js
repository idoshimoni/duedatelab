/* Chinese Gender Chart — lunar age × lunar conception month lookup.
   Note: novelty tool. ~50% accurate by design. */
(function () {
  'use strict';
  // Chart values: rows = lunar age (18..45), cols = lunar month (1..12)
  // 'B' = Boy, 'G' = Girl. Traditional published chart.
  var CHART = {
    18:'GBGBBBBBBBBG',19:'BGBGBBGGGGBG',20:'GBGBBBBBBGGB',21:'BGGGGGGGGGGG',22:'GBBGBGBBGBBB',
    23:'BBGBBBGBGGBG',24:'BBGGBBGBGBGG',25:'GBBBGGBGBGGG',26:'BGBGBGBGBGBB',27:'GBBGBGBBGBGG',
    28:'BGBBGBBGGBGG',29:'GBBGBBGBGGGB',30:'BGBGBGBGBGBB',31:'BGBGGBGBGBGB',32:'BGBGGBGBGBGB',
    33:'GBGBBGBGBGGB',34:'BGBGBBGBGGGG',35:'BGBGBGBBBGBG',36:'GBGBGBGBGBGB',37:'BGBGBGBGBGBG',
    38:'GBGBGBGBGBGG',39:'BGBGBGBGBGBG',40:'GBGBGBGBGBGB',41:'BGBGBGBGBGBG',42:'GBGBGBGBGBGB',
    43:'BGBGBGBGBGBG',44:'GGBGBGBGBGBG',45:'BGBGBGBGBGBG'
  };

  // Approx Chinese-zodiac new-year cutoffs (month-day) for 1900-2100.
  // If month-day is before cutoff, lunar age = age+2; else age+1. Good enough for a novelty tool.
  function lunarAgeAt(birthDate, conceptionDate) {
    var by = birthDate.getFullYear();
    var ay = conceptionDate.getFullYear();
    // Simple approximation: lunar age = western age + 1 (+1 more if conception is before ~Feb 4 of that year and birthday hasn't passed)
    var age = ay - by;
    if (conceptionDate.getMonth() < birthDate.getMonth() ||
       (conceptionDate.getMonth() === birthDate.getMonth() && conceptionDate.getDate() < birthDate.getDate())) {
      age -= 1;
    }
    age += 1; // +1 for lunar (counted from conception)
    // If conception falls before lunar new year (approx Feb 4), add another year
    var cutoffMonth = 1, cutoffDay = 20; // approx, ranges Jan 21 – Feb 20
    if (conceptionDate.getMonth() < cutoffMonth || (conceptionDate.getMonth() === cutoffMonth && conceptionDate.getDate() < cutoffDay)) {
      age += 1;
    }
    return age;
  }

  function lunarMonthApprox(d) {
    // Rough: subtract ~20 days to shift Gregorian → lunar start of month.
    var shifted = new Date(d.getTime() - 20 * 86400000);
    return shifted.getMonth() + 1; // 1..12
  }

  var form = document.getElementById('cgc-form');
  if (!form) return;
  var result = document.getElementById('cgc-result');
  var resultBig = document.getElementById('cgc-big');
  var resultExpl = document.getElementById('cgc-expl');
  var chartWrap = document.getElementById('cgc-chart');
  var errMsg = document.getElementById('cgc-err');
  var modeBtns = document.querySelectorAll('[data-cgc-mode]');
  var panels = document.querySelectorAll('[data-cgc-panel]');
  var currentMode = 'date';

  function setMode(m) {
    currentMode = m;
    modeBtns.forEach(function(b){ b.classList.toggle('active', b.dataset.cgcMode === m); });
    panels.forEach(function(p){ p.classList.toggle('hidden', p.dataset.cgcPanel !== m); });
    errMsg.textContent = '';
  }
  modeBtns.forEach(function(b){ b.addEventListener('click', function(){ setMode(b.dataset.cgcMode); }); });

  function getConceptionDate() {
    if (currentMode === 'date') {
      var cday = form.elements['conception'].value;
      if (!cday) return { err: 'Enter the conception date, or switch to “Estimate from my last period”.' };
      return { date: new Date(cday + 'T00:00:00') };
    }
    var lmp = form.elements['lmp'].value;
    if (!lmp) return { err: 'Enter the first day of your last period.' };
    var cycle = parseInt(form.elements['cycle'].value, 10);
    if (!(cycle >= 21 && cycle <= 45)) return { err: 'Cycle length should be between 21 and 45 days.' };
    var lmpDate = new Date(lmp + 'T00:00:00');
    // Ovulation ≈ cycle_length - 14 days after LMP start
    var conc = new Date(lmpDate.getTime() + (cycle - 14) * 86400000);
    return { date: conc };
  }

  form.addEventListener('submit', function (e) {
    e.preventDefault();
    errMsg.textContent = '';
    var bday = form.elements['birth'].value;
    if (!bday) { errMsg.textContent = 'Enter the mother’s date of birth.'; return; }
    var cRes = getConceptionDate();
    if (cRes.err) { errMsg.textContent = cRes.err; return; }
    var birth = new Date(bday + 'T00:00:00');
    var conc = cRes.date;
    if (conc < birth) { errMsg.textContent = 'Conception date can’t be before the mother’s birth date. Please check your inputs.'; return; }
    var age = lunarAgeAt(birth, conc);
    var month = lunarMonthApprox(conc);
    if (age < 18 || age > 45) {
      errMsg.textContent = 'This chart only covers mothers aged 18–45 at conception. Your estimated age here is ' + age + '.'; return;
    }
    var prediction = CHART[age].charAt(month - 1);
    var isBoy = prediction === 'B';

    resultBig.innerHTML = isBoy ? 'It\u2019s a <span style="color:#1A2E4A">boy</span>' : 'It\u2019s a <span style="color:#EC0D5C">girl</span>';
    resultExpl.innerHTML = 'Lunar age <b>' + age + '</b> · Conception lunar month <b>' + month + '</b>. This is a novelty prediction, about 50% accurate.';
    chartWrap.innerHTML = renderChart(age, month);
    result.classList.remove('hidden');
    result.scrollIntoView({ behavior: 'smooth', block: 'start' });

    // Only the static `tool` string is sent. User birth date, conception
    // month, and derived prediction never leave the browser.
    if (window.gtag) {
      window.gtag('event', 'calculator_submit', { tool: 'chinese_gender' });
    }
  });

  function renderChart(hlAge, hlMonth) {
    var out = '<table class="pl-chart"><thead><tr><th>Age</th>';
    for (var m = 1; m <= 12; m++) out += '<th>' + m + '</th>';
    out += '</tr></thead><tbody>';
    Object.keys(CHART).forEach(function (ageStr) {
      var age = +ageStr;
      var hl = age === hlAge;
      out += '<tr class="' + (hl ? 'hl' : '') + '"><td>' + age + '</td>';
      for (var m = 1; m <= 12; m++) {
        var v = CHART[age].charAt(m - 1);
        var isPredict = hl && m === hlMonth;
        out += '<td class="' + (isPredict ? 'predict' : '') + '">' + v + '</td>';
      }
      out += '</tr>';
    });
    return out + '</tbody></table>';
  }

  var tryagain = document.getElementById('cgc-tryagain');
  if (tryagain) tryagain.addEventListener('click', function (e) { e.preventDefault(); result.classList.add('hidden'); form.reset(); form.elements['cycle'].value = 28; setMode('date'); window.PL.scrollToTop(); });
})();
