/* Baby Percentile — WHO weight-for-age + length/height-for-age, 0-60 months.
   LMS values from WHO Child Growth Standards (boys + girls).
   Source: who.int/tools/child-growth-standards/standards. Values verified against published tables. */
(function () {
  'use strict';

  // WHO weight-for-age LMS, months 0..60. [L, M, S]
  var W_BOY = [
    [0.3487,3.3464,0.14602],[0.2297,4.4709,0.13395],[0.197,5.5675,0.12385],[0.1738,6.3762,0.11727],[0.1553,7.0023,0.11316],
    [0.1395,7.5105,0.1108],[0.1257,7.934,0.10958],[0.1134,8.297,0.10902],[0.1021,8.6151,0.10882],[0.0917,8.9014,0.10881],
    [0.082,9.1649,0.10891],[0.073,9.4122,0.10906],[0.0644,9.6479,0.10925],[0.0563,9.8749,0.10949],[0.0487,10.0953,0.10976],
    [0.0413,10.3108,0.11007],[0.0343,10.5228,0.11041],[0.0275,10.7319,0.11079],[0.0211,10.9385,0.1112],[0.0148,11.143,0.11164],
    [0.0087,11.3462,0.11211],[0.0029,11.5486,0.11261],[-0.0028,11.7504,0.11314],[-0.0083,11.9514,0.1137],[-0.0137,12.1515,0.11428],
    [-0.019,12.3502,0.11488],[-0.0241,12.5478,0.11551],[-0.0291,12.744,0.11615],[-0.0339,12.9389,0.11681],[-0.0386,13.1325,0.11748],
    [-0.0432,13.3249,0.11816],[-0.0477,13.5161,0.11885],[-0.0521,13.7061,0.11955],[-0.0565,13.895,0.12026],[-0.0608,14.0827,0.12097],
    [-0.0651,14.2692,0.12168],[-0.0693,14.4547,0.1224],[-0.0734,14.639,0.12311],[-0.0775,14.8221,0.12383],[-0.0816,15.0042,0.12455],
    [-0.0856,15.1852,0.12526],[-0.0896,15.3652,0.12598],[-0.0936,15.5442,0.12669],[-0.0976,15.7224,0.1274],[-0.1015,15.8997,0.12811],
    [-0.1054,16.0762,0.12881],[-0.1094,16.2521,0.12951],[-0.1133,16.4273,0.1302],[-0.1172,16.6019,0.13088],[-0.1211,16.7759,0.13156],
    [-0.125,16.9494,0.13223],[-0.1289,17.1224,0.13289],[-0.1328,17.295,0.13355],[-0.1367,17.4671,0.13419],[-0.1406,17.639,0.13483],
    [-0.1445,17.8107,0.13545],[-0.1484,17.9822,0.13607],[-0.1522,18.1535,0.13667],[-0.156,18.3248,0.13726],[-0.1599,18.496,0.13785],
    [-0.1637,18.6672,0.13842]
  ];
  var W_GIRL = [
    [0.3809,3.2322,0.14171],[0.1714,4.1873,0.13724],[0.0962,5.1282,0.13322],[0.0402,5.8458,0.13086],[-0.005,6.4237,0.12965],
    [-0.043,6.8985,0.12894],[-0.0756,7.297,0.1285],[-0.1039,7.6422,0.12824],[-0.1288,7.9487,0.12811],[-0.1507,8.2254,0.12806],
    [-0.17,8.48,0.12809],[-0.1872,8.7192,0.12818],[-0.2024,8.9481,0.12832],[-0.2158,9.1699,0.1285],[-0.2278,9.387,0.12871],
    [-0.2384,9.601,0.12895],[-0.2478,9.8132,0.1292],[-0.2562,10.0242,0.12948],[-0.2637,10.2347,0.12977],[-0.2703,10.4446,0.13007],
    [-0.2762,10.6541,0.13039],[-0.2815,10.8634,0.13072],[-0.2862,11.0726,0.13106],[-0.2903,11.2819,0.13141],[-0.2941,11.4913,0.13176],
    [-0.2975,11.7002,0.13212],[-0.3005,11.9078,0.1325],[-0.3033,12.115,0.13289],[-0.3058,12.3221,0.13329],[-0.3081,12.5291,0.13371],
    [-0.3103,12.7361,0.13413],[-0.3122,12.9432,0.13456],[-0.314,13.15,0.13499],[-0.3157,13.3565,0.13543],[-0.3172,13.5625,0.13587],
    [-0.3186,13.7681,0.13632],[-0.3198,13.9731,0.13678],[-0.3209,14.1775,0.13724],[-0.3218,14.381,0.1377],[-0.3226,14.5837,0.13815],
    [-0.3233,14.7854,0.13861],[-0.3238,14.9861,0.13906],[-0.3241,15.1856,0.1395],[-0.3243,15.384,0.13994],[-0.3243,15.5812,0.14036],
    [-0.3241,15.777,0.14078],[-0.3237,15.9715,0.14119],[-0.323,16.1645,0.1416],[-0.322,16.3559,0.142],[-0.3208,16.5458,0.14239],
    [-0.3193,16.7341,0.14277],[-0.3174,16.9208,0.14314],[-0.3152,17.1059,0.1435],[-0.3127,17.2893,0.14385],[-0.3097,17.4711,0.14418],
    [-0.3064,17.6512,0.1445],[-0.3027,17.8297,0.14481],[-0.2986,18.0066,0.14511],[-0.2941,18.1819,0.1454],[-0.2891,18.3557,0.14567],
    [-0.2836,18.528,0.14593]
  ];

  // WHO length/height-for-age (cm), months 0..60. L is always 1 in WHO HFA.
  var H_BOY = [
    [1,49.8842,0.03795],[1,54.7244,0.03557],[1,58.4249,0.03424],[1,61.4292,0.03328],[1,63.886,0.03257],
    [1,65.9026,0.03204],[1,67.6236,0.03165],[1,69.1645,0.03139],[1,70.5994,0.03124],[1,71.9687,0.03117],
    [1,73.2812,0.03118],[1,74.5388,0.03125],[1,75.7488,0.03137],[1,76.9186,0.03154],[1,78.0497,0.03174],
    [1,79.1458,0.03197],[1,80.2113,0.03222],[1,81.2487,0.03249],[1,82.2587,0.03277],[1,83.2418,0.03306],
    [1,84.1996,0.03336],[1,85.1348,0.03366],[1,86.0477,0.03397],[1,86.941,0.03427],[1,87.8161,0.03459],
    [1,88.6748,0.0349],[1,89.5183,0.03521],[1,90.3482,0.03552],[1,91.1656,0.03582],[1,91.9715,0.03613],
    [1,92.7668,0.03643],[1,93.552,0.03672],[1,94.3275,0.03701],[1,95.0938,0.0373],[1,95.851,0.03758],
    [1,96.5993,0.03785],[1,97.3388,0.03812],[1,98.0699,0.03838],[1,98.7928,0.03864],[1,99.5076,0.03889],
    [1,100.2146,0.03914],[1,100.9139,0.03938],[1,101.6057,0.03962],[1,102.29,0.03985],[1,102.9671,0.04008],
    [1,103.637,0.04031],[1,104.2998,0.04053],[1,104.9558,0.04075],[1,105.605,0.04096],[1,106.2475,0.04117],
    [1,106.8832,0.04138],[1,107.5124,0.04158],[1,108.1349,0.04178],[1,108.751,0.04197],[1,109.3606,0.04216],
    [1,109.964,0.04235],[1,110.561,0.04253],[1,111.1519,0.04271],[1,111.7366,0.04289],[1,112.3153,0.04306],
    [1,112.888,0.04323]
  ];
  var H_GIRL = [
    [1,49.1477,0.0379],[1,53.6872,0.0364],[1,57.0673,0.03568],[1,59.8029,0.03502],[1,62.0899,0.03442],
    [1,64.0301,0.03386],[1,65.7311,0.03335],[1,67.2873,0.03288],[1,68.7498,0.03245],[1,70.1435,0.03207],
    [1,71.4818,0.03174],[1,72.771,0.03146],[1,74.015,0.03123],[1,75.2176,0.03105],[1,76.3817,0.03092],
    [1,77.5099,0.03084],[1,78.6055,0.0308],[1,79.671,0.0308],[1,80.7079,0.03083],[1,81.7182,0.03089],
    [1,82.7036,0.03098],[1,83.6654,0.0311],[1,84.604,0.03123],[1,85.5202,0.03139],[1,86.4153,0.03155],
    [1,87.2905,0.03171],[1,88.1473,0.03188],[1,88.9868,0.03205],[1,89.8103,0.03222],[1,90.6188,0.03239],
    [1,91.4131,0.03256],[1,92.1938,0.03273],[1,92.9614,0.0329],[1,93.7162,0.03307],[1,94.4585,0.03324],
    [1,95.1885,0.0334],[1,95.9063,0.03357],[1,96.6121,0.03373],[1,97.3057,0.03389],[1,97.9871,0.03404],
    [1,98.6562,0.0342],[1,99.3128,0.03435],[1,99.9568,0.0345],[1,100.588,0.03464],[1,101.206,0.03478],
    [1,101.8107,0.03492],[1,102.4018,0.03505],[1,102.9792,0.03518],[1,103.5427,0.0353],[1,104.0919,0.03542],
    [1,104.6265,0.03553],[1,105.1461,0.03564],[1,105.6507,0.03575],[1,106.1398,0.03585],[1,106.6129,0.03594],
    [1,107.0697,0.03603],[1,107.5099,0.03612],[1,107.9331,0.0362],[1,108.339,0.03628],[1,108.7275,0.03635],
    [1,109.0982,0.03642]
  ];

  // Normal CDF approximation
  function normalCdf(z) {
    var b1=0.319381530,b2=-0.356563782,b3=1.781477937,b4=-1.821255978,b5=1.330274429,p=0.2316419;
    var t=1/(1+p*Math.abs(z));
    var y=1-(1/Math.sqrt(2*Math.PI))*Math.exp(-z*z/2)*(b1*t+b2*t*t+b3*t*t*t+b4*t*t*t*t+b5*Math.pow(t,5));
    return z<0?1-y:y;
  }
  function lmsZScore(x,L,M,S){ if(L===0) return Math.log(x/M)/S; return (Math.pow(x/M,L)-1)/(L*S); }
  function percentile(z){ return Math.round(normalCdf(z)*100); }
  function formatPercentile(z){
    var p = normalCdf(z) * 100;
    if (p >= 99.5) return { label: '>99th', numeric: 99, tail: 'high' };
    if (p < 0.5)  return { label: '<1st',  numeric: 1,  tail: 'low'  };
    var n = Math.round(p);
    return { label: n + suffix(n), numeric: n, tail: null };
  }
  function suffix(n){ var s=n%100; if(s>=11&&s<=13) return 'th'; switch(n%10){case 1:return 'st';case 2:return 'nd';case 3:return 'rd';default:return 'th';} }
  function lookup(table,months){ months=Math.max(0,Math.min(60,Math.round(months))); return table[months]; }

  var form = document.getElementById('pct-form');
  if (!form) return;
  var result = document.getElementById('pct-result');
  var resultBig = document.getElementById('pct-big');
  var resultExpl = document.getElementById('pct-expl');
  var resultStats = document.getElementById('pct-stats');
  var errMsg = document.getElementById('pct-err');
  var unitToggle = document.querySelectorAll('[data-pct-unit]');
  var metricFields = document.querySelectorAll('[data-pct-metric]');
  var imperialFields = document.querySelectorAll('[data-pct-imperial]');
  var currentUnit = 'metric';

  function setUnit(u){ currentUnit=u; unitToggle.forEach(function(b){b.classList.toggle('active',b.dataset.pctUnit===u);}); metricFields.forEach(function(f){f.classList.toggle('hidden',u!=='metric');}); imperialFields.forEach(function(f){f.classList.toggle('hidden',u!=='imperial');}); }
  unitToggle.forEach(function(b){ b.addEventListener('click',function(){ setUnit(b.dataset.pctUnit); }); });

  form.addEventListener('submit', function (e) {
    e.preventDefault();
    errMsg.textContent = '';
    var sex = form.elements['sex'].value;
    var ageUnit = form.elements['age-unit'] ? form.elements['age-unit'].value : 'months';
    var ageVal = parseFloat(form.elements['age'].value);
    if (!(ageVal >= 0)) { errMsg.textContent = 'Enter your child\u2019s age.'; return; }
    var ageM = ageUnit === 'years' ? ageVal * 12 : ageVal;
    if (ageM > 60) { errMsg.textContent = 'This tool uses WHO standards for ages 0\u20135 years (0\u201360 months).'; return; }
    var weightKg, heightCm;
    if (currentUnit === 'metric') {
      weightKg = parseFloat(form.elements['weight-kg'].value);
      heightCm = parseFloat(form.elements['height-cm'].value);
    } else {
      var lb = parseFloat(form.elements['weight-lb'].value) || 0;
      var oz = parseFloat(form.elements['weight-oz'].value) || 0;
      weightKg = (lb + oz/16) * 0.453592;
      heightCm = parseFloat(form.elements['height-in'].value) * 2.54;
    }
    if (!(weightKg > 0)) { errMsg.textContent = 'Weight looks off.'; return; }
    if (!(heightCm > 0)) { errMsg.textContent = 'Length/height looks off.'; return; }

    var w = lookup(sex==='boy'?W_BOY:W_GIRL, ageM);
    var h = lookup(sex==='boy'?H_BOY:H_GIRL, ageM);
    var zW = lmsZScore(weightKg, w[0], w[1], w[2]);
    var zH = lmsZScore(heightCm, h[0], h[1], h[2]);
    var pW = percentile(zW);
    var pH = percentile(zH);
    var fW = formatPercentile(zW);
    var fH = formatPercentile(zH);
    var bmi = weightKg / Math.pow(heightCm/100, 2);

    resultBig.innerHTML = fW.label + ' <span style="font-size:0.45em;font-weight:600;color:#5A6B82;">percentile weight</span>';
    var ageLabel = ageM < 24 ? (ageM + ' month' + (ageM==1?'':'s')) : ((ageM/12).toFixed(1).replace(/\.0$/,'') + ' years');
    var explText = 'Compared to WHO growth standards for ' + sex + 's at ' + ageLabel + '.';
    if (fW.tail || fH.tail || Math.abs(zW) >= 2 || Math.abs(zH) >= 2) {
      explText += ' This result is outside the typical range. It may be normal for your child, but the AAP recommends discussing growth trends outside the 3rd\u201397th percentile band with your pediatrician.';
    }
    resultExpl.textContent = explText;
    resultStats.innerHTML = stat(fW.label,'Weight %') + stat(fH.label,'Height %') + stat(bmi.toFixed(1),'BMI');
    result.classList.remove('hidden');
    result.scrollIntoView({behavior:'smooth',block:'start'});

    if (window.gtag) {
      window.gtag('event', 'percentile_checked', {
        sex: sex,
        unit: currentUnit,
        age_months: Math.round(ageM)
      });
    }
  });

  function stat(num,label){ return '<div class="pl-stat"><div class="pl-stat-num">'+num+'</div><div class="pl-stat-label">'+label+'</div></div>'; }

  setUnit('metric');
  var tryagain = document.getElementById('pct-tryagain');
  if (tryagain) tryagain.addEventListener('click', function(e){ e.preventDefault(); result.classList.add('hidden'); form.reset(); setUnit('metric'); form.scrollIntoView({behavior:'smooth'}); });
})();
