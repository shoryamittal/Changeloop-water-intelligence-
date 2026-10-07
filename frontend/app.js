/* ==========================================================================
   ChangeLoop - water intelligence operating interface

   No framework, no build step. Every figure rendered here comes from the
   server; nothing is computed in the browser and nothing is hardcoded.

   Visual thesis: water is VOLUME MOVING THROUGH CONSTRAINED PATHS. One
   grammar is used everywhere a quantity of water appears - its THICKNESS is
   proportional to its volume. The flow field, the circularity network, the
   mass balance and the process river all obey it, so the interface reads as
   water without a droplet, wave or leaf anywhere in it.
   ========================================================================== */
'use strict';

/* ==========================================================================
   STATE
   ========================================================================== */
var S = {
  state: null, sites: null, modes: null, mode: 'NORMAL',
  view: 'command',
  forecast: null, insight: null, evidence: null, ablation: null,
  sensitivity: null, modeCompare: null, cluster: null, pilot: null,
  governance: null, matrix: null, businessCase: null,
  selectedStream: null,
  busy: false, loadedAt: null
};

var VIEWS = [
  { id: 'command',   label: 'Command',   group: 'Operations', ico: 'command' },
  { id: 'forecast',  label: 'Forecast',  group: 'Operations', ico: 'forecast' },
  { id: 'decisions', label: 'Decisions', group: 'Operations', ico: 'decisions' },
  { id: 'water',     label: 'Water',     group: 'Operations', ico: 'water' },
  { id: 'impact',    label: 'Impact',    group: 'Evidence',   ico: 'impact' },
  { id: 'evidence',  label: 'Evidence',  group: 'Evidence',   ico: 'evidence' },
  { id: 'audit',     label: 'Audit',     group: 'Evidence',   ico: 'audit' },
  { id: 'scenarios', label: 'Scenarios', group: 'Analysis',   ico: 'scenarios' }
];

/* ==========================================================================
   ICONS - one set, 16px, 1.4px stroke, no fills
   ========================================================================== */
var ICON = {
  command:   'M2 8h3.2l1.6-4 2.4 9 2-5h4',
  forecast:  'M2 12.5l3.2-4 2.6 2.2L11 5l3 3.6M2 2v12h12',
  decisions: 'M4 2v4.2a2 2 0 0 0 2 2h6M12 5.2 14 8l-2 2.8M4 14V9.8',
  water:     'M2 5h5.5a3 3 0 0 1 0 6H5.5M2 11h3M11 3.5 14 8l-3 4.5',
  impact:    'M2.5 13.5h11M4.5 11V6M8 11V3.5M11.5 11V8',
  evidence:  'M4 2h5l3 3v9H4zM9 2v3h3',
  audit:     'M8 2 3 4v4.5c0 3 2.1 5.1 5 6 2.9-.9 5-3 5-6V4zM6 8l1.6 1.6L10.5 6.7',
  scenarios: 'M3 3h10M5 3v4.2L3 13h10l-2-5.8V3',
  reset:     'M13 8a5 5 0 1 1-1.8-3.8M13 2v3h-3',
  export:    'M8 2v8M5 7l3 3 3-3M3 13h10',
  check:     'M3 8.4 6.2 11.6 13 4.8',
  cross:     'M4 4l8 8M12 4l-8 8',
  arrow:     'M3 8h9M9 5l3 3-3 3'
};

function ico(name, size) {
  var d = ICON[name] || ICON.command;
  var s = size || 15;
  return '<svg class="ico" width="' + s + '" height="' + s + '" ' +
    'viewBox="0 0 16 16" fill="none" stroke="currentColor" ' +
    'stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round" ' +
    'aria-hidden="true"><path d="' + d + '"/></svg>';
}

/* ==========================================================================
   FORMAT
   ========================================================================== */
function esc(s) {
  return String(s == null ? '' : s)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}

function num(v, dp) {
  if (v == null || v === '') return '—';
  var n = Number(v);
  if (!isFinite(n)) return '—';
  var d = (dp == null) ? (Math.abs(n) >= 100 ? 0 : Math.abs(n) >= 10 ? 1 : 2) : dp;
  return n.toLocaleString('en-IN', { minimumFractionDigits: d, maximumFractionDigits: d });
}
function inr(v) { return v == null ? '—' : '₹' + num(v, 0); }
function pct(v, dp) { return v == null ? '—' : num(v, dp == null ? 1 : dp) + '%'; }

/* a readout: label, big tabular number, unit, footnote */
function readout(opts) {
  return '<div class="readout ' + (opts.tone || '') + '"' +
    (opts.k ? ' data-k="' + esc(opts.k) + '" data-v="' + esc(opts.value) + '"' : '') +
    '><div class="readout-k">' + opts.label + '</div>' +
    '<div class="readout-v' + (opts.size ? ' ' + opts.size : '') + '">' +
    '<span>' + (opts.raw != null ? opts.raw : num(opts.value, opts.dp)) + '</span>' +
    (opts.unit ? '<span class="u">' + esc(opts.unit) + '</span>' : '') + '</div>' +
    (opts.foot ? '<div class="readout-f">' + opts.foot + '</div>' : '') + '</div>';
}

/* a delta where DOWN is good: we are reducing consumption */
function down(v, unit, dp) {
  if (v == null || !isFinite(Number(v))) return '<span class="delta flat">—</span>';
  var n = Number(v);
  if (Math.abs(n) < 0.005) return '<span class="delta flat">no change</span>';
  return '<span class="delta ' + (n > 0 ? 'down' : 'up') + '">' +
    (n > 0 ? '−' : '+') + num(Math.abs(n), dp) +
    (unit ? ' ' + esc(unit) : '') + '</span>';
}

function ev(kind) {
  var k = String(kind || 'MODELLED').toUpperCase().split(' ')[0];
  return '<span class="ev ev-' + esc(k) + '">' + esc(k) + '</span>';
}

function srule(title, note) {
  return '<div class="srule"><h2>' + esc(title) + '</h2>' +
    (note ? '<span class="note">' + note + '</span>' : '') + '</div>';
}

function phead(eyebrow, title, sub, aside) {
  return '<div class="phead"><div>' +
    '<div class="phead-eyebrow">' + esc(eyebrow) + '</div>' +
    '<h1>' + esc(title) + '</h1>' +
    (sub ? '<p class="phead-sub">' + sub + '</p>' : '') + '</div>' +
    '<div class="phead-aside">' + (aside || '') + '</div></div>';
}

function disc(title, html) {
  return '<details class="d"><summary>' + esc(title) + '</summary>' +
    '<div class="d-body">' + html + '</div></details>';
}

function row(k, v) { return '<div><dt>' + k + '</dt><dd>' + v + '</dd></div>'; }

function check(pass, name, detail) {
  return '<div class="check ' + (pass ? 'pass' : 'fail') + '">' +
    '<span class="mk">' + ico(pass ? 'check' : 'cross', 13) + '</span>' +
    '<span><span class="nm">' + esc(name) + '</span>' +
    (detail ? '<span class="dt">' + esc(detail) + '</span>' : '') +
    '</span></div>';
}

/* flow band: the core grammar. thickness is volume. */
function flowBand(label, value, unit, frac, tone, foot) {
  var h = Math.max(3, Math.round(3 + 15 * Math.max(0, Math.min(1, frac))));
  return '<div class="flow"><div class="flow-hd">' +
    '<span class="flow-k">' + label + '</span>' +
    '<span class="flow-v">' + num(value, 0) +
    (unit ? ' <span class="u">' + esc(unit) + '</span>' : '') + '</span></div>' +
    '<div class="flow-band" style="height:' + h + 'px">' +
    '<div class="flow-fill ' + tone + '" style="width:' +
    (Math.max(0, Math.min(1, frac)) * 100).toFixed(1) + '%"></div></div>' +
    (foot ? '<div class="flow-f">' + foot + '</div>' : '') + '</div>';
}

var toastT = null;
function toast(msg, isErr) {
  var t = document.getElementById('toast');
  t.textContent = msg;
  t.className = 'toast show' + (isErr ? ' err' : '');
  clearTimeout(toastT);
  toastT = setTimeout(function () { t.className = 'toast'; }, 4600);
}

/* ==========================================================================
   API
   ========================================================================== */
function api(path, opts) {
  var o = opts || {};
  o.headers = o.headers || { 'Content-Type': 'application/json' };
  return fetch(path, o).then(function (res) {
    return res.json().catch(function () { return null; }).then(function (b) {
      if (!res.ok) {
        var e = new Error((b && b.error && b.error.message) ||
          ('Request failed: ' + res.status));
        e.payload = b;
        throw e;
      }
      return b;
    });
  });
}
function post(path, data, idem) {
  var h = { 'Content-Type': 'application/json' };
  if (idem) h['Idempotency-Key'] = idem;
  return api(path, { method: 'POST', headers: h, body: JSON.stringify(data || {}) });
}

/* ==========================================================================
   BOOT
   ========================================================================== */
function boot() {
  Promise.all([api('/api/state'), api('/api/sites'), api('/api/modes')])
    .then(function (r) {
      S.state = r[0]; S.sites = r[1]; S.modes = r[2].modes;
      S.loadedAt = Date.now();
      renderChrome(); renderNav(); render();
      prefetch();
    })
    .catch(function (e) {
      document.getElementById('view').innerHTML =
        '<div class="sec"><div class="status fault">' +
        '<span class="status-k">Engine</span>' +
        '<span class="status-v">Unreachable</span>' +
        '<span class="status-t">' + esc(e.message) +
        '. Start it with <span class="mono">python backend/server.py</span>' +
        '</span></div></div>';
    });
}

function prefetch() {
  /* Background loads. Each is caught so a single slow or failed endpoint
     degrades one panel rather than the whole interface. */
  api('/api/forecast')
    .then(function (d) { S.forecast = d; soft('command'); soft('forecast'); })
    .catch(function () { S.forecast = null; });
  api('/api/insight/salt-is-water')
    .then(function (d) { S.insight = d; soft('command'); soft('water'); })
    .catch(function () { S.insight = null; });
  /* The explanation ladder. Served from core/narrative.py so the wording
     here, in the deck and in the video script cannot drift apart. */
  api('/api/narrative')
    .then(function (d) { S.narrative = d; soft('command'); })
    .catch(function () { S.narrative = null; });
}
function soft(v) { if (S.view === v) render(); }

function refreshState() {
  return api('/api/state').then(function (st) {
    S.state = st; S.loadedAt = Date.now();
    return api('/api/forecast').then(function (f) { S.forecast = f; });
  });
}

/* ==========================================================================
   CHROME: context bar + nav
   ========================================================================== */
function renderChrome() {
  var st = S.state, b = st.basin;

  document.getElementById('brandCtx').innerHTML =
    '<b>' + esc(b.cluster.split(',')[0]) + '</b><br>' +
    esc(st.machine.name) + ' &middot; shift 1';

  var siteSel = document.getElementById('siteSel');
  siteSel.innerHTML = S.sites.sites.map(function (s) {
    return '<option value="' + esc(s.site_id) + '"' +
      (s.site_id === st.site_id ? ' selected' : '') + '>' +
      esc(s.cluster.split(',')[0]) + '</option>';
  }).join('');
  siteSel.onchange = function () {
    guard(function () {
      return post('/api/session/site', { site_id: siteSel.value })
        .then(function (x) {
          S.state = x;
          S.ablation = S.sensitivity = S.modeCompare = S.forecast = null;
          return api('/api/forecast').then(function (f) { S.forecast = f; });
        })
        .then(function () {
          toast('Site changed. Downstream decisions invalidated: the basin ' +
            'weighting, allocation and cost basis all differ.');
        });
    });
  };

  var modeSel = document.getElementById('modeSel');
  modeSel.innerHTML = Object.keys(S.modes).map(function (k) {
    return '<option value="' + esc(k) + '"' + (k === S.mode ? ' selected' : '') +
      '>' + esc(S.modes[k].name) + '</option>';
  }).join('');
  modeSel.onchange = function () {
    S.mode = modeSel.value;
    S.ablation = S.sensitivity = null;
    guard(function () {
      return post('/api/optimise', { mode: S.mode })
        .then(function (x) { S.state = x; return api('/api/forecast'); })
        .then(function (f) {
          S.forecast = f;
          toast('Re-optimised under ' + S.modes[S.mode].name + '.');
          if (S.view === 'command') S.view = 'decisions';
        });
    });
  };

  document.getElementById('resetBtn').onclick = function () {
    guard(function () {
      return post('/api/session/reset', {})
        .then(function (x) {
          S.state = x; S.businessCase = null; S.selectedStream = null;
          S.view = 'command';
          return api('/api/forecast');
        })
        .then(function (f) { S.forecast = f; toast('Session reset. New ledger chain started.'); });
    });
  };
  document.getElementById('cmdBtn').onclick = openPalette;
  wireTheme();

  updateCtx();
}

function updateCtx() {
  var st = S.state;
  var imp = st.impact;
  var fc = S.forecast && S.forecast.plan;

  document.getElementById('ctxAsset').textContent = st.machine.machine_id;

  var rState = 'NORMAL', rCls = '';
  if (fc) {
    var r = fc.envelope.risk;
    if (r === 'BREACH_PROJECTED') { rState = 'BREACH PROJECTED'; rCls = 'fault'; }
    else if (r === 'AT_RISK') { rState = 'AT RISK'; rCls = 'warn'; }
    else if (r === 'TIGHT') { rState = 'TIGHT'; rCls = 'warn'; }
    else { rState = 'WITHIN ALLOWANCE'; }
  }
  document.getElementById('ctxResource').innerHTML =
    '<span class="dot ' + rCls + '"></span>' + rState;

  var age = S.loadedAt ? Math.round((Date.now() - S.loadedAt) / 1000) : null;
  document.getElementById('ctxData').innerHTML =
    age == null ? '—'
      : (age < 90 ? '<span class="dot"></span>' + age + ' s ago'
         : '<span class="dot idle"></span>stale, ' + Math.round(age / 60) + ' min');

  var ok = imp && imp.validation && imp.validation.all_pass;
  var lok = st.ledger_integrity && st.ledger_integrity.intact;
  document.getElementById('ctxSystem').innerHTML =
    '<span class="dot ' + (ok && lok ? '' : 'fault') + '"></span>' +
    (ok && lok ? 'OPERATIONAL' : 'CHECK FAILED');
}

/* ---------- theme ----------------------------------------------------
   Dark is the default, set in CSS so it holds without JavaScript. Only an
   explicit light choice is recorded. The button label always names what it
   will DO, not the current state. */
function isDark() {
  return document.documentElement.getAttribute('data-theme') !== 'light';
}
function syncThemeLabel() {
  var el = document.getElementById('themeLbl');
  if (el) el.textContent = isDark() ? 'Light' : 'Dark';
}
function setTheme(next) {
  document.documentElement.setAttribute('data-theme', next);
  try { localStorage.setItem('cl-theme', next); } catch (e) { /* ignore */ }
  syncThemeLabel();
  /* The SVG visuals read their colours from custom properties, so they are
     re-rendered to pick the new set up cleanly rather than being restyled
     in place. */
  render();
}
function wireTheme() {
  var b = document.getElementById('themeBtn');
  if (b) b.onclick = function () { setTheme(isDark() ? 'light' : 'dark'); };
  syncThemeLabel();
}

function renderNav() {
  var html = '', lastGroup = null;
  VIEWS.forEach(function (v) {
    if (v.group !== lastGroup) {
      html += '<div class="nav-group">' + esc(v.group) + '</div>';
      lastGroup = v.group;
    }
    html += '<button class="nav-item" data-view="' + v.id + '"' +
      (v.id === S.view ? ' aria-current="page"' : '') + '>' +
      ico(v.ico) + '<span class="lbl">' + esc(v.label) + '</span></button>';
  });
  var nav = document.getElementById('nav');
  nav.innerHTML = html;
  Array.prototype.forEach.call(nav.querySelectorAll('.nav-item'), function (b) {
    b.onclick = function () { go(b.dataset.view); };
  });
}

function go(v) {
  S.view = v; renderNav(); render();
  document.querySelector('.page').scrollIntoView({ block: 'start' });
  window.scrollTo(0, 0);
}

function guard(fn) {
  if (S.busy) return Promise.resolve();
  S.busy = true;
  return Promise.resolve().then(fn)
    .catch(function (e) { toast(e.message, true); })
    .then(function () {
      S.busy = false; S.loadedAt = Date.now();
      render(); renderNav(); updateCtx();
    });
}

/* ==========================================================================
   RENDER
   ========================================================================== */
var LAST = {};
function render() {
  var map = {
    command: vCommand, forecast: vForecast, decisions: vDecisions,
    water: vWater, impact: vImpact, evidence: vEvidence,
    audit: vAudit, scenarios: vScenarios
  };
  document.getElementById('view').innerHTML = (map[S.view] || vCommand)();
  wire();
  markChanges();
  updateCtx();
}

/* marks what moved. never invents a movement. */
function markChanges() {
  Array.prototype.forEach.call(
    document.querySelectorAll('#view .readout[data-k]'), function (el) {
      var k = el.dataset.k, v = el.dataset.v;
      if (LAST[k] !== undefined && LAST[k] !== v) el.classList.add('changed');
      LAST[k] = v;
    });
}

/* ==========================================================================
   SIGNATURE VISUAL 1 - FLOW FIELD
   The command hero. Volume as thickness, the loop that does not close.
   ========================================================================== */
function flowField(sc, live) {
  if (!sc) return '';
  var W = 940, H = 300;
  var w = sc.water, z = sc.zld;

  var demand = w.process_demand_l;
  var reuse = w.permeate_reuse_l;
  var reject = z.reject_l;
  var fresh = w.freshwater_intake_l;
  var maxV = Math.max(demand, 1);
  var T = function (v) { return Math.max(2, (v / maxV) * 46); };   // thickness

  var yMain = 150;
  var xProc = 120, xRO = 430, xSplit = 520, xEvap = 720, xStack = 870;
  var yReuse = 74, yRej = 226;

  function band(d, cls, v, extra) {
    return '<path class="' + cls + (live ? ' vz-live' : '') + '" d="' + d +
      '" stroke-width="' + T(v).toFixed(1) + '"' + (extra || '') + '/>';
  }

  return '<div class="viz viz-wide"><svg viewBox="0 0 ' + W + ' ' + H + '" ' +
    'role="img" aria-label="Water flow field: process demand through reverse ' +
    'osmosis, permeate returning to process and reject evaporated, with ' +
    'freshwater makeup replacing the evaporative loss">' +

    /* ---- reuse loop: permeate returns to the process. drawn first so it
            sits behind the nodes, and it is what makes the loop legible. */
    band('M' + xSplit + ',' + yMain + ' C' + (xSplit + 60) + ',' + yMain +
         ' ' + (xSplit + 40) + ',' + yReuse + ' ' + (xSplit - 40) + ',' + yReuse +
         ' L' + (xProc - 34) + ',' + yReuse +
         ' C' + (xProc - 74) + ',' + yReuse + ' ' + (xProc - 74) + ',' + yMain +
         ' ' + (xProc - 34) + ',' + yMain, 'vz-flow-reuse', reuse) +

    /* ---- demand: process to RO */
    band('M' + xProc + ',' + yMain + ' L' + xRO + ',' + yMain, 'vz-flow', demand) +

    /* ---- reject: RO down to the evaporator */
    band('M' + xSplit + ',' + yMain + ' C' + (xSplit + 60) + ',' + yMain +
         ' ' + (xEvap - 90) + ',' + yRej + ' ' + xEvap + ',' + yRej,
         'vz-flow-salt', reject) +

    /* ---- vapour: destroyed, leaves the system upward */
    band('M' + (xEvap + 46) + ',' + yRej + ' C' + (xEvap + 110) + ',' + yRej +
         ' ' + (xStack - 20) + ',' + (yRej - 60) + ' ' + xStack + ',' + 92,
         'vz-flow-loss', reject) +

    /* ---- freshwater makeup: replaces exactly what was evaporated */
    band('M' + (xProc - 34) + ',' + 248 + ' L' + (xProc - 34) + ',' + (yMain + T(demand) / 2) +
         '', 'vz-flow-pale', fresh) +

    /* ---- nodes ---- */
    nodeBox(xProc - 34 - 52, yMain - 30, 104, 60, 'Dyehouse', num(demand, 0), 'L demand', true) +
    nodeBox(xRO, yMain - 34, 90, 68, 'RO', pct(z.ro_recovery_frac * 100, 1), 'recovery', true) +
    nodeBox(xEvap - 46, yRej - 26, 92, 52, 'Evaporator', num(z.mee_thermal_kwh, 0), 'kWh th') +
    nodeBox(xStack - 46, 56, 92, 52, 'Emissions', num(sc.carbon.mee_thermal_co2e_kg, 0), 'kg CO2e') +

    /* ---- annotations: the sentence the picture is making ---- */
    '<text class="vz-lbl-k" x="' + (xProc - 120) + '" y="268">Freshwater makeup</text>' +
    '<text class="vz-val" x="' + (xProc - 120) + '" y="286">' + num(fresh, 0) +
    '<tspan class="vz-unit"> L from basin</tspan></text>' +

    '<text class="vz-lbl-k" x="' + (xProc + 100) + '" y="' + (yReuse - 18) + '">' +
    'Permeate returned to process</text>' +
    '<text class="vz-val" x="' + (xProc + 100) + '" y="' + (yReuse - 2) + '">' +
    num(reuse, 0) + '<tspan class="vz-unit"> L reused</tspan></text>' +

    '<text class="vz-lbl" x="' + (xStack - 40) + '" y="' + 132 + '">destroyed as vapour</text>' +
    '<text class="vz-lbl" text-anchor="end" x="' + (W - 12) + '" y="' + (H - 10) +
    '">band thickness = volume</text>' +

    '</svg>' +
    '<div class="legend">' +
    lg('var(--water)', 'Process demand') +
    lg('var(--emerald)', 'Permeate reused') +
    lg('var(--salt)', 'Salt-bearing reject') +
    lg('var(--hair-3)', 'Evaporative loss') +
    lg('var(--water-pale)', 'Freshwater makeup') +
    '</div></div>';
}

function nodeBox(x, y, w, h, label, value, unit, key) {
  return '<rect class="' + (key ? 'vz-node-key' : 'vz-node') + '" x="' + x +
    '" y="' + y + '" width="' + w + '" height="' + h + '" rx="2"/>' +
    '<text class="vz-lbl-k" x="' + (x + 9) + '" y="' + (y + 17) + '">' +
    esc(label) + '</text>' +
    '<text class="vz-val" x="' + (x + 9) + '" y="' + (y + 36) + '">' +
    esc(value) + '</text>' +
    '<text class="vz-unit" x="' + (x + 9) + '" y="' + (y + 48) + '">' +
    esc(unit) + '</text>';
}

function lg(colour, label) {
  return '<span class="lg"><i style="background:' + colour + '"></i>' +
    esc(label) + '</span>';
}

/* ==========================================================================
   SIGNATURE VISUAL 2 - WATER CIRCULARITY NETWORK
   Source -> treatment -> operation -> recovery -> quality gate -> destinations
   ========================================================================== */
function waterNetwork(sc, sel) {
  if (!sc) return '';
  var W = 940, H = 420;
  var w = sc.water, z = sc.zld;

  var fresh = w.freshwater_intake_l;
  var demand = w.process_demand_l;
  var effluent = z.effluent_volume_l;
  var permeate = z.permeate_l;
  var reject = z.reject_l;
  var reuse = w.permeate_reuse_l;
  var maxV = Math.max(demand, effluent, 1);
  var T = function (v) { return Math.max(2, (v / maxV) * 40); };

  var nodes = [
    { id: 'source',  x: 40,  y: 40,  w: 130, h: 54, t: 'Basin source', v: num(fresh, 0), u: 'L abstracted' },
    { id: 'treat',   x: 40,  y: 140, w: 130, h: 54, t: 'Intake treatment', v: 'softened', u: 'to process spec' },
    { id: 'op',      x: 300, y: 140, w: 150, h: 64, t: 'Dyeing operation', v: num(demand, 0), u: 'L demand', key: true },
    { id: 'eff',     x: 300, y: 262, w: 150, h: 54, t: 'Effluent', v: num(z.effluent_tds_mg_l, 0), u: 'mg/L TDS' },
    { id: 'ro',      x: 540, y: 262, w: 130, h: 64, t: 'RO recovery', v: pct(z.ro_recovery_frac * 100, 1), u: 'recovery', key: true },
    { id: 'gate',    x: 540, y: 140, w: 130, h: 54, t: 'Quality gate', v: 'screened', u: 'suitability' },
    { id: 'reuse',   x: 770, y: 140, w: 130, h: 54, t: 'Reuse', v: num(reuse, 0), u: 'L to process' },
    { id: 'evap',    x: 770, y: 262, w: 130, h: 54, t: 'Evaporator', v: num(reject, 0), u: 'L reject' },
    { id: 'solids',  x: 770, y: 352, w: 130, h: 48, t: 'Recovered solids', v: num(z.recovered_solids_kg, 1), u: 'kg salt' },
    { id: 'loss',    x: 540, y: 352, w: 130, h: 48, t: 'Evaporative loss', v: num(reject, 0), u: 'L as vapour' }
  ];

  var links = [
    { from: 'source', to: 'treat',  v: fresh,     cls: 'vz-flow-pale',  id: 'fresh' },
    { from: 'treat',  to: 'op',     v: fresh,     cls: 'vz-flow-pale',  id: 'fresh' },
    { from: 'reuse',  to: 'op',     v: reuse,     cls: 'vz-flow-reuse', id: 'reuse' },
    { from: 'op',     to: 'eff',    v: effluent,  cls: 'vz-flow',       id: 'effluent' },
    { from: 'eff',    to: 'ro',     v: effluent,  cls: 'vz-flow-salt',  id: 'effluent' },
    { from: 'ro',     to: 'gate',   v: permeate,  cls: 'vz-flow',       id: 'permeate' },
    { from: 'gate',   to: 'reuse',  v: reuse,     cls: 'vz-flow-reuse', id: 'reuse' },
    { from: 'ro',     to: 'evap',   v: reject,    cls: 'vz-flow-salt',  id: 'reject' },
    { from: 'evap',   to: 'solids', v: reject * 0.04, cls: 'vz-flow-salt', id: 'solids' },
    { from: 'evap',   to: 'loss',   v: reject,    cls: 'vz-flow-loss',  id: 'loss' }
  ];

  var byId = {};
  nodes.forEach(function (n) { byId[n.id] = n; });

  function port(n, side) {
    if (side === 'r') return [n.x + n.w, n.y + n.h / 2];
    if (side === 'l') return [n.x, n.y + n.h / 2];
    if (side === 'b') return [n.x + n.w / 2, n.y + n.h];
    return [n.x + n.w / 2, n.y];
  }

  var paths = links.map(function (l) {
    var a = byId[l.from], b = byId[l.to];
    var p1, p2;
    if (Math.abs((a.y + a.h / 2) - (b.y + b.h / 2)) < 20) {
      p1 = port(a, b.x > a.x ? 'r' : 'l');
      p2 = port(b, b.x > a.x ? 'l' : 'r');
    } else if (b.y > a.y) { p1 = port(a, 'b'); p2 = port(b, 't'); }
    else { p1 = port(a, 't'); p2 = port(b, 'b'); }

    var mx = (p1[0] + p2[0]) / 2, my = (p1[1] + p2[1]) / 2;
    var d = 'M' + p1[0] + ',' + p1[1] +
      ' C' + mx + ',' + p1[1] + ' ' + mx + ',' + p2[1] + ' ' + p2[0] + ',' + p2[1];
    var dim = sel && sel !== l.id ? ' vz-dim' : '';
    return '<path class="' + l.cls + dim + '" d="' + d + '" stroke-width="' +
      T(l.v).toFixed(1) + '" data-stream="' + l.id + '"/>';
  }).join('');

  var boxes = nodes.map(function (n) {
    var dim = sel && !linkTouches(links, sel, n.id) ? ' vz-dim' : '';
    return '<g class="' + dim.trim() + '">' +
      nodeBox(n.x, n.y, n.w, n.h, n.t, n.v, n.u, n.key) + '</g>';
  }).join('');

  return '<div class="viz viz-wide' + (sel ? ' has-sel' : '') + '">' +
    '<svg viewBox="0 0 ' + W + ' ' + H + '" role="img" ' +
    'aria-label="Water circularity network from basin source through the ' +
    'dyeing operation, recovery, quality gate and destinations">' +
    paths + boxes + '</svg>' +
    '<div class="legend">' +
    lg('var(--water-pale)', 'Freshwater') +
    lg('var(--water)', 'Process / permeate') +
    lg('var(--salt)', 'Salt-bearing') +
    lg('var(--emerald)', 'Reused') +
    lg('var(--hair-3)', 'Destroyed') +
    '<span class="lg nowrap">thickness = volume</span>' +
    '</div></div>';
}

function linkTouches(links, streamId, nodeId) {
  for (var i = 0; i < links.length; i++) {
    if (links[i].id === streamId &&
        (links[i].from === nodeId || links[i].to === nodeId)) return true;
  }
  return false;
}

/* ==========================================================================
   SIGNATURE VISUAL 3 - MASS BALANCE
   Engineering accounting. Bands that must sum, and a stated variance.
   ========================================================================== */
function massBalance(sc) {
  if (!sc) return '';
  var w = sc.water, z = sc.zld;
  var input = w.process_demand_l;
  var outs = [
    { k: 'Permeate recovered', v: z.permeate_l, tone: 'water',
      f: 'returned to the RO outlet' },
    { k: 'Reused in process', v: w.permeate_reuse_l, tone: 'emerald',
      f: 'bounded by both recovery and demand' },
    { k: 'Evaporated at the MEE', v: z.reject_l, tone: 'loss',
      f: 'leaves as vapour, not available for reuse' },
    { k: 'Freshwater makeup', v: w.freshwater_intake_l, tone: 'pale',
      f: 'new abstraction from the basin' }
  ];
  var variance = input - (w.permeate_reuse_l + w.freshwater_intake_l);

  return '<div class="stack">' +
    '<div class="flows">' +
      flowBand('<b>Input</b> &mdash; process demand', input, 'L', 1, 'water',
        'everything below must reconcile against this') +
    '</div>' +
    '<div class="flows" style="padding-left:var(--s5);border-left:1px solid var(--hair)">' +
      outs.map(function (o) {
        return flowBand(esc(o.k), o.v, 'L', input > 0 ? o.v / input : 0, o.tone, o.f);
      }).join('') +
    '</div>' +
    '<div class="status ' + (Math.abs(variance) < 0.5 ? 'ok' : 'fault') + '">' +
      '<span class="status-k">Balance</span>' +
      '<span class="status-v">' + num(variance, 1) + ' L variance</span>' +
      '<span class="status-t">' +
      (Math.abs(variance) < 0.5
        ? 'Demand is met exactly by reuse plus fresh intake. No reconciliation term.'
        : 'Balance does not close. The figure is not fit to display.') +
      '</span></div>' +
    disc('How this closes',
      '<div class="formula">process_demand = permeate_reuse + freshwater_intake</div>' +
      '<p style="margin-top:10px">Reuse is bounded twice: it cannot exceed ' +
      'what RO produced, and it cannot exceed what the process demanded. ' +
      'That double bound is what prevents the classic double count.</p>' +
      '<p>Evaporative loss is reported separately because the water is ' +
      'destroyed, not recovered. In a closed loop it equals the freshwater ' +
      'makeup exactly, which is why basin draw tracks evaporator duty.</p>') +
    '</div>';
}

/* ==========================================================================
   SIGNATURE VISUAL 4 - PROCESS RIVER
   Two aligned paths. Width swells where a changeover burden appears.
   ========================================================================== */
function processRiver(baselineOrder, planOrder, transitions, baseTransitions) {
  var lots = S.state.lots;
  function lot(id) {
    for (var i = 0; i < lots.length; i++) if (lots[i].lot_id === id) return lots[i];
    return {};
  }
  var W = 940, rowH = 92, H = rowH * 2 + 56;
  var n = Math.max(baselineOrder.length, planOrder.length);
  var xs = 90, xe = W - 40;
  var step = (xe - xs) / Math.max(1, n - 1);

  var maxW = 0;
  [transitions, baseTransitions].forEach(function (ts) {
    (ts || []).forEach(function (t) { if (t.water_l > maxW) maxW = t.water_l; });
  });

  function path(order, trans, y, cls, label) {
    var out = '';
    /* channel segments: thickness carries the changeover burden */
    for (var i = 0; i < order.length - 1; i++) {
      var t = (trans || []).filter(function (x) {
        return x.from_lot === order[i] && x.to_lot === order[i + 1];
      })[0] || { water_l: 0, cleaning_baths: 0 };
      var th = maxW > 0 ? Math.max(1.5, (t.water_l / maxW) * 26) : 1.5;
      var x1 = xs + i * step, x2 = xs + (i + 1) * step;
      out += '<path class="' + (t.water_l > 0 ? 'vz-flow-salt' : 'vz-flow-pale') +
        '" d="M' + x1 + ',' + y + ' L' + x2 + ',' + y + '" stroke-width="' +
        th.toFixed(1) + '"/>';
      if (t.water_l > 0) {
        out += '<text class="vz-val" text-anchor="middle" x="' +
          ((x1 + x2) / 2) + '" y="' + (y - th / 2 - 8) + '">' +
          num(t.water_l, 0) + '<tspan class="vz-unit"> L</tspan></text>' +
          '<text class="vz-lbl" text-anchor="middle" x="' + ((x1 + x2) / 2) +
          '" y="' + (y + th / 2 + 15) + '">' + t.cleaning_baths +
          ' cleaning bath' + (t.cleaning_baths === 1 ? '' : 's') + '</text>';
      }
    }
    /* lot nodes, coloured by actual shade */
    order.forEach(function (id, i) {
      var l = lot(id), x = xs + i * step;
      out += '<circle cx="' + x + '" cy="' + y + '" r="9" fill="' +
        esc(l.shade_hex || '#999') + '" stroke="var(--surface)" stroke-width="2"/>' +
        '<text class="vz-tick" text-anchor="middle" x="' + x + '" y="' + (y + 26) +
        '">' + esc(id) + '</text>';
    });
    out += '<text class="vz-lbl-k" x="12" y="' + (y - 4) + '">' + esc(label) + '</text>';
    return out;
  }

  var baseTotal = (baseTransitions || []).reduce(function (a, t) { return a + t.water_l; }, 0);
  var planTotal = (transitions || []).reduce(function (a, t) { return a + t.water_l; }, 0);

  return '<div class="viz viz-wide"><svg viewBox="0 0 ' + W + ' ' + H + '" ' +
    'role="img" aria-label="Baseline and recommended lot sequences as two ' +
    'aligned channels, where channel width is the changeover water burden">' +
    path(baselineOrder, baseTransitions, 44, '', 'Baseline') +
    '<line class="vz-grid" x1="12" x2="' + (W - 12) + '" y1="' + (rowH + 2) +
    '" y2="' + (rowH + 2) + '"/>' +
    path(planOrder, transitions, rowH + 52, '', 'ChangeLoop') +
    '<text class="vz-lbl" text-anchor="end" x="' + (W - 12) + '" y="' + (H - 8) +
    '">channel width = changeover water</text>' +
    '</svg>' +
    '<div class="legend">' +
    '<span class="lg">Baseline changeover water <b class="mono">&nbsp;' +
    num(baseTotal, 0) + ' L</b></span>' +
    '<span class="lg">ChangeLoop <b class="mono">&nbsp;' + num(planTotal, 0) +
    ' L</b></span>' +
    '<span class="lg">' + down(baseTotal - planTotal, 'L', 0) + '</span>' +
    '</div></div>';
}

/* ==========================================================================
   SIGNATURE VISUAL 5 - FORECAST INSTRUMENT
   Cumulative draw vs the abstraction envelope, with an uncertainty band.
   ========================================================================== */
function forecastChart(cmp) {
  if (!cmp) return '';
  var plan = cmp.plan, base = cmp.baseline;
  var steps = plan.steps, bsteps = base.steps;
  var W = 940, H = 330, L = 78, R = 150, T = 20, B = 46;

  var alloc = plan.envelope.allocation_l;
  var maxY = Math.max(alloc * 1.12,
    steps[steps.length - 1].band_high_l,
    bsteps[bsteps.length - 1].cumulative_freshwater_l) * 1.04;

  var n = steps.length;
  var X = function (i) { return L + (W - L - R) * i / Math.max(1, n - 1); };
  var Y = function (v) { return T + (H - T - B) * (1 - v / maxY); };

  function line(arr, key) {
    return arr.map(function (s, i) {
      return (i ? 'L' : 'M') + X(i).toFixed(1) + ',' + Y(s[key]).toFixed(1);
    }).join(' ');
  }
  var bandPath = steps.map(function (s, i) {
    return (i ? 'L' : 'M') + X(i).toFixed(1) + ',' + Y(s.band_high_l).toFixed(1);
  }).join(' ') + ' ' + steps.slice().reverse().map(function (s, i) {
    var idx = n - 1 - i;
    return 'L' + X(idx).toFixed(1) + ',' + Y(s.band_low_l).toFixed(1);
  }).join(' ') + ' Z';

  var yAlloc = Y(alloc);
  var breach = plan.envelope.breach_hour;
  var breachRect = breach != null
    ? '<rect class="vz-breach" x="' + X(breach) + '" y="' + T + '" width="' +
      (W - R - X(breach)) + '" height="' + (H - T - B) + '"/>' : '';

  var ticks = [0, 0.25, 0.5, 0.75, 1].map(function (f) {
    var v = maxY * f, y = Y(v);
    return '<line class="vz-grid" x1="' + L + '" x2="' + (W - R) + '" y1="' + y +
      '" y2="' + y + '"/><text class="vz-tick" text-anchor="end" x="' + (L - 8) +
      '" y="' + (y + 3) + '">' + num(v, 0) + '</text>';
  }).join('');

  var hourTicks = steps.map(function (s, i) {
    if (i % 3 !== 0) return '';
    return '<text class="vz-tick" text-anchor="middle" x="' + X(i) + '" y="' +
      (H - B + 16) + '">' + esc(s.clock) + '</text>';
  }).join('');

  /* the hour the schedule ends: beyond it the queue is simply done */
  var lastActive = 0;
  steps.forEach(function (s, i) { if (s.freshwater_l > 0) lastActive = i; });

  return '<div class="viz viz-wide"><svg viewBox="0 0 ' + W + ' ' + H + '" ' +
    'role="img" aria-label="Cumulative freshwater draw against the ' +
    'machine-shift abstraction allocation, for the baseline and the ' +
    'recommended plan, with a declared uncertainty band">' +
    breachRect + ticks +

    /* uncertainty band */
    '<path class="vz-area-band" d="' + bandPath + '"/>' +

    /* allocation envelope */
    '<line class="vz-threshold" x1="' + L + '" x2="' + (W - R) + '" y1="' +
    yAlloc + '" y2="' + yAlloc + '"/>' +
    '<text class="vz-lbl-k" x="' + (W - R + 10) + '" y="' + (yAlloc - 4) +
    '" style="fill:var(--coral)">Allocation</text>' +
    '<text class="vz-val" x="' + (W - R + 10) + '" y="' + (yAlloc + 13) +
    '">' + num(alloc, 0) + '<tspan class="vz-unit"> L</tspan></text>' +

    /* baseline: what happens with no intervention */
    '<path class="vz-trace" style="stroke:var(--hair-3);stroke-dasharray:4 3" d="' +
    line(bsteps, 'cumulative_freshwater_l') + '"/>' +

    /* the plan */
    '<path class="vz-trace" style="stroke:var(--water);stroke-width:2" d="' +
    line(steps, 'cumulative_freshwater_l') + '"/>' +

    /* end-of-schedule marker */
    '<line class="vz-marker" x1="' + X(lastActive) + '" x2="' + X(lastActive) +
    '" y1="' + T + '" y2="' + (H - B) + '" style="stroke-dasharray:2 3"/>' +
    '<text class="vz-lbl" text-anchor="middle" x="' + X(lastActive) + '" y="' +
    (T + 12) + '">queue complete</text>' +

    /* endpoint callouts */
    '<circle class="vz-pt" cx="' + X(n - 1) + '" cy="' +
    Y(steps[n - 1].cumulative_freshwater_l) + '" r="3.5" style="stroke:var(--water)"/>' +
    '<text class="vz-lbl-k" x="' + (W - R + 10) + '" y="' +
    (Y(steps[n - 1].cumulative_freshwater_l) - 4) + '">ChangeLoop</text>' +
    '<text class="vz-val" x="' + (W - R + 10) + '" y="' +
    (Y(steps[n - 1].cumulative_freshwater_l) + 13) + '">' +
    num(steps[n - 1].cumulative_freshwater_l, 0) + '<tspan class="vz-unit"> L</tspan></text>' +

    '<text class="vz-lbl" x="' + (W - R + 10) + '" y="' +
    (Y(bsteps[n - 1].cumulative_freshwater_l) + 4) + '">baseline ' +
    num(bsteps[n - 1].cumulative_freshwater_l, 0) + ' L</text>' +

    /* axes */
    '<line class="vz-axis" x1="' + L + '" x2="' + (W - R) + '" y1="' + (H - B) +
    '" y2="' + (H - B) + '"/>' +
    '<line class="vz-axis" x1="' + L + '" x2="' + L + '" y1="' + T + '" y2="' +
    (H - B) + '"/>' + hourTicks +
    '<text class="vz-lbl" x="' + L + '" y="' + (H - 8) + '">shift hour</text>' +
    '<text class="vz-lbl" transform="translate(16,' + (T + 92) +
    ') rotate(-90)">cumulative freshwater draw, L</text>' +
    '</svg>' +
    '<div class="legend">' +
    lg('var(--water)', 'ChangeLoop plan') +
    lg('var(--hair-3)', 'Baseline, no intervention') +
    lg('var(--water-pale)', 'Declared uncertainty band') +
    lg('var(--coral)', 'Abstraction allocation') +
    '</div></div>';
}

/* ==========================================================================
   SIGNATURE VISUAL 6 - TELEMETRY INSTRUMENT
   ========================================================================== */
function telemetry(w) {
  if (!w) return '';
  var W = 940, H = 280, L = 70, R = 120, T = 18, B = 42;
  var n = w.scheduled_baths;
  var byBath = [];
  for (var i = 0; i < n; i++) {
    var cs = [], cols = [], temps = [];
    w.samples.forEach(function (x) {
      if (x.bath_index !== i) return;
      if (x.conductivity_ms_cm != null) cs.push(x.conductivity_ms_cm);
      if (x.residual_colour_admi != null) cols.push(x.residual_colour_admi);
      temps.push(x.temp_c);
    });
    byBath.push({
      cond: cs.length ? cs.reduce(function (a, b) { return a + b; }, 0) / cs.length : null,
      col: cols.length ? Math.max.apply(null, cols) : null,
      temp: temps.length ? temps.reduce(function (a, b) { return a + b; }, 0) / temps.length : null
    });
  }
  var maxC = 1, maxCol = 1;
  byBath.forEach(function (b) {
    if (b.cond > maxC) maxC = b.cond;
    if (b.col > maxCol) maxCol = b.col;
  });
  var lim = S.state.release_limits;
  var X = function (i) { return L + (W - L - R) * i / Math.max(1, n - 1); };
  var YC = function (v) { return T + (H - T - B) * (1 - v / maxC); };
  var YL = function (v) { return T + (H - T - B) * (1 - v / maxCol); };

  function trace(key, sc, cls) {
    var d = [], first = true;
    byBath.forEach(function (b, i) {
      if (b[key] == null) return;
      d.push((first ? 'M' : 'L') + X(i).toFixed(1) + ',' + sc(b[key]).toFixed(1));
      first = false;
    });
    return '<path class="vz-trace ' + cls + '" d="' + d.join(' ') + '"/>';
  }

  var yLim = YC(lim.conductivity_release_ms_cm);
  var savedFrom = w.baths_avoidable > 0 ? X(n - w.baths_avoidable) : null;

  return '<div class="viz viz-wide"><svg viewBox="0 0 ' + W + ' ' + H + '" ' +
    'role="img" aria-label="Conductivity and residual colour decay across ' +
    'the scheduled wash-off baths, against the release limit">' +
    [0.25, 0.5, 0.75].map(function (f) {
      var y = T + (H - T - B) * f;
      return '<line class="vz-grid" x1="' + L + '" x2="' + (W - R) + '" y1="' + y +
        '" y2="' + y + '"/>';
    }).join('') +
    (savedFrom != null
      ? '<rect class="vz-saved" x="' + savedFrom + '" y="' + T + '" width="' +
        (W - R - savedFrom) + '" height="' + (H - T - B) + '"/>' +
        '<text class="vz-lbl-k" x="' + (savedFrom + 8) + '" y="' + (T + 14) +
        '" style="fill:var(--emerald)">' + w.baths_avoidable +
        ' bath(s) avoidable</text>' +
        '<text class="vz-val" x="' + (savedFrom + 8) + '" y="' + (T + 31) +
        '" style="fill:var(--emerald)">' + num(w.water_avoidable_l, 0) +
        '<tspan class="vz-unit"> L</tspan></text>' : '') +
    '<line class="vz-limit" x1="' + L + '" x2="' + (W - R) + '" y1="' + yLim +
    '" y2="' + yLim + '"/>' +
    '<text class="vz-lbl" x="' + (L + 4) + '" y="' + (yLim - 5) +
    '" style="fill:var(--emerald)">conductivity release limit ' +
    num(lim.conductivity_release_ms_cm, 2) + ' mS/cm</text>' +
    trace('col', YL, 'col') + trace('cond', YC, 'cond') +
    byBath.map(function (b, i) {
      return (b.cond == null ? '' : '<circle class="vz-pt" cx="' + X(i) + '" cy="' +
        YC(b.cond) + '" r="3" style="stroke:var(--cyan)"/>') +
        (b.col == null ? '' : '<circle class="vz-pt" cx="' + X(i) + '" cy="' +
        YL(b.col) + '" r="3" style="stroke:var(--salt)"/>');
    }).join('') +
    (w.endpoint_bath != null
      ? '<line class="vz-marker" x1="' + X(w.endpoint_bath) + '" x2="' +
        X(w.endpoint_bath) + '" y1="' + T + '" y2="' + (H - B) + '"/>' +
        '<text class="vz-lbl-k" text-anchor="middle" x="' + X(w.endpoint_bath) +
        '" y="' + (H - B + 30) + '">endpoint</text>' : '') +
    '<line class="vz-axis" x1="' + L + '" x2="' + (W - R) + '" y1="' + (H - B) +
    '" y2="' + (H - B) + '"/>' +
    '<line class="vz-axis" x1="' + L + '" x2="' + L + '" y1="' + T + '" y2="' +
    (H - B) + '"/>' +
    byBath.map(function (b, i) {
      return '<text class="vz-tick" text-anchor="middle" x="' + X(i) + '" y="' +
        (H - B + 16) + '">' + (i + 1) + '</text>';
    }).join('') +
    '<text class="vz-tick" text-anchor="end" x="' + (L - 8) + '" y="' + (T + 8) +
    '">' + num(maxC, 1) + '</text>' +
    '<text class="vz-tick" text-anchor="end" x="' + (L - 8) + '" y="' + (H - B) +
    '">0</text>' +
    '<text class="vz-lbl" x="' + L + '" y="' + (H - 8) + '">wash-off bath</text>' +
    '<text class="vz-lbl" x="' + (W - R + 10) + '" y="' + (T + 10) +
    '" style="fill:var(--cyan)">conductivity</text>' +
    '<text class="vz-lbl" x="' + (W - R + 10) + '" y="' + (T + 26) +
    '" style="fill:var(--salt)">residual colour</text>' +
    '</svg></div>';
}

/* ==========================================================================
   SIGNATURE VISUAL 7 - DECISION TIMELINE
   ========================================================================== */
function timeline(events) {
  return '<div class="tl">' + events.map(function (e) {
    return '<div class="tl-e ' + (e.cls || '') + '">' +
      '<div class="tl-t">' + esc(e.t) + '</div>' +
      '<div class="tl-n">' + esc(e.n) + '</div>' +
      (e.d ? '<div class="tl-d">' + esc(e.d) + '</div>' : '') + '</div>';
  }).join('') + '</div>';
}

/* ==========================================================================
   VIEW 1 - COMMAND
   What is happening / what will happen / what should I do / what changes
   ========================================================================== */
/* =====================================================================
   The plain-language band.

   The engine's finding is thermodynamically subtle, and that is a
   liability before it is an asset: a reviewer with forty submissions and
   ten minutes each does not reward rigour they cannot parse. So the top
   of the interface states the finding in one jargon-free sentence, backs
   it with three numbers the engine computed rather than three numbers we
   typed, and puts the full reasoning one click away instead of in the
   reader's face.

   Everything here reads from /api/narrative. Nothing is hardcoded.
   ===================================================================== */
function plainBand() {
  var n = S.narrative;
  if (!n) return '';

  var pf = null, vl = null, i;
  for (i = 0; i < n.ladder.length; i++) {
    if (n.ladder[i].id === 'proof') pf = n.ladder[i].detail;
    if (n.ladder[i].id === 'validation') vl = n.ladder[i].detail;
  }
  var ep = n.evidence_posture || null;

  function fact(k, v, t, tone) {
    return '<div class="pb-fact' + (tone ? ' pb-' + tone : '') + '">' +
      '<div class="pb-fact-k">' + esc(k) + '</div>' +
      '<div class="pb-fact-v mono">' + v + '</div>' +
      '<div class="pb-fact-t">' + esc(t) + '</div></div>';
  }

  var facts = '';
  if (pf) {
    facts += fact('Cut water 20%',
      (pf.cut_water_20pct_change_pct > 0 ? '+' : '') +
        pf.cut_water_20pct_change_pct.toFixed(1) + '%',
      'change in evaporator energy', 'flat');
    facts += fact('Cut salt 20%',
      pf.cut_salt_20pct_change_pct.toFixed(1) + '%',
      'change in evaporator energy', 'move');
  }
  if (vl && vl.points && vl.points.length) {
    var last = vl.points[vl.points.length - 1];
    facts += fact('Model vs published',
      last.predicted_reject_frac_pct.toFixed(1) + '%',
      'predicted at CPCB\u2019s measured inlet; published band 20\u201330%',
      'val');
  }
  if (ep) {
    facts += fact('Coefficients sourced',
      (ep.summary.PUBLISHED || 0) + '+' + (ep.summary.DERIVED || 0) +
        '/' + ep.total,
      'published or derived; 0 measured, and we say so', 'ev');
  }

  return '<div class="sec"><div class="pb">' +
    '<div class="pb-main">' +
      '<div class="pb-eyebrow">The finding, in one sentence</div>' +
      '<p class="pb-hook">' + esc(n.hook) + '</p>' +
      '<p class="pb-sub">' + esc(n.ladder[1].body) + '</p>' +
      '<div class="pb-acts">' +
        '<button class="btn btn-sm" data-why="reasoning">' +
          'Read the reasoning</button>' +
        '<button class="btn btn-sm btn-q" data-why="validation">' +
          'How we checked it</button>' +
        '<span class="pb-eq mono">' + esc(n.ladder[4].equation) + '</span>' +
      '</div>' +
    '</div>' +
    '<div class="pb-facts">' + facts + '</div>' +
  '</div></div>';
}

function vCommand() {
  var st = S.state, i = st.impact, fc = S.forecast;
  var o = st.optimisation;
  var sc = i.achieved_scenario;
  var decided = st.sequencing_status !== 'PENDING';
  var released = st.washoff_status === 'RELEASED';
  var live = decided || released;

  /* --- the single operational sentence ----------------------------- */
  var env = fc ? fc.plan.envelope : null;
  var sCls = 'info', sVal = 'READY', sTxt =
    'Run the optimiser to generate a plan for the committed queue.';
  if (env && env.risk === 'BREACH_PROJECTED') {
    sCls = 'fault'; sVal = 'BREACH PROJECTED';
    sTxt = env.risk_text + ' Peak draw ' + num(env.peak_hourly_draw_l, 0) +
      ' L at ' + env.peak_hour + '.';
  } else if (env && (env.risk === 'AT_RISK' || env.risk === 'TIGHT')) {
    sCls = 'warn'; sVal = env.risk.replace('_', ' ');
    sTxt = env.risk_text;
  } else if (env) {
    sCls = 'ok'; sVal = 'WITHIN ALLOWANCE'; sTxt = env.risk_text;
  }

  var rec = o && o.status === 'FEASIBLE'
    ? o.options.filter(function (x) { return x.option_id === o.recommended_option_id; })[0]
    : null;

  return phead('Command', 'Current resource state',
    'Freshwater draw in a closed-loop plant equals what the evaporator ' +
    'destroyed, and that is set by <strong>salt</strong> — not by water volume.',
    (o ? '<button class="btn btn-pri" data-go="decisions">Open decision</button>'
       : '<button class="btn btn-pri" data-act="optimise">Run optimiser</button>') +
    '<button class="btn" data-go="forecast">Forecast</button>'
  ) +

  plainBand() +

  /* ---------------- status ---------------- */
  '<div class="sec"><div class="status ' + sCls + '">' +
    '<span class="status-k">Resource state</span>' +
    '<span class="status-v">' + esc(sVal) + '</span>' +
    '<span class="status-t">' + esc(sTxt) + '</span>' +
    (env ? '<button class="why" data-why="envelope">Why</button>' : '') +
  '</div></div>' +

  /* ---------------- the hero: current draw + flow field ---------------- */
  '<div class="sec">' + srule('Resource flow',
    (live ? 'live &mdash; plan committed' : 'static &mdash; no decision taken') +
    ' &nbsp;' + ev('MODELLED')) +
    '<div class="grid g-8-4">' +
      '<div>' + flowField(sc, live) + '</div>' +
      '<div class="stack">' +
        readout({ label: 'Freshwater intake', k: 'fw_abs',
          value: sc.water.freshwater_intake_l, unit: 'L', size: 'xl',
          tone: 'water', dp: 0,
          foot: 'this shift, from the ' + esc(st.basin.basin_name) }) +
        readout({ label: 'Stress weighted', k: 'leq',
          value: sc.stress_equivalent_l_eq, unit: 'L-eq', size: 'sm', dp: 0,
          foot: '&times;' + num(st.basin.stress_weight, 2) + ' basin weight &nbsp;' +
            ev('ASSUMED') }) +
        readout({ label: 'Salt load', k: 'salt_abs', tone: 'salt',
          value: sc.salt.total_salt_kg, unit: 'kg', size: 'sm', dp: 0,
          foot: 'sets the evaporator duty' }) +
        '<div>' + disc('What binds here',
          '<dl class="defs">' +
          row('Binding constraint', '<b>' +
            esc(sc.zld.binding_constraint.replace('_', ' ').toLowerCase()) + '</b>') +
          row('Effluent TDS', '<span class="n">' + num(sc.zld.effluent_tds_mg_l, 0) +
            '</span> mg/L') +
          row('Reject TDS', '<span class="n">' + num(sc.zld.reject_tds_mg_l, 0) +
            '</span> mg/L ceiling') +
          '</dl><p style="margin-top:9px">' +
          (sc.zld.binding_constraint === 'SALT_BALANCE'
            ? 'Salt-limited: reducing salt reduces evaporator duty proportionally. Reducing water alone would not.'
            : 'Hydraulically limited: the membrane array, not the salt balance, sets reject volume here.') +
          '</p>') + '</div>' +
      '</div>' +
    '</div>' +
  '</div>' +

  /* ---------------- baseline -> changeloop ---------------- */
  '<div class="sec">' + srule('Baseline to ChangeLoop',
    'attributed to the decisions actually taken') +
    '<div class="strip">' +
      readout({ label: 'Freshwater avoided', k: 'fw', tone: 'water',
        value: i.freshwater_avoided_l, unit: 'L', dp: 0,
        foot: down(i.freshwater_avoided_l, 'L', 0) + ' &middot; ' +
          pct(i.baseline_freshwater_intake_l > 0
            ? i.freshwater_avoided_l / i.baseline_freshwater_intake_l * 100 : 0) }) +
      readout({ label: 'Salt avoided', k: 'slt', tone: 'salt',
        value: i.salt_avoided_kg, unit: 'kg', dp: 0,
        foot: 'drives the evaporator saving' }) +
      readout({ label: 'Evaporator steam', k: 'mee', tone: 'energy',
        value: i.mee_thermal_avoided_kwh, unit: 'kWh', dp: 0,
        foot: 'thermal, avoided' }) +
      readout({ label: 'CO₂e avoided', k: 'co2', tone: 'carbon',
        value: i.co2e_avoided_kg, unit: 'kg', dp: 0,
        foot: pct(i.baseline_co2e_kg > 0
          ? i.co2e_avoided_kg / i.baseline_co2e_kg * 100 : 0) + ' of baseline' }) +
      readout({ label: 'Cost avoided', k: 'cost', tone: 'good',
        raw: inr(i.cost_avoided_inr), value: i.cost_avoided_inr,
        foot: 'per shift' }) +
    '</div>' +
    (!decided && !released
      ? '<p class="small muted" style="margin-top:10px">Zero until a ' +
        'decision is approved. These are the figures for the decisions ' +
        'actually taken.</p>' : '') +
  '</div>' +

  /* ---------------- recommendation + proof ---------------- */
  '<div class="sec"><div class="grid g-7-5">' +
    '<div>' + srule('Recommended decision', o ? esc(o.optimality.replace(/_/g, ' ').toLowerCase()) : '') +
      (rec
        ? '<div class="stack">' +
          '<div><div class="readout-k">' + esc(rec.option_id.replace('_', ' ')) +
          '</div><div style="font-size:var(--t-h3);font-weight:600;margin-top:4px">' +
          esc(rec.title) + '</div></div>' +
          '<div class="seq">' + seqChips(rec.order) + '</div>' +
          '<dl class="defs">' +
          row('Process strategy', esc(rec.strategy.name)) +
          row('Freshwater', '<span class="n">' + num(rec.freshwater_intake_l, 0) +
            '</span> L &nbsp;' + down(rec.delta_vs_baseline.freshwater_l, 'L', 0)) +
          row('Evaporator steam', '<span class="n">' + num(rec.mee_thermal_kwh, 0) +
            '</span> kWh &nbsp;' + down(rec.delta_vs_baseline.mee_thermal_kwh, '', 0)) +
          row('Schedule', num(rec.total_late_h, 2) + ' h lateness, ' +
            rec.firm_date_breaches + ' firm breach' +
            (rec.firm_date_breaches === 1 ? '' : 'es')) +
          '</dl>' +
          '<div class="row">' +
            (decided
              ? '<span class="status ' + (st.sequencing_status === 'APPROVED' ? 'ok' : 'warn') +
                '" style="flex:1"><span class="status-k">Decision</span>' +
                '<span class="status-v">' + esc(st.sequencing_status) + '</span>' +
                '<span class="status-t">recorded against ' +
                esc(st.sequencing_actor || 'unknown') + '</span></span>'
              : '<button class="btn btn-ok" data-act="approve">Accept</button>' +
                '<button class="btn btn-no" data-act="reject">Reject</button>' +
                '<button class="why" data-why="recommendation">Why this recommendation</button>') +
          '</div></div>'
        : '<div class="empty"><div class="empty-k">No plan generated</div>' +
          '<h3>The optimiser has not run</h3>' +
          '<p>It enumerates every lot order against every process strategy and ' +
          'discards any plan that breaches a hard constraint.</p>' +
          '<button class="btn btn-pri" data-act="optimise">Run optimiser</button></div>') +
    '</div>' +
    '<div>' + srule('Salt is water', 'live from mass conservation &nbsp;' + ev('DERIVED')) +
      (S.insight
        ? '<div class="stack">' +
          '<div class="formula">V_reject = M_salt / C_reject_max</div>' +
          '<div class="flows">' +
            flowBand('Cut water 20%, salt unchanged',
              S.insight.cut_water_20pct_only.mee_energy_change_pct, '%', 0,
              'loss', 'evaporator energy does not move') +
            flowBand('Cut salt 20%, water unchanged',
              S.insight.cut_salt_20pct_only.mee_energy_change_pct, '%', 1,
              'salt', 'evaporator energy falls proportionally') +
          '</div>' +
          '<button class="why" data-why="salt">Why this holds, and where it stops</button>' +
          '</div>'
        : '<div class="load"><div class="load-k">Computing proof</div>' +
          '<div class="load-bar"><i></i></div></div>') +
    '</div>' +
  '</div></div>';
}

function seqChips(order) {
  var lots = S.state.lots, arrival = S.state.arrival_order;
  return order.map(function (id, i) {
    var lot = null;
    for (var j = 0; j < lots.length; j++) if (lots[j].lot_id === id) lot = lots[j];
    lot = lot || {};
    var moved = arrival[i] !== id;
    return (i ? '<span class="seq-a">' + ico('arrow', 11) + '</span>' : '') +
      '<span class="chip' + (moved ? ' moved' : '') + '" title="' +
      esc(lot.shade_name + ', ' + lot.depth_owf + '% owf') + '">' +
      '<span class="sw" style="background:' + esc(lot.shade_hex || '#999') +
      '"></span>' + esc(id) + '</span>';
  }).join('');
}

/* ==========================================================================
   VIEW 2 - FORECAST
   ========================================================================== */
function vForecast() {
  var fc = S.forecast;
  if (!fc) {
    return phead('Forecast', 'Resource forecast') +
      '<div class="sec"><div class="load">' +
      '<div class="load-k">Projecting the committed queue</div>' +
      '<div class="load-d">24 hour horizon<br>abstraction envelope<br>uncertainty band</div>' +
      '<div class="load-bar"><i></i></div></div></div>';
  }
  var p = fc.plan, b = fc.baseline, e = p.envelope, d = fc.delta;

  var risk = e.risk;
  var rCls = risk === 'BREACH_PROJECTED' ? 'fault'
    : (risk === 'AT_RISK' || risk === 'TIGHT') ? 'warn' : 'ok';

  return phead('Forecast', 'Resource forecast and abstraction envelope',
    'Not a statistical forecast. The order book is committed, so this ' +
    'trajectory is the <strong>shadow of a decision not yet taken</strong> — ' +
    'approve a different plan and the curve moves.',
    '<button class="why" data-why="forecast-method">Method</button>'
  ) +

  '<div class="sec"><div class="status ' + rCls + '">' +
    '<span class="status-k">Envelope</span>' +
    '<span class="status-v">' + esc(risk.replace(/_/g, ' ')) + '</span>' +
    '<span class="status-t">' + esc(e.risk_text) + '</span>' +
  '</div></div>' +

  '<div class="sec">' + srule('Cumulative draw against allocation',
    esc(p.strategy_name) + ' &nbsp;' + ev('MODELLED')) +
    forecastChart(fc) +
  '</div>' +

  '<div class="sec"><div class="strip">' +
    readout({ label: 'Projected draw', k: 'f_draw', tone: 'water',
      value: e.projected_draw_l, unit: 'L', dp: 0,
      foot: pct(e.utilisation_pct) + ' of allocation' }) +
    readout({ label: 'Allocation', value: e.allocation_l, unit: 'L', dp: 0,
      foot: 'per machine-shift &nbsp;' + ev('ASSUMED') }) +
    readout({ label: 'Headroom', k: 'f_head',
      tone: e.headroom_l < 0 ? 'fault' : 'good',
      value: e.headroom_l, unit: 'L', dp: 0,
      foot: e.headroom_l < 0 ? 'over the allocation' : 'remaining' }) +
    readout({ label: 'Peak hourly draw', value: e.peak_hourly_draw_l, unit: 'L',
      dp: 0, foot: 'at ' + esc(e.peak_hour || '—') }) +
    readout({ label: 'Breach', raw: e.breach_clock || 'none',
      value: e.breach_clock || 'none',
      tone: e.breach_clock ? 'fault' : 'good',
      size: 'sm', foot: e.breach_clock ? 'central projection crosses' : 'inside the envelope' }) +
  '</div></div>' +

  '<div class="sec"><div class="grid g-7-5">' +
    '<div>' + srule('Hour by hour') +
      '<div class="tw"><table class="t"><thead><tr>' +
      '<th>Hour</th><th>Lot</th><th>Activity</th>' +
      '<th class="n">Water</th><th class="n">Salt</th>' +
      '<th class="n">Fresh draw</th><th class="n">Cumulative</th>' +
      '<th class="n">Ambient</th></tr></thead><tbody>' +
      p.steps.filter(function (s) { return s.freshwater_l > 0; }).map(function (s) {
        var over = s.cumulative_freshwater_l > e.allocation_l;
        return '<tr' + (over ? ' class="muted"' : '') + '>' +
          '<td class="t-k mono">' + esc(s.clock) + '</td>' +
          '<td class="mono">' + esc(s.lot_id || '—') + '</td>' +
          '<td>' + esc(s.activity.toLowerCase()) + '</td>' +
          '<td class="n">' + num(s.water_l, 0) + '</td>' +
          '<td class="n">' + num(s.salt_kg, 1) + '</td>' +
          '<td class="n">' + num(s.freshwater_l, 0) + '</td>' +
          '<td class="n"' + (over ? ' style="color:var(--coral)"' : '') + '>' +
          num(s.cumulative_freshwater_l, 0) + '</td>' +
          '<td class="n">' + num(s.ambient_c, 1) + '</td></tr>';
      }).join('') + '</tbody></table></div>' +
    '</div>' +
    '<div>' + srule('Drivers') +
      '<div class="stack-s">' + p.drivers.map(function (dr) {
        return '<div style="padding:9px 0;border-bottom:1px solid var(--hair)">' +
          '<div class="row" style="justify-content:space-between">' +
          '<span class="t-k">' + esc(dr.name) + '</span>' +
          '<span class="mono small">' + esc(dr.value) + '</span></div>' +
          '<div class="micro muted" style="margin-top:3px;line-height:1.45">' +
          esc(dr.detail) + ' ' + ev(dr.evidence) + '</div></div>';
      }).join('') + '</div>' +
      '<div style="margin-top:var(--s4)">' +
      srule('Decision consequence') +
      '<dl class="defs">' +
        row('Draw reduced', down(d.projected_draw_l, 'L', 0)) +
        row('Headroom gained', '<span class="n">' + num(d.headroom_gained_l, 0) + '</span> L') +
        row('Baseline risk', esc(d.baseline_risk.replace(/_/g, ' '))) +
        row('Plan risk', esc(d.plan_risk.replace(/_/g, ' '))) +
      '</dl>' +
      (d.plan_risk === 'BREACH_PROJECTED'
        ? '<div class="status warn" style="margin-top:var(--s3)">' +
          '<span class="status-k">Note</span>' +
          '<span class="status-t">The recommended plan still breaches. ' +
          'Under this binding constraint the water lever alone is not ' +
          'enough — change the constraint to Drought or Carbon priority ' +
          'and the optimiser will buy the salt lever.</span></div>' : '') +
      '</div>' +
    '</div>' +
  '</div></div>';
}

/* ==========================================================================
   VIEW 3 - DECISIONS
   ========================================================================== */
function vDecisions() {
  var st = S.state, o = st.optimisation;
  if (!o) {
    return phead('Decisions', 'Decision workbench') +
      '<div class="sec"><div class="empty">' +
      '<div class="empty-k">No active plan</div>' +
      '<h3>The optimiser has not run</h3>' +
      '<p>It enumerates every lot order against every process strategy, ' +
      'scores each on the full downstream consequence, and discards any that ' +
      'breaches a hard constraint.</p>' +
      '<button class="btn btn-pri" data-act="optimise">Run optimiser</button>' +
      '</div></div>';
  }
  if (o.status !== 'FEASIBLE') {
    return phead('Decisions', 'No feasible plan') +
      '<div class="sec"><div class="status fault">' +
      '<span class="status-k">Status</span><span class="status-v">' +
      esc(o.status.replace(/_/g, ' ')) + '</span>' +
      '<span class="status-t">' + esc(o.reason || '') + '</span></div></div>';
  }

  var rec = o.options.filter(function (x) { return x.is_recommended; })[0];
  var base = o.options.filter(function (x) { return x.option_id === 'OPTION_A'; })[0];
  var decided = st.sequencing_status !== 'PENDING';

  var rows = [
    ['Lot order', function (x) { return '<div class="seq">' + seqChips(x.order) + '</div>'; }, false],
    ['Process strategy', function (x) { return esc(x.strategy.name); }, false],
    ['Freshwater intake', function (x) { return num(x.freshwater_intake_l, 0) + ' <span class="u">L</span>'; }, true],
    ['Stress weighted', function (x) { return num(x.stress_equivalent_l_eq, 0) + ' <span class="u">L-eq</span>'; }, true],
    ['Total salt load', function (x) { return num(x.total_salt_kg, 1) + ' <span class="u">kg</span>'; }, true],
    ['RO reject', function (x) { return num(x.ro_reject_l, 0) + ' <span class="u">L</span>'; }, true],
    ['Evaporator steam', function (x) { return num(x.mee_thermal_kwh, 0) + ' <span class="u">kWh</span>'; }, true],
    ['CO₂e', function (x) { return num(x.co2e_kg, 0) + ' <span class="u">kg</span>'; }, true],
    ['Total cost', function (x) { return inr(x.cost_inr); }, true],
    ['Schedule lateness', function (x) { return num(x.total_late_h, 2) + ' <span class="u">h</span>'; }, true],
    ['Firm date breaches', function (x) {
      return x.firm_date_breaches > 0
        ? '<span style="color:var(--coral)">' + x.firm_date_breaches + '</span>'
        : '0';
    }, true],
    ['Feasible', function (x) {
      return x.feasible
        ? '<span style="color:var(--emerald)">yes</span>'
        : '<span style="color:var(--coral)">no</span>';
    }, false]
  ];

  return phead('Decisions', 'Decision workbench',
    'Current state, then every feasible alternative, then the consequence of ' +
    'each, then one recommendation. <strong>Option C saves the most ' +
    'freshwater and is refused</strong>, because it breaches a firm ship date.',
    '<button class="why" data-why="weights">Objective weights</button>'
  ) +

  /* --- the canvas: alternatives as aligned columns, not card stacks --- */
  '<div class="sec">' + srule('Feasible alternatives',
    esc(o.method) + ' &nbsp;' + ev('MODELLED')) +
    '<div class="tw"><table class="t"><thead><tr><th></th>' +
    o.options.map(function (x) {
      return '<th class="n" style="min-width:150px">' +
        '<div style="color:' + (x.is_recommended ? 'var(--water)' :
          !x.feasible ? 'var(--coral)' : 'var(--slate-3)') + '">' +
        esc(x.option_id.replace('_', ' ')) + '</div>' +
        '<div style="font-family:var(--sans);font-size:var(--t-small);' +
        'font-weight:600;color:var(--graphite);text-transform:none;' +
        'letter-spacing:0;margin-top:3px;white-space:normal">' +
        esc(x.title.split(' - ')[0]) + '</div>' +
        (x.is_recommended ? '<div style="color:var(--water);margin-top:3px">recommended</div>'
          : !x.feasible ? '<div style="color:var(--coral);margin-top:3px">refused</div>'
          : '<div style="margin-top:3px">baseline</div>') +
        '</th>';
    }).join('') + '</tr></thead><tbody>' +
    rows.map(function (r) {
      return '<tr' + (r[0] === 'Freshwater intake' || r[0] === 'Evaporator steam'
        ? ' class="rec"' : '') + '>' +
        '<td class="t-k">' + r[0] + '</td>' +
        o.options.map(function (x) {
          return '<td class="' + (r[2] ? 'n' : '') + '">' + r[1](x) + '</td>';
        }).join('') + '</tr>';
    }).join('') + '</tbody></table></div>' +
    (o.options.filter(function (x) { return !x.feasible; }).map(function (x) {
      return '<div class="status fault" style="margin-top:var(--s3)">' +
        '<span class="status-k">' + esc(x.option_id.replace('_', ' ')) + '</span>' +
        '<span class="status-v">Refused</span>' +
        '<span class="status-t">' + x.violations.map(esc).join(' ') + '</span></div>';
    }).join('')) +
  '</div>' +

  /* --- the process river --- */
  '<div class="sec">' + srule('What changed in the sequence',
    'channel width is the changeover water burden') +
    processRiver(base.order, rec.order,
      findTransitions(rec.order), findTransitions(base.order)) +
  '</div>' +

  /* --- the recommendation, as an engineering recommendation --- */
  '<div class="sec"><div class="grid g-7-5">' +
    '<div>' + srule('Recommendation') +
      '<div class="stack">' +
        '<div><div class="readout-k">' + esc(rec.option_id.replace('_', ' ')) +
        '</div><div style="font-size:var(--t-h2);font-weight:600;' +
        'letter-spacing:-0.02em;margin-top:5px">' + esc(rec.title) + '</div>' +
        '<p class="small muted" style="margin-top:6px">' + esc(rec.description) +
        '</p></div>' +
        '<div><div class="readout-k" style="margin-bottom:7px">Why</div>' +
        o.rationale.why.map(function (w, n) {
          return '<div style="display:grid;grid-template-columns:24px 1fr;' +
            'gap:10px;padding:7px 0;border-bottom:1px solid var(--hair)">' +
            '<span class="mono micro muted">' + (n < 9 ? '0' : '') + (n + 1) +
            '</span><span class="small">' + esc(w) + '</span></div>';
        }).join('') + '</div>' +
        '<div><div class="readout-k" style="margin-bottom:7px">Expected change</div>' +
        '<dl class="defs">' +
          row('Water', down(rec.delta_vs_baseline.freshwater_l, 'L', 0)) +
          row('Salt', down(rec.delta_vs_baseline.salt_kg, 'kg', 1)) +
          row('Energy', down(rec.delta_vs_baseline.mee_thermal_kwh, 'kWh', 0)) +
          row('Carbon', down(rec.delta_vs_baseline.co2e_kg, 'kg', 0)) +
          row('Cost', down(rec.delta_vs_baseline.cost_inr, '₹', 0)) +
          row('Schedule', num(rec.delta_vs_baseline.lateness_h, 2) + ' h change') +
        '</dl></div>' +
        (decided
          ? '<div class="status ' + (st.sequencing_status === 'APPROVED' ? 'ok' : 'warn') + '">' +
            '<span class="status-k">Decision</span><span class="status-v">' +
            esc(st.sequencing_status) + '</span><span class="status-t">Recorded ' +
            'against ' + esc(st.sequencing_actor || 'unknown') + ' in the ' +
            'tamper-evident ledger. ' +
            (st.sequencing_status === 'APPROVED'
              ? 'The plan is the executed order and strategy.'
              : 'Arrival order retained; nothing credited.') + '</span></div>' +
            '<div class="row"><button class="btn btn-pri" data-go="water">' +
            'Continue to the wash-off gate</button></div>'
          : '<div class="row">' +
            '<button class="btn btn-ok" data-act="approve">Accept</button>' +
            '<button class="btn btn-no" data-act="reject">Reject</button>' +
            '<button class="why" data-why="recommendation">Full rationale</button>' +
            '</div>') +
      '</div>' +
    '</div>' +
    '<div>' + srule('Order book', ev('SIMULATED')) +
      '<div class="tw"><table class="t"><thead><tr><th>Lot</th><th>Shade</th>' +
      '<th class="n">Depth</th><th class="n">Salt</th><th class="n">Due</th>' +
      '</tr></thead><tbody>' + st.lots.map(function (l) {
        return '<tr><td><span class="t-k mono">' + esc(l.lot_id) + '</span>' +
          '<div class="t-s">' + esc(l.buyer_ref) + '</div></td>' +
          '<td><span class="chip"><span class="sw" style="background:' +
          esc(l.shade_hex) + '"></span>' + esc(l.shade_name) + '</span></td>' +
          '<td class="n">' + num(l.depth_owf, 2) + '</td>' +
          '<td class="n">' + num(l.salt_dose_g_per_l, 0) + '</td>' +
          '<td class="n">' + num(l.due_h, 1) + ' h' +
          (l.priority === 1 ? '<div class="t-s" style="color:var(--coral)">firm</div>' : '') +
          '</td></tr>';
      }).join('') + '</tbody></table></div>' +
      '<div style="margin-top:var(--s4)">' +
      disc('What we do not claim as novel', '<p>' + esc(o.not_claimed) + '</p>') +
      disc('Uncertainty', '<p>' + esc(o.rationale.uncertainty) + '</p>' +
        '<ul style="margin:8px 0 0;padding-left:18px">' +
        o.rationale.what_would_change_this.map(function (x) {
          return '<li style="margin-bottom:5px">' + esc(x) + '</li>';
        }).join('') + '</ul>') +
      '</div>' +
    '</div>' +
  '</div></div>';
}

function findTransitions(order) {
  var o = S.state.optimisation;
  if (!o || !o.options) return [];
  for (var i = 0; i < o.options.length; i++) {
    var x = o.options[i];
    if (x.order.join() === order.join() && x.sequence_transitions) {
      return x.sequence_transitions;
    }
  }
  /* the optimiser payload does not carry transitions per option, so derive
     the burdens from the computed matrix the server already exposes */
  if (!S.matrix) return [];
  var out = [];
  for (var k = 0; k < order.length - 1; k++) {
    var row = S.matrix[order[k]];
    var t = row && row[order[k + 1]];
    if (t) out.push(t);
  }
  return out;
}

/* ==========================================================================
   VIEW 4 - WATER
   ========================================================================== */
function vWater() {
  var st = S.state, i = st.impact, sc = i.achieved_scenario;
  var w = st.washoff;
  var faults = [
    ['none', 'No fault'], ['sensor_dropout', 'Probe dropout'],
    ['sensor_frozen', 'Probe frozen'], ['sensor_drift', 'Calibration drift'],
    ['colour_spike', 'Residual dye slug'], ['thermal_deficit', 'Bath under temperature']
  ];

  var gate = w ? w.gate : null;
  var gCls = !gate ? 'info'
    : gate.state === 'LOCKED_OUT' ? 'fault'
    : gate.state === 'AWAITING_HUMAN_RELEASE' ? 'warn' : 'info';

  return phead('Water', 'Circularity, balance and release',
    'Where the water came from, what quality it has, where it goes, and ' +
    'whether it can be reused. Select a stream to trace its route.',
    '<button class="why" data-why="balance">Accounting rules</button>'
  ) +

  /* ---- the network ---- */
  '<div class="sec">' + srule('Water circularity network',
    (S.selectedStream ? 'tracing ' + esc(S.selectedStream) +
      ' &middot; <button class="why" data-stream="">clear</button>'
      : 'click a stream to trace it') + ' &nbsp;' + ev('MODELLED')) +
    waterNetwork(sc, S.selectedStream) +
    '<div class="row" style="margin-top:var(--s3)">' +
    ['fresh', 'effluent', 'permeate', 'reuse', 'reject', 'loss'].map(function (s) {
      return '<button class="btn btn-sm' +
        (S.selectedStream === s ? ' btn-pri' : '') + '" data-stream="' + s +
        '">' + esc(s) + '</button>';
    }).join('') + '</div>' +
  '</div>' +

  /* ---- mass balance + quality ---- */
  '<div class="sec"><div class="grid g-7-5">' +
    '<div>' + srule('Mass balance', 'engineering accounting') +
      massBalance(sc) + '</div>' +
    '<div>' + srule('Water quality and suitability',
      ev('SIMULATED')) + qualityBars(sc, w) + '</div>' +
  '</div></div>' +

  /* ---- the release gate ---- */
  '<div class="sec">' + srule('Wash-off release gate',
    'fail-closed, never automatic') +
    '<div class="status ' + gCls + '">' +
      '<span class="status-k">Gate</span>' +
      '<span class="status-v">' + esc(gate ? gate.state.replace(/_/g, ' ') : 'NOT RUN') +
      '</span><span class="status-t">' +
      esc(gate ? gate.message : 'Run the wash-off telemetry for the deepest ' +
        'shade in the queue, where the fixed-time schedule has the most slack.') +
      '</span>' +
      (gate ? '<button class="why" data-why="gate">Why fail-closed</button>' : '') +
    '</div>' +

    (w
      ? '<div class="grid g-8-4" style="margin-top:var(--s4)">' +
        '<div>' + telemetry(w) + '</div>' +
        '<div class="stack">' +
          '<div class="checks">' + [
            ['conductivity_asymptote', 'Conductivity at release limit'],
            ['residual_colour_within_limit', 'Residual colour within limit'],
            ['fixation_temperature_held', 'Fixation temperature held'],
            ['dual_probe_agreement', 'Dual probes agree'],
            ['data_completeness', 'Telemetry complete']
          ].map(function (c) {
            return check(gate.checks[c[0]], c[1]);
          }).join('') + '</div>' +
          '<div class="strip" style="grid-template-columns:1fr 1fr">' +
            readout({ label: 'Baths avoidable', value: w.baths_avoidable,
              dp: 0, size: 'sm', foot: 'of ' + w.scheduled_baths + ' scheduled' }) +
            readout({ label: 'Water', value: w.water_avoidable_l, unit: 'L',
              dp: 0, size: 'sm', tone: 'water',
              foot: 'integrated from flow' }) +
          '</div>' +
          (gate.state === 'AWAITING_HUMAN_RELEASE'
            ? '<div class="row"><button class="btn btn-ok" data-act="release">' +
              'Grant release</button><button class="btn" data-act="norelease">' +
              'Decline</button></div>'
            : gate.state === 'LOCKED_OUT'
              ? '<div class="status fault"><span class="status-k">Lockout</span>' +
                '<span class="status-t">' + esc(gate.lockout_reason) +
                ' Attempt it — the request is refused at the gate and at ' +
                'the API, and the refusal is recorded.</span></div>' +
                '<div class="row"><button class="btn btn-no" data-act="release">' +
                'Attempt release</button></div>'
              : '<p class="small muted">No endpoint reached before the ' +
                'scheduled baths completed. Short schedules on pale shades ' +
                'have no slack, and the system reports zero rather than ' +
                'manufacturing a saving.</p>') +
          (st.washoff_status === 'RELEASED'
            ? '<div class="status ok"><span class="status-k">Released</span>' +
              '<span class="status-t">Granted by ' + esc(st.washoff_actor) +
              ' and recorded.</span></div>' : '') +
        '</div></div>'
      : '') +

    '<div style="margin-top:var(--s4)"><div class="readout-k" ' +
    'style="margin-bottom:8px">Inject a fault — each must force lockout</div>' +
    '<div class="row">' + faults.map(function (f) {
      return '<button class="btn btn-sm' +
        ((st.fault_mode || 'none') === f[0] ? ' btn-pri' : '') +
        '" data-fault="' + f[0] + '">' + esc(f[1]) + '</button>';
    }).join('') + '</div></div>' +
  '</div>';
}

function qualityBars(sc, w) {
  var lim = S.state.release_limits;
  var z = sc.zld;
  var items = [
    { k: 'Effluent TDS', v: z.effluent_tds_mg_l, u: 'mg/L', max: 12000,
      okTo: 8000, f: 'feed to the RO train' },
    { k: 'Reject TDS', v: z.reject_tds_mg_l, u: 'mg/L', max: 70000,
      okTo: 60000, f: 'ceiling set by scaling' },
    { k: 'RO recovery', v: z.ro_recovery_frac * 100, u: '%', max: 100,
      okTo: 90, f: 'hydraulic ceiling 90%' }
  ];
  if (w) {
    var last = null, lastCol = null;
    w.samples.forEach(function (s) {
      if (s.conductivity_ms_cm != null) last = s.conductivity_ms_cm;
      if (s.residual_colour_admi != null) lastCol = s.residual_colour_admi;
    });
    items.push({ k: 'Final conductivity', v: last, u: 'mS/cm', max: 3,
      okTo: lim.conductivity_release_ms_cm, f: 'release limit ' +
      num(lim.conductivity_release_ms_cm, 2), limit: true });
    items.push({ k: 'Residual colour', v: lastCol, u: 'ADMI', max: 60,
      okTo: lim.colour_release_admi, f: 'release limit ' +
      num(lim.colour_release_admi, 0), limit: true });
  }

  var suit = w && w.gate.checks.all_pass ? 'REUSE'
    : w && w.gate.state === 'LOCKED_OUT' ? 'HOLD' : 'TREAT';
  var suitCls = suit === 'REUSE' ? 'ok' : suit === 'HOLD' ? 'fault' : 'warn';

  return '<div class="stack">' + items.map(function (it) {
    if (it.v == null) return '';
    var p = Math.max(0, Math.min(100, it.v / it.max * 100));
    var okW = Math.max(0, Math.min(100, it.okTo / it.max * 100));
    var out = it.limit ? it.v > it.okTo : it.v > it.okTo;
    return '<div class="meas"><div class="meas-hd">' +
      '<span class="meas-k">' + esc(it.k) + '</span>' +
      '<span class="meas-v"' + (out ? ' style="color:var(--coral)"' : '') + '>' +
      num(it.v, it.v < 10 ? 2 : 0) + ' <span class="u">' + esc(it.u) +
      '</span></span></div>' +
      '<div class="meas-track">' +
      '<div class="meas-ok" style="left:0;width:' + okW.toFixed(1) + '%"></div>' +
      '<div class="meas-lim" style="left:' + okW.toFixed(1) + '%"></div>' +
      '<div class="meas-pt' + (out ? ' out' : '') + '" style="left:' +
      p.toFixed(1) + '%"></div></div>' +
      '<div class="meas-f">' + esc(it.f) + '</div></div>';
  }).join('') +
  '<div class="status ' + suitCls + '">' +
    '<span class="status-k">Suitability</span>' +
    '<span class="status-v">' + suit + '</span>' +
    '<span class="status-t">' +
    (suit === 'REUSE' ? 'All clearance checks pass. Reuse may be released by a named human.'
      : suit === 'HOLD' ? 'Interlocked. Reuse cannot be authorised.'
      : 'Not yet evidenced for reuse. Treat or run the full cycle.') +
    '</span></div>' +
  '<p class="micro muted">Recovered is never the same as reusable. ' +
  'Suitability is a gate, not a consequence of recovery.</p>' +
  '</div>';
}

/* ==========================================================================
   VIEW 5 - IMPACT
   ========================================================================== */
function vImpact() {
  var i = S.state.impact;
  var lines = [
    ['Freshwater intake', 'L', i.baseline_freshwater_intake_l,
      i.achieved_freshwater_intake_l, i.freshwater_avoided_l,
      'freshwater_avoided_l', 'MODELLED'],
    ['Total salt load', 'kg', i.baseline_salt_kg, i.achieved_salt_kg,
      i.salt_avoided_kg, null, 'MODELLED'],
    ['RO reject volume', 'L', i.baseline_reject_l, i.achieved_reject_l,
      i.reject_avoided_l, null, 'DERIVED'],
    ['Evaporator steam', 'kWh', i.baseline_mee_thermal_kwh,
      i.achieved_mee_thermal_kwh, i.mee_thermal_avoided_kwh,
      'mee_thermal_avoided_kwh', 'DERIVED'],
    ['CO₂e', 'kg', i.baseline_co2e_kg, i.achieved_co2e_kg,
      i.co2e_avoided_kg, 'co2e_avoided_kg', 'DERIVED'],
    ['Total cost', '₹', i.baseline_cost_inr, i.achieved_cost_inr,
      i.cost_avoided_inr, 'cost_avoided_inr', 'ASSUMED']
  ];

  return phead('Impact', 'Impact ledger',
    'Baseline and achieved are computed by the same code path, so the delta ' +
    'is a real difference and not two models disagreeing. Any row opens its ' +
    'formula and coefficients.',
    '<button class="btn" data-act="export">Export</button>'
  ) +

  '<div class="sec">' + srule('Resource ledger', 'click a row for its derivation') +
    '<div class="tw"><table class="t"><thead><tr>' +
    '<th>Quantity</th><th class="n">Baseline</th><th class="n">ChangeLoop</th>' +
    '<th class="n">Delta</th><th class="n">%</th><th>Evidence</th><th></th>' +
    '</tr></thead><tbody>' +
    lines.map(function (r) {
      var p = r[2] > 0 ? (r[4] / r[2] * 100) : 0;
      return '<tr' + (r[5] ? ' class="clickable" data-trace="' + r[5] + '"' : '') + '>' +
        '<td class="t-k">' + r[0] + ' <span class="u">' + esc(r[1]) + '</span></td>' +
        '<td class="n">' + num(r[2], 0) + '</td>' +
        '<td class="n">' + num(r[3], 0) + '</td>' +
        '<td class="n">' + down(r[4], '', 0) + '</td>' +
        '<td class="n">' + pct(p) + '</td>' +
        '<td>' + ev(r[6]) + '</td>' +
        '<td class="n">' + (r[5] ? '<span class="why">Trace</span>' : '') + '</td>' +
        '</tr>';
    }).join('') +
    '<tr class="clickable" data-trace="stress_equivalent_avoided_l_eq">' +
      '<td class="t-k">Stress-weighted freshwater <span class="u">L-eq</span></td>' +
      '<td class="n">—</td><td class="n">—</td>' +
      '<td class="n">' + down(i.stress_equivalent_avoided_l_eq, '', 0) + '</td>' +
      '<td class="n">&times;' + num(i.stress_weight, 2) + '</td>' +
      '<td>' + ev('ASSUMED') + '</td>' +
      '<td class="n"><span class="why">Trace</span></td></tr>' +
    '</tbody></table></div>' +
  '</div>' +

  '<div class="sec"><div class="grid g-5-7">' +
    '<div>' + srule('Attribution', 'an unapproved decision credits zero') +
      '<div class="tw"><table class="t"><thead><tr><th>Decision</th>' +
      '<th>Status</th><th class="n">Water</th><th class="n">Salt</th>' +
      '</tr></thead><tbody>' +
      '<tr><td class="t-k">Sequence &amp; strategy<div class="t-s">' +
        'changeover burden and rinse strategy</div></td>' +
        '<td class="mono micro">' + esc(i.sequencing_status) + '</td>' +
        '<td class="n">' + num(i.sequencing_water_avoided_l, 0) + ' L</td>' +
        '<td class="n">' + num(i.sequencing_salt_avoided_kg, 1) + ' kg</td></tr>' +
      '<tr><td class="t-k">Wash-off release<div class="t-s">' +
        'released baths, integrated from flow</div></td>' +
        '<td class="mono micro">' + esc(i.washoff_status) + '</td>' +
        '<td class="n">' + num(i.washoff_water_avoided_l, 0) + ' L</td>' +
        '<td class="n">' + num(i.washoff_salt_avoided_kg, 1) + ' kg</td></tr>' +
      '</tbody></table></div>' +
      (i.notes && i.notes.length
        ? '<div style="margin-top:var(--s3)">' + disc('Accounting notes',
            '<ul style="margin:0;padding-left:18px">' + i.notes.map(function (n) {
              return '<li style="margin-bottom:5px">' + esc(n) + '</li>';
            }).join('') + '</ul>') + '</div>' : '') +
    '</div>' +
    '<div>' + srule('Accounting invariants',
      i.validation.all_pass ? 'all ' + i.validation.checks.length + ' pass'
        : i.validation.failed_count + ' failed') +
      '<div class="checks">' + i.validation.checks.map(function (c) {
        return check(c.pass, c.rule.replace(/_/g, ' '), c.detail);
      }).join('') + '</div>' +
      '<p class="micro muted" style="margin-top:9px">Run on every read. A ' +
      'failure means the figure is not fit to display.</p>' +
    '</div>' +
  '</div></div>';
}

/* ==========================================================================
   VIEW 6 - EVIDENCE
   ========================================================================== */
function vEvidence() {
  if (!S.evidence) {
    api('/api/evidence').then(function (d) { S.evidence = d; soft('evidence'); });
    return phead('Evidence', 'Coefficient registry') +
      '<div class="sec"><div class="load"><div class="load-k">' +
      'Loading registry</div><div class="load-bar"><i></i></div></div></div>';
  }
  var e = S.evidence, sum = e.summary;
  var order = ['MEASURED', 'PUBLISHED', 'DERIVED', 'ASSUMED', 'SIMULATED'];

  return phead('Evidence', 'Coefficient registry and claim register',
    'No number may be used in a calculation unless it is registered with a ' +
    'unit, a derivation and an evidence class. <strong>Nothing here is ' +
    'measured</strong> — that class exists so a pilot can promote values into it.'
  ) +

  '<div class="sec"><div class="strip">' +
    order.map(function (k) {
      return readout({ label: ev(k), value: sum[k] || 0, dp: 0, size: 'sm',
        foot: k === 'MEASURED' ? 'enforced by a test' : 'coefficients' });
    }).join('') +
  '</div></div>' +

  '<div class="sec">' + srule('Coefficients', 'core/factors.py') +
    '<div class="tw"><table class="t"><thead><tr><th>Coefficient</th>' +
    '<th class="n">Value</th><th>Unit</th><th>Class</th><th>Basis</th>' +
    '</tr></thead><tbody>' + e.coefficients.map(function (c) {
      return '<tr><td><span class="t-k">' + esc(c.label) + '</span>' +
        '<div class="t-s mono">' + esc(c.key) + '</div></td>' +
        '<td class="n">' + num(c.value, c.value < 1 ? 5 : 2) + '</td>' +
        '<td class="mono micro">' + esc(c.unit) + '</td>' +
        '<td>' + ev(c.evidence) + (c.tunable ? '' :
          '<div class="t-s">fixed</div>') + '</td>' +
        '<td class="small" style="max-width:40ch">' + esc(c.basis) + '</td></tr>';
    }).join('') + '</tbody></table></div>' +
  '</div>' +

  '<div class="sec"><div class="grid g-1-1">' +
    '<div>' + srule('Basin weighting', ev('ASSUMED')) +
      '<div class="formula">' + esc(e.basin_methodology.formula) + '</div>' +
      '<dl class="defs" style="margin-top:var(--s3)">' +
        row('What this is', esc(e.basin_methodology.what_this_is)) +
        row('What it is <b>not</b>', esc(e.basin_methodology.what_this_is_not)) +
        row('Before external use', esc(e.basin_methodology.before_external_use)) +
      '</dl></div>' +
    '<div>' + srule('Release limits', ev('ASSUMED')) +
      '<dl class="defs">' +
        row('Conductivity', '<span class="n">' +
          num(e.release_limits.conductivity_release_ms_cm, 2) + '</span> mS/cm') +
        row('Residual colour', '<span class="n">' +
          num(e.release_limits.colour_release_admi, 0) + '</span> ADMI') +
        row('Fixation temperature', '<span class="n">' +
          num(e.release_limits.fixation_min_temp_c, 0) + '</span> °C min') +
        row('If released wrongly', esc(e.release_limits.failure_consequence)) +
      '</dl></div>' +
  '</div></div>' +

  '<div class="sec">' + srule('Claim register', 'every external claim') +
    '<div class="tw"><table class="t"><thead><tr><th>Claim</th><th>Level</th>' +
    '<th>Safe wording</th></tr></thead><tbody>' +
    e.claim_register.claims.map(function (c) {
      return '<tr><td class="small" style="max-width:48ch">' + esc(c.claim) + '</td>' +
        '<td><span class="mono micro">' + esc(c.level) + '</span>' +
        '<div class="t-s">' + esc(e.claim_register.evidence_levels[c.level] || '') +
        '</div></td><td class="small muted" style="max-width:36ch">' +
        esc(c.safe_wording) + '</td></tr>';
    }).join('') + '</tbody></table></div>' +
    '<div style="margin-top:var(--s3)">' + disc('Forbidden wordings',
      '<ul style="margin:0;padding-left:18px">' +
      e.claim_register.forbidden_wordings.map(function (f) {
        return '<li style="margin-bottom:5px">' + esc(f) + '</li>';
      }).join('') + '</ul>') + '</div>' +
  '</div>';
}

/* ==========================================================================
   VIEW 7 - AUDIT
   ========================================================================== */
function vAudit() {
  var st = S.state, integ = st.ledger_integrity;
  var recs = st.ledger_records || [];

  var events = recs.slice().reverse().map(function (r) {
    var cls = /BLOCKED|LOCK|REJECT/i.test(r.action) ? 'fault'
      : /DECISION|RELEASE|COMMIT/i.test(r.action) ? 'done' : '';
    return {
      t: String(r.timestamp).replace('T', ' ').replace('Z', ''),
      n: r.action.replace(/_/g, ' '),
      d: r.detail + '  — ' + r.actor,
      cls: cls
    };
  });

  return phead('Audit', 'Provenance and evidence chain',
    'An append-only hash chain with a keyed MAC over each link. It answers ' +
    'one question: can a record have been edited after the fact?',
    '<button class="btn" data-act="verify">Re-verify</button>' +
    '<button class="btn" data-act="export">Export</button>'
  ) +

  '<div class="sec"><div class="status ' + (integ.intact ? 'ok' : 'fault') + '">' +
    '<span class="status-k">Chain</span>' +
    '<span class="status-v">' + (integ.intact ? 'Intact' : 'Broken') + '</span>' +
    '<span class="status-t">' + esc(integ.detail) + ' ' +
    '<span class="n">' + integ.records + '</span> records, every link ' +
    'recomputed from its contents.</span>' +
    '<button class="why" data-why="chain">What this proves</button>' +
  '</div>' +
  '<p class="micro muted mono" style="margin-top:8px;word-break:break-all">' +
  'head ' + esc(integ.head_hash) + '</p></div>' +

  '<div class="sec"><div class="grid g-7-5">' +
    '<div>' + srule('Decision event timeline', 'newest last') +
      (events.length ? timeline(events)
        : '<div class="empty"><div class="empty-k">No records</div>' +
          '<h3>Nothing has been decided yet</h3>' +
          '<p>Every approval, rejection, lockout and refusal is recorded here ' +
          'with its actor.</p></div>') +
    '</div>' +
    '<div>' + srule('Records', 'as stored') +
      '<div class="tw"><table class="t"><thead><tr><th class="n">#</th>' +
      '<th>Action</th><th>Actor</th><th>Hash</th></tr></thead><tbody>' +
      recs.map(function (r) {
        return '<tr><td class="n mono">' + r.seq + '</td>' +
          '<td><span class="mono micro">' + esc(r.action) + '</span></td>' +
          '<td class="small">' + esc(r.actor) + '</td>' +
          '<td class="mono micro muted">' +
          esc(String(r.record_hash).slice(0, 10)) + '</td></tr>';
      }).join('') + '</tbody></table></div>' +
    '</div>' +
  '</div></div>';
}

/* ==========================================================================
   VIEW 8 - SCENARIOS
   ========================================================================== */
function vScenarios() {
  if (!S.ablation) {
    api('/api/ablation?mode=' + encodeURIComponent(S.mode))
      .then(function (d) { S.ablation = d; soft('scenarios'); });
  }
  if (!S.sensitivity) {
    api('/api/sensitivity').then(function (d) { S.sensitivity = d; soft('scenarios'); });
  }
  if (!S.modeCompare) {
    api('/api/modes/compare').then(function (d) { S.modeCompare = d; soft('scenarios'); });
  }
  if (!S.cluster) {
    api('/api/cluster-projection').then(function (d) { S.cluster = d; soft('scenarios'); });
  }
  if (!S.pilot) {
    api('/api/pilot').then(function (d) { S.pilot = d; soft('scenarios'); });
  }
  var ab = S.ablation, se = S.sensitivity, mc = S.modeCompare,
      cl = S.cluster, pl = S.pilot, bc = S.businessCase;

  var fields = [
    ['lots_per_year', 'Dye lots per year', 9000, ''],
    ['freshwater_avoided_per_lot_l', 'Freshwater avoided per lot', 1108, 'L'],
    ['salt_avoided_per_lot_kg', 'Salt avoided per lot', 12.5, 'kg'],
    ['freshwater_cost_inr_per_m3', 'Freshwater cost', 45, '₹/m³'],
    ['recycled_water_cost_inr_per_m3', 'Recycled water cost', 135, '₹/m³'],
    ['steam_cost_inr_per_kwh_th', 'Steam cost', 2.4, '₹/kWh'],
    ['salt_cost_inr_per_kg', 'Salt cost', 9, '₹/kg'],
    ['implementation_cost_inr', 'Implementation', 450000, '₹'],
    ['annual_subscription_inr', 'Annual subscription', 240000, '₹']
  ];

  return phead('Scenarios', 'Analysis and proof',
    'Three self-critical tests, all reproducible from the API, plus the ' +
    'economic case computed from your own tariffs.'
  ) +

  /* --- constraint response --- */
  '<div class="sec">' + srule('Constraint response',
    'does the optimiser change its mind?') +
    (mc ? '<div class="tw"><table class="t"><thead><tr>' +
      '<th>Binding constraint</th><th>Recommended strategy</th>' +
      '<th class="n">Freshwater</th><th class="n">Steam</th>' +
      '<th class="n">Cost</th><th class="n">Late</th></tr></thead><tbody>' +
      mc.modes.map(function (m) {
        return '<tr' + (m.mode_id === S.mode ? ' class="rec"' : '') + '>' +
          '<td><span class="t-k">' + esc(m.mode_name) + '</span>' +
          '<div class="t-s">' + esc(m.trigger || '') + '</div></td>' +
          '<td>' + esc(m.strategy_name || m.status) + '</td>' +
          '<td class="n">' + num(m.freshwater_intake_l, 0) + '</td>' +
          '<td class="n">' + num(m.mee_thermal_kwh, 0) + '</td>' +
          '<td class="n">' + inr(m.cost_inr) + '</td>' +
          '<td class="n">' + num(m.total_late_h, 1) + '</td></tr>';
      }).join('') + '</tbody></table></div>' +
      '<p class="small" style="margin-top:10px;max-width:var(--measure)">' +
      esc(mc.interpretation) + ' Normal economics skips the low-salt ' +
      'chemistry, because the dye premium costs more than the steam it ' +
      'saves. Price scarcity or carbon and the same engine buys it.</p>'
      : loading('Comparing modes')) +
  '</div>' +

  /* --- ablation --- */
  '<div class="sec">' + srule('Ablation',
    'under ' + esc(modeName()) + ' &nbsp;' + ev('MODELLED')) +
    (ab ? '<div class="tw"><table class="t"><thead><tr><th>Variant</th>' +
      '<th class="n">Freshwater reported</th><th class="n">vs full</th>' +
      '<th class="n">Steam</th><th class="n">Breach</th>' +
      '<th>Capability lost</th></tr></thead><tbody>' +
      ab.variants.map(function (v) {
        return '<tr' + (v.variant === 'full' ? ' class="rec"' :
          v.firm_breaches > 0 ? ' class="muted"' : '') + '>' +
          '<td class="t-k">' + esc(v.label) + '</td>' +
          '<td class="n">' + num(v.freshwater_avoided_l, 0) + ' L</td>' +
          '<td class="n">' + (v.reported_vs_full_pct == null ? '—'
            : pct(v.reported_vs_full_pct, 0) + (v.overstates
              ? '<div class="t-s" style="color:var(--coral)">over-reports</div>' : '')) +
          '</td><td class="n">' + num(v.mee_thermal_avoided_kwh, 0) + '</td>' +
          '<td class="n"' + (v.firm_breaches > 0 ? ' style="color:var(--coral)"' : '') +
          '>' + v.firm_breaches + '</td>' +
          '<td class="small muted" style="max-width:40ch">' +
          esc(v.capability_lost) +
          (v.overstatement_note ? '<div class="t-s" style="color:var(--coral)">' +
            esc(v.overstatement_note) + '</div>' : '') + '</td></tr>';
      }).join('') + '</tbody></table></div>' +
      '<p class="small" style="margin-top:10px;max-width:var(--measure)">' +
      esc(ab.conclusion) + '</p>'
      : loading('Running ablation')) +
  '</div>' +

  /* --- sensitivity --- */
  '<div class="sec">' + srule('Sensitivity',
    se ? (se.decision_robust ? 'decision robust'
      : se.recommendation_changed_count + ' of ' +
        (se.coefficients.length * 2) + ' runs change the plan') : '') +
    (se ? '<p class="small" style="margin-bottom:var(--s3);max-width:var(--measure)">' +
      esc(se.interpretation) + '</p>' +
      '<div class="tw"><table class="t"><thead><tr><th>Coefficient</th>' +
      '<th>Class</th><th class="n">Base</th><th class="n">Cost swing</th>' +
      '<th>Low bound</th><th>High bound</th></tr></thead><tbody>' +
      se.coefficients.map(function (c) {
        return '<tr><td><span class="t-k">' + esc(c.label) + '</span>' +
          '<div class="t-s mono">' + esc(c.coefficient) + '</div></td>' +
          '<td>' + ev(c.evidence) + '</td>' +
          '<td class="n">' + num(c.base_value, c.base_value < 1 ? 3 : 2) + '</td>' +
          '<td class="n">' + inr(c.cost_swing_inr) + '</td>' +
          c.variants.map(function (v) {
            return '<td class="small"><span class="mono">' +
              num(v.value, v.value < 1 ? 2 : 0) + '</span> &rarr; ' +
              esc(v.recommended_strategy || '—') +
              (v.recommendation_changed
                ? '<div class="t-s" style="color:var(--amber)">changes plan</div>'
                : '') + '</td>';
          }).join('') + '</tr>';
      }).join('') + '</tbody></table></div>'
      : loading('Sweeping coefficients')) +
  '</div>' +

  /* --- business case --- */
  '<div class="sec">' + srule('Economic case', 'your tariffs, not ours') +
    '<div class="grid g-5-7"><div>' +
      '<div class="fields">' + fields.map(function (f) {
        return '<div class="field"><label for="bc_' + f[0] + '">' + esc(f[1]) +
          '</label><div class="field-in"><input id="bc_' + f[0] +
          '" type="number" step="any" min="0" value="' + f[2] + '">' +
          (f[3] ? '<span class="field-u">' + f[3] + '</span>' : '') +
          '</div></div>';
      }).join('') + '</div>' +
      '<div class="row" style="margin-top:var(--s4)">' +
      '<button class="btn btn-pri" data-act="calc">Calculate</button></div>' +
      '<p class="micro muted" style="margin-top:9px">A projection built on a ' +
      'vendor’s assumptions is not a business case. This refuses to ' +
      'compute until you enter your own figures.</p>' +
    '</div><div>' +
      (bc && bc.status === 'CALCULATED' ? caseResult(bc)
        : bc ? '<div class="status fault"><span class="status-k">' +
          esc(String(bc.status).replace(/_/g, ' ')) + '</span>' +
          '<span class="status-t">' + esc(bc.notice || '') + '</span></div>'
        : '<div class="empty"><div class="empty-k">No case computed</div>' +
          '<h3>Enter your site figures</h3><p>Every benefit line is priced ' +
          'from your own tariffs. Nothing is assumed on your behalf.</p></div>') +
    '</div></div>' +
  '</div>' +

  /* --- scale + pilot --- */
  '<div class="sec"><div class="grid g-1-1">' +
    '<div>' + srule('Cluster scale', ev('PROJECTED')) +
      (cl ? '<div class="flows">' +
        flowBand('Freshwater avoided', cl.freshwater_avoided_million_litres_per_year,
          'ML/yr', 1, 'water', 'across ' + num(cl.units, 0) + ' units') +
        flowBand('Salt avoided', cl.salt_avoided_tonnes_per_year, 't/yr', .72,
          'salt', 'less crystalliser load') +
        flowBand('Evaporator steam', cl.evaporator_steam_avoided_mwh_per_year,
          'MWh/yr', .62, 'amber', 'thermal') +
        flowBand('CO₂e avoided', cl.co2e_avoided_tonnes_per_year, 't/yr',
          .48, 'carbon', 'boiler emissions') +
        '</div><p class="micro muted" style="margin-top:10px">' +
        esc(cl.honesty) + '</p>' : loading('Projecting')) +
    '</div>' +
    '<div>' + srule('Pilot', pl ? ev(pl.classification) : '') +
      (pl ? '<div class="tl">' + pl.phases.map(function (ph) {
        return '<div class="tl-e"><div class="tl-t">Weeks ' + esc(ph.weeks) +
          '</div><div class="tl-n">' + esc(ph.name) + '</div>' +
          '<div class="tl-d">' + esc(ph.objective) + '</div></div>';
      }).join('') + '</div>' +
      '<div style="margin-top:var(--s3)">' +
      disc('Stop conditions', '<ul style="margin:0;padding-left:18px">' +
        pl.stop_conditions.map(function (s) {
          return '<li style="margin-bottom:5px">' + esc(s) + '</li>';
        }).join('') + '</ul>') +
      disc('What we will not claim', '<p>' + esc(pl.what_we_will_not_claim) + '</p>') +
      '</div>' : loading('Loading pilot')) +
    '</div>' +
  '</div></div>';
}

function loading(what) {
  return '<div class="load"><div class="load-k">' + esc(what) +
    '</div><div class="load-bar"><i></i></div></div>';
}

function modeName() {
  var m = S.modes && S.modes[S.mode];
  return (m && m.name) || S.mode || 'Normal operation';
}

function caseResult(bc) {
  var q = bc.annual_quantities, b = bc.benefit_breakdown_inr;
  var maxB = 0;
  Object.keys(b).forEach(function (k) { if (b[k] > maxB) maxB = b[k]; });
  return '<div class="stack">' +
    '<div class="strip" style="grid-template-columns:1fr 1fr">' +
      readout({ label: 'Annual net benefit', raw: inr(bc.annual_net_benefit_inr),
        value: bc.annual_net_benefit_inr, tone: 'good',
        foot: 'after subscription' }) +
      readout({ label: 'Payback', value: bc.payback_years, unit: 'yr',
        foot: 'on ' + inr(bc.implementation_cost_inr) + ' capex' }) +
    '</div>' +
    '<div><div class="readout-k" style="margin-bottom:8px">' +
    'Benefit breakdown</div><div class="flows">' +
    Object.keys(b).map(function (k) {
      var tone = /water/.test(k) ? 'water' : /salt|electro/.test(k) ? 'salt'
        : /steam|heat/.test(k) ? 'amber' : 'emerald';
      return flowBand(esc(k.replace(/_/g, ' ')), b[k], '₹',
        maxB > 0 ? b[k] / maxB : 0, tone);
    }).join('') + '</div></div>' +
    '<dl class="defs">' +
      row('Gross annual', inr(bc.annual_gross_benefit_inr)) +
      row('3-year NPV at 12%', inr(bc.npv_3yr_at_12pct_inr)) +
      row('Evaporator steam avoided', num(q.evaporator_steam_avoided_kwh_th / 1000, 1) +
        ' MWh/yr') +
      row('Salt avoided', num(q.salt_avoided_kg / 1000, 1) + ' t/yr') +
    '</dl>' +
    '<p class="micro muted">The water line is priced at your <b>recycled</b> ' +
    'rate, not your freshwater rate. In a closed loop the litre you avoid is ' +
    'the expensive one you would otherwise have had to treat.</p>' +
    disc('Deliberately excluded', '<ul style="margin:0;padding-left:18px">' +
      bc.excluded_from_this_calculation.map(function (x) {
        return '<li style="margin-bottom:5px">' + esc(x) + '</li>';
      }).join('') + '</ul>') +
    '</div>';
}

/* ==========================================================================
   SIDE SHEET
   ========================================================================== */
function sheet(kind, title, html) {
  document.getElementById('sheetKind').textContent = kind;
  document.getElementById('sheetTitle').textContent = title;
  document.getElementById('sheetBody').innerHTML = html;
  document.getElementById('sheet').classList.add('open');
  document.getElementById('sheetBd').classList.add('open');
  document.getElementById('sheetClose').focus();
}
function closeSheet() {
  document.getElementById('sheet').classList.remove('open');
  document.getElementById('sheetBd').classList.remove('open');
}

function openWhy(what) {
  var st = S.state, o = st.optimisation, fc = S.forecast;

  /* The explanation ladder, rung by rung. Six readings of the same fact,
     shortest first, each one true on its own, so a reader can stop
     wherever their interest stops and still be holding something
     correct. */
  if (what === 'reasoning' && S.narrative) {
    var n = S.narrative;
    var body = n.ladder.map(function (r) {
      var eq = r.equation
        ? '<div class="formula" style="margin:10px 0 0">' +
            esc(r.equation) + '</div>'
        : '';
      return '<div class="rung">' +
        '<div class="rung-hd">' +
          '<span class="rung-n mono">' + r.rung + '</span>' +
          '<span class="rung-l">' + esc(r.label) + '</span>' +
          '<span class="rung-a mono micro muted">' + esc(r.audience) +
          ' &middot; ' + r.seconds + 's</span>' +
        '</div>' +
        '<p class="small" style="margin:6px 0 0">' + esc(r.body || '') +
        '</p>' + eq +
        (r.id === 'proof' && r.detail
          ? '<p class="micro muted" style="margin:8px 0 0">' +
              esc(r.detail.reading) + '</p>'
          : '') +
      '</div>';
    }).join('');

    return sheet('Explainability', 'How this works, in six readings',
      '<p class="small" style="margin:0 0 var(--s4)">' + esc(n.so_what) +
      '</p>' + body +
      '<div class="readout-k" style="margin:var(--s5) 0 8px">' +
      'What we are not claiming</div>' +
      '<ul class="small" style="margin:0;padding-left:18px">' +
      n.not_claimed.map(function (x) {
        return '<li style="margin-bottom:7px">' + esc(x) + '</li>';
      }).join('') + '</ul>' +
      '<p class="micro muted" style="margin:var(--s4) 0 0">' +
      esc(n.note) + '</p>');
  }

  /* Cross-validation against published operating data. The honest answer
     to "you have no measured data": our outputs land where real plants
     sit, on inputs the engine never reads back. */
  if (what === 'validation' && S.narrative &&
      S.narrative.evidence_posture) {
    var nv = S.narrative, vd = null, k;
    for (k = 0; k < nv.ladder.length; k++) {
      if (nv.ladder[k].id === 'validation') vd = nv.ladder[k].detail;
    }
    if (!vd) return;
    var rows = vd.points.map(function (p) {
      return '<tr><td class="mono">' + num(p.inlet_tds_mg_l, 0) +
        '</td><td class="small">' + esc(p.note) + '</td>' +
        '<td class="mono" style="text-align:right">' +
        p.predicted_reject_frac_pct.toFixed(1) + '%</td></tr>';
    }).join('');

    return sheet('Evidence', 'How we checked a model with no measurements',
      '<div class="formula">' + esc(vd.headline) + '</div>' +
      '<p class="small" style="margin:var(--s4) 0">' +
      'CPCB measured 18,340 mg/L TDS entering the evaporation stage at an ' +
      'assessed Tirupur unit. Separately, Indian ZLD operators report RO ' +
      'reject at 20\u201330% of inlet volume. Two facts, different ' +
      'sources, neither one an input to this engine. Feed it the first ' +
      'and it predicts the second.</p>' +
      '<table class="t"><thead><tr><th>Inlet TDS fed in</th>' +
      '<th>What that is</th><th class="n">Model ' +
      'predicts</th></tr></thead><tbody>' + rows + '</tbody></table>' +
      '<div class="readout-k" style="margin:var(--s5) 0 8px">' +
      'What this is</div>' +
      '<p class="small" style="margin:0">' + esc(vd.what_this_is) + '</p>' +
      '<div class="readout-k" style="margin:var(--s4) 0 8px">' +
      'What this is not</div>' +
      '<p class="small" style="margin:0">' + esc(vd.what_this_is_not) +
      '</p>' +
      '<div class="readout-k" style="margin:var(--s5) 0 8px">' +
      'Evidence posture</div>' +
      '<p class="small" style="margin:0">' +
      esc(nv.evidence_posture.statement) + '</p>' +
      '<div class="readout-k" style="margin:var(--s4) 0 8px">' +
      'What would promote this to measured</div>' +
      '<p class="small" style="margin:0">' +
      esc(nv.evidence_posture.next_step_to_promote) + '</p>' +
      '<p class="micro muted" style="margin:var(--s4) 0 0">Enforced by ' +
      '<span class="mono">' + esc(vd.enforced_by) + '</span>. Sources are ' +
      'listed in <span class="mono">docs/data_sources.md</span>.</p>');
  }

  if (what === 'recommendation' && o) {
    var r = o.rationale;
    sheet('Explainability', 'Why this recommendation',
      '<div class="formula">' + esc(r.recommendation) + '</div>' +
      '<div class="readout-k" style="margin:var(--s4) 0 8px">Reasons</div>' +
      r.why.map(function (w, n) {
        return '<div style="display:grid;grid-template-columns:24px 1fr;gap:10px;' +
          'padding:8px 0;border-bottom:1px solid var(--hair)">' +
          '<span class="mono micro muted">' + (n < 9 ? '0' : '') + (n + 1) +
          '</span><span class="small">' + esc(w) + '</span></div>';
      }).join('') +
      '<div class="readout-k" style="margin:var(--s5) 0 8px">Constraints satisfied</div>' +
      '<div class="checks">' + r.constraints_satisfied.map(function (c) {
        return check(true, c);
      }).join('') + '</div>' +
      '<div class="readout-k" style="margin:var(--s5) 0 8px">Uncertainty</div>' +
      '<p class="small">' + esc(r.uncertainty) + '</p>' +
      '<div class="readout-k" style="margin:var(--s5) 0 8px">What would change this</div>' +
      '<ul style="margin:0;padding-left:18px" class="small">' +
      r.what_would_change_this.map(function (x) {
        return '<li style="margin-bottom:6px">' + esc(x) + '</li>';
      }).join('') + '</ul>' +
      '<div class="readout-k" style="margin:var(--s5) 0 8px">Not claimed as novel</div>' +
      '<p class="small muted">' + esc(o.not_claimed) + '</p>');
    return;
  }

  if (what === 'weights' && o) {
    sheet('Objective', 'Weights in force',
      '<p class="small">The objective is a scalarised sum in rupees of total ' +
      'consequence. These weights encode a value judgement, so they are shown ' +
      'rather than buried.</p>' +
      '<div class="formula" style="margin:var(--s4) 0">objective = cost\n' +
      '          + strategy_cost\n' +
      '          + stress_L_eq/1000 x stress_premium\n' +
      '          + CO2e_kg/1000   x carbon_price\n' +
      '          + lateness_h     x lateness_penalty</div>' +
      '<dl class="defs">' +
        row('Scarcity premium', '<span class="n">' +
          num(o.weights.stress_premium_inr_per_m3_eq, 0) + '</span> ₹/m³-eq') +
        row('Carbon price', '<span class="n">' +
          num(o.weights.carbon_price_inr_per_tonne, 0) + '</span> ₹/tonne') +
        row('Lateness penalty', '<span class="n">' +
          num(o.weights.lateness_penalty_inr_per_hour, 0) + '</span> ₹/hour') +
      '</dl>' +
      '<div class="readout-k" style="margin:var(--s5) 0 8px">Hard constraints</div>' +
      '<p class="small">Enforced as feasibility, not as a penalty. A plan ' +
      'breaching a firm ship date is refused at any objective value.</p>' +
      '<dl class="defs">' +
        row('Firm dates', o.constraints.no_firm_date_breach ? 'inviolable' : 'relaxed') +
        row('Total lateness', num(o.constraints.max_total_lateness_h, 1) + ' h max') +
        row('Per-lot lateness', num(o.constraints.max_single_lot_lateness_h, 1) + ' h max') +
      '</dl>');
    return;
  }

  if (what === 'salt' && S.insight) {
    var ins = S.insight;
    sheet('Mechanism', 'Salt is water',
      '<div class="formula">V_reject = M_salt / C_reject_max</div>' +
      '<p class="small" style="margin-top:var(--s4)">Salt is conserved. ' +
      'Reverse osmosis, biology and evaporation do not destroy it, and the ' +
      'final RO stage can only concentrate to a ceiling before scaling stops ' +
      'it. So reject volume is fixed by salt mass, and evaporator steam is ' +
      'proportional to reject volume.</p>' +
      '<p class="small">Because the loop is closed, freshwater makeup equals ' +
      'what was evaporated. Freshwater, evaporator load and carbon are the ' +
      'same number here.</p>' +
      '<div class="tw" style="margin-top:var(--s4)"><table class="t"><thead><tr>' +
      '<th>Intervention</th><th class="n">Reject</th><th class="n">Steam</th>' +
      '<th class="n">Change</th></tr></thead><tbody>' +
      [['Baseline', ins.baseline],
       ['Cut water 20% only', ins.cut_water_20pct_only],
       ['Cut salt 20% only', ins.cut_salt_20pct_only],
       ['Cut both 20%', ins.cut_both_20pct]].map(function (p) {
        return '<tr><td class="t-k">' + p[0] + '</td>' +
          '<td class="n">' + num(p[1].reject_l, 0) + ' L</td>' +
          '<td class="n">' + num(p[1].mee_thermal_kwh, 0) + ' kWh</td>' +
          '<td class="n">' + (p[1].mee_energy_change_pct == null ? '—'
            : pct(p[1].mee_energy_change_pct)) + '</td></tr>';
      }).join('') + '</tbody></table></div>' +
      '<div class="readout-k" style="margin:var(--s5) 0 8px">Where it stops</div>' +
      '<p class="small muted">Below a crossover the RO hydraulic floor takes ' +
      'over and further salt reduction buys nothing. A product claiming "cut ' +
      'salt, always win" would be wrong. The engine reports which constraint ' +
      'binds on every stream.</p>');
    return;
  }

  if (what === 'envelope' && fc) {
    var e = fc.plan.envelope;
    sheet('Risk', 'Abstraction envelope',
      '<p class="small">' + esc(e.risk_text) + '</p>' +
      '<div class="formula" style="margin:var(--s4) 0">' +
      esc(e.allocation_basis) + '</div>' +
      '<dl class="defs">' +
        row('Projected draw', '<span class="n">' + num(e.projected_draw_l, 0) + '</span> L') +
        row('Allocation', '<span class="n">' + num(e.allocation_l, 0) + '</span> L') +
        row('Utilisation', pct(e.utilisation_pct)) +
        row('Headroom', '<span class="n">' + num(e.headroom_l, 0) + '</span> L') +
        row('Peak hourly', '<span class="n">' + num(e.peak_hourly_draw_l, 0) +
          '</span> L at ' + esc(e.peak_hour || '—')) +
        row('Breach', esc(e.breach_clock || 'none projected')) +
      '</dl>' +
      '<div class="readout-k" style="margin:var(--s5) 0 8px">Method</div>' +
      '<p class="small">' + esc(fc.plan.method.what_this_is) + '</p>' +
      '<p class="small muted">' + esc(fc.plan.method.what_this_is_not) + '</p>' +
      '<p class="small muted">' + esc(fc.plan.method.band) + '</p>');
    return;
  }

  if (what === 'forecast-method' && fc) {
    var m = fc.plan.method;
    sheet('Method', 'How this projection is made',
      '<dl class="defs">' +
        row('What this is', esc(m.what_this_is)) +
        row('What it is <b>not</b>', esc(m.what_this_is_not)) +
        row('The band', esc(m.band)) +
        row('Why it moves', esc(m.why_it_moves)) +
      '</dl>');
    return;
  }

  if (what === 'gate' && st.washoff) {
    var g = st.washoff.gate;
    sheet('Safety', 'Why the gate is fail-closed',
      '<p class="small">Ending wash-off early on unfixed dye causes bleeding ' +
      'and a failed fastness test. The lot is then re-processed, consuming ' +
      '<b>more</b> water, steam and salt than the baths that were skipped. A ' +
      'wrong release destroys the very saving it was chasing.</p>' +
      '<div class="readout-k" style="margin:var(--s4) 0 8px">Clearance</div>' +
      '<div class="checks">' + [
        ['conductivity_asymptote', 'Conductivity at release limit'],
        ['residual_colour_within_limit', 'Residual colour within limit'],
        ['fixation_temperature_held', 'Fixation temperature held'],
        ['dual_probe_agreement', 'Dual probes agree'],
        ['data_completeness', 'Telemetry complete']
      ].map(function (c) { return check(g.checks[c[0]], c[1]); }).join('') + '</div>' +
      '<dl class="defs" style="margin-top:var(--s4)">' +
        row('Authority', esc(g.authority)) +
        row('Automatic release', '<span class="mono">' +
          String(g.automatic_release) + '</span> — hardcoded, with no ' +
          'code path that sets it true') +
        row('If released wrongly', esc(st.release_limits.failure_consequence)) +
      '</dl>');
    return;
  }

  if (what === 'chain') {
    var k = st.ledger_integrity.key;
    sheet('Provenance', 'What the chain proves',
      '<div class="formula">record_hash = HMAC_SHA256(key,\n' +
      '  seq | timestamp | actor | action | detail\n' +
      '  | payload_hash | prev_hash)</div>' +
      '<dl class="defs" style="margin-top:var(--s4)">' +
        row('Proves', esc(k.proves)) +
        row('Does <b>not</b> prove', esc(k.does_not_prove)) +
        row('Not a blockchain', esc(k.not_a_blockchain)) +
        row('Mechanism', esc(k.mechanism)) +
        row('Key source', esc(k.source) + (k.is_secret ? ''
          : ' — a published constant, not a secret. Anything else would ' +
            'be security theatre.')) +
      '</dl>' +
      '<p class="small muted" style="margin-top:var(--s4)">The detail field is ' +
      'inside the MAC deliberately: it is the text an auditor actually reads, ' +
      'so leaving it out would let a record’s meaning be rewritten while ' +
      'the chain still verified.</p>');
    return;
  }

  if (what === 'balance') {
    sheet('Accounting', 'Water vocabulary and rules',
      '<p class="small">These six quantities are defined once and never used ' +
      'interchangeably. Conflating them is the most common way water claims ' +
      'become dishonest.</p>' +
      '<dl class="defs" style="margin-top:var(--s4)">' +
        row('Process demand', 'water the process must receive, from any source') +
        row('Permeate reuse', 'recovered water actually fed back, bounded by ' +
          'both what RO produced and what the process demands') +
        row('Freshwater intake', 'demand reuse could not cover — the only ' +
          'figure representing new abstraction') +
        row('Evaporative loss', 'water destroyed in the evaporator; not ' +
          'available for reuse') +
        row('Demand avoided', 'reduction in demand versus baseline. <b>Not</b> ' +
          'a recovery figure') +
        row('Freshwater avoided', 'reduction in intake versus baseline. The ' +
          'headline number, always &le; baseline intake') +
      '</dl>' +
      '<div class="formula" style="margin-top:var(--s4)">' +
      'process_demand = permeate_reuse + freshwater_intake</div>');
    return;
  }

  toast('No explanation registered for that.', true);
}

function openTrace(metric) {
  api('/api/trace?metric=' + encodeURIComponent(metric)).then(function (t) {
    sheet('Derivation', t.metric,
      '<div class="formula">' + esc(t.formula) + '</div>' +
      '<dl class="defs" style="margin-top:var(--s4)">' +
        row('Evidence', ev(t.evidence) + ' <span class="small muted">' +
          esc(t.evidence) + '</span>') +
      '</dl>' +
      '<div class="readout-k" style="margin:var(--s5) 0 8px">Upstream chain</div>' +
      '<div class="tl">' + t.upstream.map(function (u) {
        return '<div class="tl-e"><div class="tl-n mono small">' + esc(u) +
          '</div></div>';
      }).join('') + '</div>' +
      (t.coefficient_detail && t.coefficient_detail.length
        ? '<div class="readout-k" style="margin:var(--s5) 0 8px">' +
          'Coefficients</div><div class="tw"><table class="t"><tbody>' +
          t.coefficient_detail.map(function (c) {
            return '<tr><td><span class="t-k">' + esc(c.label) + '</span>' +
              '<div class="t-s">' + esc(c.basis) + '</div></td>' +
              '<td class="n nowrap">' + num(c.value, c.value < 1 ? 5 : 2) +
              '<div class="t-s mono">' + esc(c.unit) + '</div></td>' +
              '<td>' + ev(c.evidence) + '</td></tr>';
          }).join('') + '</tbody></table></div>' : ''));
  }).catch(function (e) { toast(e.message, true); });
}

/* ==========================================================================
   COMMAND PALETTE
   ========================================================================== */
var CMDS = [];
function buildCmds() {
  CMDS = VIEWS.map(function (v) {
    return { lbl: v.label, grp: 'Go to', ico: v.ico, run: function () { go(v.id); } };
  }).concat([
    { lbl: 'Run optimiser', grp: 'Action', ico: 'command',
      run: function () { act('optimise'); } },
    { lbl: 'Accept recommendation', grp: 'Action', ico: 'check',
      run: function () { act('approve'); } },
    { lbl: 'Reject recommendation', grp: 'Action', ico: 'cross',
      run: function () { act('reject'); } },
    { lbl: 'Run wash-off telemetry', grp: 'Action', ico: 'water',
      run: function () { fault('none'); } },
    { lbl: 'Inject calibration drift', grp: 'Action', ico: 'water',
      run: function () { fault('sensor_drift'); } },
    { lbl: 'Verify ledger chain', grp: 'Action', ico: 'audit',
      run: function () { act('verify'); } },
    { lbl: 'Export evidence', grp: 'Action', ico: 'export',
      run: function () { act('export'); } },
    { lbl: 'Download export', grp: 'Action', ico: 'export',
      run: function () { act('download'); } },
    { lbl: 'Reset session', grp: 'Action', ico: 'reset',
      run: function () { document.getElementById('resetBtn').click(); } },
    { lbl: 'Toggle dark mode', grp: 'View', ico: 'evidence',
      run: function () { setTheme(isDark() ? 'light' : 'dark'); } }
  ]);
}

var cpSel = 0, cpFiltered = [];
function openPalette() {
  buildCmds();
  document.getElementById('cp').classList.add('open');
  document.getElementById('cpBd').classList.add('open');
  var inp = document.getElementById('cpInput');
  inp.value = ''; inp.focus();
  filterCmds('');
}
function closePalette() {
  document.getElementById('cp').classList.remove('open');
  document.getElementById('cpBd').classList.remove('open');
}
function filterCmds(q) {
  var s = q.trim().toLowerCase();
  cpFiltered = CMDS.filter(function (c) {
    return !s || c.lbl.toLowerCase().indexOf(s) >= 0 ||
      c.grp.toLowerCase().indexOf(s) >= 0;
  });
  cpSel = 0;
  renderCmds();
}
function renderCmds() {
  var el = document.getElementById('cpList');
  if (!cpFiltered.length) {
    el.innerHTML = '<div class="cp-empty">No command matches.</div>';
    return;
  }
  el.innerHTML = cpFiltered.map(function (c, i) {
    return '<button class="cp-item" role="option" aria-selected="' +
      (i === cpSel) + '" data-i="' + i + '">' + ico(c.ico, 14) +
      '<span class="lbl">' + esc(c.lbl) + '</span>' +
      '<span class="grp">' + esc(c.grp) + '</span></button>';
  }).join('');
  Array.prototype.forEach.call(el.querySelectorAll('.cp-item'), function (b) {
    b.onclick = function () {
      closePalette();
      cpFiltered[Number(b.dataset.i)].run();
    };
  });
}

/* ==========================================================================
   ACTIONS
   ========================================================================== */
function act(a) {
  if (a === 'optimise') {
    return guard(function () {
      return post('/api/optimise', { mode: S.mode })
        .then(function (x) { S.state = x; return api('/api/forecast'); })
        .then(function (f) {
          S.forecast = f;
          toast('Evaluated ' + S.state.optimisation.candidates_evaluated +
            ' candidates. Optimum proven.');
        });
    });
  }
  if (a === 'approve' || a === 'reject') {
    return guard(function () {
      return post('/api/decision/sequence',
        { approve: a === 'approve', actor: 'Shift planner' },
        'seq-' + Date.now())
        .then(function (x) { S.state = x; return api('/api/forecast'); })
        .then(function (f) {
          S.forecast = f;
          toast(a === 'approve'
            ? 'Accepted and recorded. The plan is the executed order.'
            : 'Rejected and recorded. Arrival order retained, nothing credited.');
          if (a === 'approve' && S.view === 'decisions') S.view = 'water';
        });
    });
  }
  if (a === 'release' || a === 'norelease') {
    return guard(function () {
      return post('/api/washoff/release',
        { approve: a === 'release', actor: 'Quality supervisor' },
        'rel-' + Date.now())
        .then(function (x) { S.state = x; return api('/api/forecast'); })
        .then(function (f) {
          S.forecast = f;
          toast(a === 'release' ? 'Released and recorded.'
            : 'Declined. Full cycle will run, nothing credited.');
        });
    });
  }
  if (a === 'verify') {
    return guard(function () {
      return api('/api/ledger/verify').then(function (r) {
        return refreshState().then(function () {
          toast(r.intact
            ? 'Chain verified: ' + r.records + ' records, every link recomputed.'
            : 'Chain broken at record ' + r.first_break_at_seq, !r.intact);
        });
      });
    });
  }
  if (a === 'export' || a === 'download') {
    return guard(function () {
      return api('/api/export').then(function (x) {
        if (a === 'download') {
          var blob = new Blob([JSON.stringify(x, null, 2)],
            { type: 'application/json' });
          var el = document.createElement('a');
          el.href = URL.createObjectURL(blob);
          el.download = 'changeloop-' + x.export_id.slice(0, 8) + '.json';
          el.click();
          URL.revokeObjectURL(el.href);
          toast('Export downloaded. SHA-256 ' + x.export_sha256.slice(0, 16));
        } else {
          sheet('Export', 'Evidence export',
            '<dl class="defs">' +
              row('Export id', '<span class="mono small">' + esc(x.export_id) + '</span>') +
              row('Generated', '<span class="mono small">' + esc(x.generated_at) + '</span>') +
              row('Calculation version', '<span class="mono small">' +
                esc(x.calculation_version) + '</span>') +
              row('Chain', x.ledger_integrity.intact ? 'intact' : 'BROKEN') +
              row('SHA-256', '<span class="mono micro" style="word-break:break-all">' +
                esc(x.export_sha256) + '</span>') +
            '</dl>' +
            '<p class="small muted" style="margin:var(--s4) 0 8px">' +
            esc(x.evidence.disclaimer) + '</p>' +
            '<div class="row"><button class="btn btn-pri" data-act="download">' +
            'Download JSON</button></div>');
        }
      });
    });
  }
  if (a === 'calc') {
    return guard(function () {
      var body = {};
      Array.prototype.forEach.call(
        document.querySelectorAll('[id^="bc_"]'), function (el) {
          body[el.id.slice(3)] = Number(el.value);
        });
      return post('/api/business-case', body).then(function (r) {
        S.businessCase = r;
        toast('Case computed from your inputs.');
      }).catch(function (e) {
        S.businessCase = e.payload || { status: 'ERROR', notice: e.message };
        throw e;
      });
    });
  }
}

function fault(mode) {
  return guard(function () {
    return post('/api/washoff/run', { fault_mode: mode })
      .then(function (x) { S.state = x; return api('/api/forecast'); })
      .then(function (f) {
        S.forecast = f;
        var g = S.state.washoff.gate;
        if (S.view !== 'water') S.view = 'water';
        toast(g.state === 'LOCKED_OUT' ? 'Locked out: ' + g.lockout_reason
          : 'Wash-off complete. Gate: ' + g.state.replace(/_/g, ' '),
          g.state === 'LOCKED_OUT');
      });
  });
}

/* ==========================================================================
   WIRING
   ========================================================================== */
function wire() {
  var v = document.getElementById('view');
  function each(sel, fn) {
    Array.prototype.forEach.call(v.querySelectorAll(sel), fn);
  }
  each('[data-go]', function (b) { b.onclick = function () { go(b.dataset.go); }; });
  each('[data-act]', function (b) { b.onclick = function () { act(b.dataset.act); }; });
  each('[data-fault]', function (b) { b.onclick = function () { fault(b.dataset.fault); }; });
  each('[data-why]', function (b) { b.onclick = function () { openWhy(b.dataset.why); }; });
  each('[data-trace]', function (b) {
    b.onclick = function () { openTrace(b.dataset.trace); };
  });
  each('[data-stream]', function (b) {
    b.onclick = function () {
      S.selectedStream = b.dataset.stream || null;
      render();
    };
  });
}

/* sheet wiring, once */
document.getElementById('sheetClose').onclick = closeSheet;
document.getElementById('sheetBd').onclick = closeSheet;
document.getElementById('cpBd').onclick = closePalette;
document.getElementById('cpInput').addEventListener('input', function (e) {
  filterCmds(e.target.value);
});

/* the sheet may contain actions */
document.getElementById('sheetBody').addEventListener('click', function (e) {
  var b = e.target.closest ? e.target.closest('[data-act]') : null;
  if (b) act(b.dataset.act);
});

document.addEventListener('keydown', function (e) {
  var cpOpen = document.getElementById('cp').classList.contains('open');

  if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
    e.preventDefault();
    cpOpen ? closePalette() : openPalette();
    return;
  }
  if (cpOpen) {
    if (e.key === 'Escape') { closePalette(); return; }
    if (e.key === 'ArrowDown') {
      e.preventDefault(); cpSel = Math.min(cpSel + 1, cpFiltered.length - 1);
      renderCmds(); return;
    }
    if (e.key === 'ArrowUp') {
      e.preventDefault(); cpSel = Math.max(cpSel - 1, 0); renderCmds(); return;
    }
    if (e.key === 'Enter' && cpFiltered[cpSel]) {
      closePalette(); cpFiltered[cpSel].run(); return;
    }
    return;
  }
  if (e.key === 'Escape') { closeSheet(); return; }
  if (e.target.matches && e.target.matches('input, select, textarea')) return;

  var n = parseInt(e.key, 10);
  if (n >= 1 && n <= VIEWS.length) go(VIEWS[n - 1].id);
});

/* data freshness ticks without re-rendering the page */
setInterval(function () {
  if (!S.busy) updateCtx();
}, 15000);

/* The changeover matrix powers the process river. A failure here must
   degrade that one visual, not break the application, so it is caught. */
api('/api/changeover-matrix').then(function (d) {
  S.matrix = d.matrix;
  if (S.view === 'decisions') render();
}).catch(function () {
  S.matrix = null;   /* the river falls back to nodes without burdens */
});

boot();
