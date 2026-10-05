/* ==========================================================================
   ChangeLoop - front end

   No framework, no build step. Every number rendered here comes from the
   server; nothing is computed in the browser and nothing is hardcoded. If a
   figure appears on screen, core/ produced it and it can be traced.
   ========================================================================== */
'use strict';

var S = {
  state: null, sites: null, modes: null, mode: 'NORMAL', view: 'brief',
  insight: null, ablation: null, sensitivity: null, modeCompare: null,
  evidence: null, pilot: null, cluster: null, businessCase: null, busy: false
};

var VIEWS = [
  { id: 'brief', label: 'Brief' },
  { id: 'decision', label: 'Decision' },
  { id: 'washoff', label: 'Wash-off gate' },
  { id: 'consequence', label: 'Consequence' },
  { id: 'evidence', label: 'Evidence' },
  { id: 'ledger', label: 'Ledger' },
  { id: 'case', label: 'Business case' },
  { id: 'scale', label: 'Scale & proof' }
];

/* ---------- utilities ---------- */
function esc(s) {
  return String(s == null ? '' : s)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}

function num(v, dp) {
  if (v == null || v === '') return '—';
  var n = Number(v);
  if (!isFinite(n)) return '—';
  var d = (dp == null)
    ? (Math.abs(n) >= 100 ? 0 : Math.abs(n) >= 10 ? 1 : 2)
    : dp;
  return n.toLocaleString('en-IN',
    { minimumFractionDigits: d, maximumFractionDigits: d });
}

function inr(v) { return v == null ? '—' : '₹' + num(v, 0); }

function val(v, unit, dp) {
  return '<span class="num">' + num(v, dp) + '</span>' +
    (unit ? ' <span class="unit">' + esc(unit) + '</span>' : '');
}

function ev(kind) {
  var k = String(kind || 'MODELLED').toUpperCase();
  return '<span class="ev ev-' + esc(k) + '">' + esc(k) + '</span>';
}

/* A delta where DOWN is good: we are reducing consumption. */
function deltaDown(v, unit, dp) {
  if (v == null || !isFinite(Number(v))) {
    return '<span class="delta flat">—</span>';
  }
  var n = Number(v);
  if (Math.abs(n) < 0.005) return '<span class="delta flat">no change</span>';
  var cls = n > 0 ? 'down' : 'up';
  var sign = n > 0 ? '−' : '+';
  return '<span class="delta ' + cls + '">' + sign + num(Math.abs(n), dp) +
    (unit ? ' ' + esc(unit) : '') + '</span>';
}

function row(k, v) { return '<div><dt>' + k + '</dt><dd>' + v + '</dd></div>'; }

var toastTimer = null;
function toast(msg, isErr) {
  var t = document.getElementById('toast');
  t.textContent = msg;
  t.className = 'toast show' + (isErr ? ' err' : '');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(function () { t.className = 'toast'; }, 4600);
}

/* ---------- api ---------- */
function api(path, opts) {
  var o = opts || {};
  o.headers = o.headers || { 'Content-Type': 'application/json' };
  return fetch(path, o).then(function (res) {
    return res.json().catch(function () { return null; }).then(function (body) {
      if (!res.ok) {
        var msg = (body && body.error && body.error.message) ||
          ('Request failed with status ' + res.status);
        var err = new Error(msg);
        err.payload = body;
        throw err;
      }
      return body;
    });
  });
}

function post(path, data, idem) {
  var h = { 'Content-Type': 'application/json' };
  if (idem) h['Idempotency-Key'] = idem;
  return api(path, { method: 'POST', headers: h,
    body: JSON.stringify(data || {}) });
}

/* ---------- boot ---------- */
function boot() {
  Promise.all([api('/api/state'), api('/api/sites'), api('/api/modes')])
    .then(function (r) {
      S.state = r[0]; S.sites = r[1]; S.modes = r[2].modes;
      renderMast(); renderRail(); render();
      api('/api/insight/salt-is-water').then(function (d) {
        S.insight = d;
        if (S.view === 'brief' || S.view === 'consequence') render();
      });
    })
    .catch(function (e) {
      document.getElementById('view').innerHTML =
        '<div class="sec-body"><div class="callout stop">' +
        '<div class="callout-title">Cannot reach the engine</div>' +
        esc(e.message) + '<p class="small muted" style="margin-top:8px">' +
        'Start it with <span class="mono-sm">python backend/server.py</span>' +
        '</p></div></div>';
    });
}

function renderMast() {
  var siteSel = document.getElementById('siteSelect');
  siteSel.innerHTML = S.sites.sites.map(function (s) {
    return '<option value="' + esc(s.site_id) + '"' +
      (s.site_id === S.state.site_id ? ' selected' : '') + '>' +
      esc(s.cluster.split(',')[0]) + ' — ' + esc(s.band) + ' stress' +
      '</option>';
  }).join('');
  siteSel.onchange = function () {
    guard(function () {
      return post('/api/session/site', { site_id: siteSel.value })
        .then(function (st) {
          S.state = st;
          S.ablation = S.sensitivity = S.modeCompare = null;
          toast('Site changed. Downstream decisions were invalidated ' +
            'because the basin weighting and cost basis differ.');
        });
    });
  };

  var modeSel = document.getElementById('modeSelect');
  modeSel.innerHTML = Object.keys(S.modes).map(function (k) {
    return '<option value="' + esc(k) + '"' + (k === S.mode ? ' selected' : '') +
      '>' + esc(S.modes[k].name) + '</option>';
  }).join('');
  modeSel.onchange = function () {
    S.mode = modeSel.value;
    // The proof studies are mode-dependent, so drop the cached ones.
    S.ablation = S.sensitivity = null;
    guard(function () {
      return post('/api/optimise', { mode: S.mode }).then(function (st) {
        S.state = st;
        toast('Re-optimised under: ' + modeName());
        if (S.view === 'brief') S.view = 'decision';
      });
    });
  };

  document.getElementById('resetBtn').onclick = function () {
    guard(function () {
      return post('/api/session/reset', {}).then(function (st) {
        S.state = st; S.businessCase = null; S.view = 'brief';
        toast('Session reset. A new ledger chain was started.');
      });
    });
  };

  var themeBtn = document.getElementById('themeBtn');
  try {
    var stored = localStorage.getItem('cl-theme');
    if (stored) document.documentElement.setAttribute('data-theme', stored);
  } catch (e) { /* private mode */ }

  function isDark() {
    var cur = document.documentElement.getAttribute('data-theme');
    return cur === 'dark' || (!cur &&
      window.matchMedia('(prefers-color-scheme: dark)').matches);
  }
  function syncTheme() {
    document.getElementById('themeLabel').textContent =
      isDark() ? 'Light' : 'Dark';
  }
  themeBtn.onclick = function () {
    var next = isDark() ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', next);
    try { localStorage.setItem('cl-theme', next); } catch (e) { /* ignore */ }
    syncTheme();
    render();
  };
  syncTheme();
}

function renderRail() {
  var nav = document.getElementById('railNav');
  nav.innerHTML = VIEWS.map(function (v, i) {
    return '<button class="rail-item" data-view="' + v.id + '"' +
      (v.id === S.view ? ' aria-current="page"' : '') + '>' +
      '<span class="idx">' + (i + 1 < 10 ? '0' : '') + (i + 1) + '</span>' +
      '<span class="lbl">' + esc(v.label) + '</span></button>';
  }).join('');
  Array.prototype.forEach.call(nav.querySelectorAll('.rail-item'),
    function (b) {
      b.onclick = function () {
        S.view = b.dataset.view; renderRail(); render(); window.scrollTo(0, 0);
      };
    });
}

function guard(fn) {
  if (S.busy) return Promise.resolve();
  S.busy = true;
  return Promise.resolve()
    .then(fn)
    .catch(function (e) { toast(e.message, true); })
    .then(function () { S.busy = false; render(); renderRail(); });
}

/* ========================================================================== */
/* views                                                                      */
/* ========================================================================== */

function render() {
  var map = {
    brief: viewBrief, decision: viewDecision, washoff: viewWashoff,
    consequence: viewConsequence, evidence: viewEvidence, ledger: viewLedger,
    'case': viewCase, scale: viewScale
  };
  document.getElementById('view').innerHTML = (map[S.view] || viewBrief)();
  wire();
}

/* The selected mode's display name, tolerant of a registry that has not
   loaded yet - a view must never crash on missing reference data. */
function modeName() {
  var m = S.modes && S.modes[S.mode];
  return (m && m.name) || S.mode || 'Normal operation';
}

function head(eyebrow, title, lede) {
  return '<div class="sec-head"><div class="sec-eyebrow">' + esc(eyebrow) +
    '</div><h1 class="sec-title">' + esc(title) + '</h1>' +
    (lede ? '<p class="sec-lede">' + lede + '</p>' : '') + '</div>';
}

/* ---------- 01 brief ---------- */
function viewBrief() {
  var st = S.state, b = st.basin, ins = S.insight;

  return head(
    'Hero use case — reactive dyeing under a Zero Liquid Discharge mandate',
    'A scheduling decision this morning sets how much coal the evaporator burns tonight.',
    'Zero Liquid Discharge solved water <em>recovery</em> in clusters like ' +
    'Tirupur — roughly 95% of water is recycled. What it did not solve is ' +
    'the cost of getting it back. Evaporating the reverse-osmosis reject is ' +
    'steam-intensive, and the volume of that reject is set by the ' +
    '<strong>salt</strong> an upstream dyeing decision put into the water. The ' +
    'planner who makes that decision never sees the evaporator.'
  ) + '<div class="sec-body">' +

  '<div class="block">' +
    '<div class="block-head"><h2 class="block-title">' +
      'The insight this product is built on</h2>' +
      '<span class="block-note">computed live from salt mass conservation ' +
      ev('DERIVED') + '</span></div>' +
    '<div class="callout insight">' +
      '<div class="callout-title">' +
        'In a zero-liquid-discharge plant, salt is water</div>' +
      '<div class="formula">V_reject  =  M_salt / C_reject_max</div>' +
      '<p style="margin-top:10px">Salt is conserved — reverse osmosis, ' +
      'biology and evaporation do not destroy it. The final RO stage can only ' +
      'concentrate to a ceiling before scaling stops it. So reject volume is ' +
      'fixed by <strong>salt mass</strong>, not by water volume, and ' +
      'evaporator steam is proportional to reject volume. Therefore:</p>' +
      '<p><strong>Cutting water without cutting salt does not cut evaporator ' +
      'energy.</strong> And because the loop is closed, freshwater makeup ' +
      'exactly equals what was evaporated — so in this plant freshwater ' +
      'and carbon are the same number.</p>' +
      (ins ? '<div class="metrics" style="margin-top:14px">' +
        '<div class="metric"><div class="metric-label">' +
          'Cut water 20%, salt unchanged</div><div class="metric-value">' +
          val(ins.cut_water_20pct_only.mee_energy_change_pct, '%', 1) +
          '</div><div class="metric-foot">change in evaporator energy</div></div>' +
        '<div class="metric is-energy"><div class="metric-label">' +
          'Cut salt 20%, water unchanged</div><div class="metric-value">' +
          val(ins.cut_salt_20pct_only.mee_energy_change_pct, '%', 1) +
          '</div><div class="metric-foot">change in evaporator energy</div></div>' +
        '<div class="metric"><div class="metric-label">Binding constraint</div>' +
          '<div class="metric-value" style="font-size:15px">' +
          esc(ins.baseline.binding_constraint.replace('_', ' ')) +
          '</div><div class="metric-foot">salt-limited, not hydraulic</div></div>' +
      '</div>' : '') +
    '</div></div>' +

  '<div class="block">' +
    '<div class="block-head"><h2 class="block-title">Site under consideration</h2>' +
      '<span class="block-note">' + ev(b.evidence) +
      ' basin weighting — see Evidence</span></div>' +
    '<div class="grid-2">' +
      '<div class="callout"><div class="callout-title">' + esc(b.cluster) +
        '</div><p>' + esc(b.context) + '</p>' +
        '<dl class="defs" style="margin-top:10px">' +
          row('Water body', esc(b.basin_name)) +
          row('Regulatory regime', esc(b.regulatory_regime)) +
          row('Stress weight', '<span class="num">' + num(b.stress_weight, 2) +
            '</span>&#215; &nbsp;<span class="muted small">' + esc(b.band) +
            '</span>') +
        '</dl></div>' +
      '<div>' + stepsBar() + '<div style="margin-top:14px">' + heroMetrics() +
      '</div></div>' +
    '</div></div>' +

  '<div class="block">' +
    '<div class="block-head"><h2 class="block-title">' +
      'Why no existing system catches this</h2></div>' +
    '<div class="tbl-wrap"><table class="tbl">' +
      '<thead><tr><th>System already in the plant</th>' +
      '<th>What it optimises</th><th>What it cannot see</th></tr></thead>' +
      '<tbody>' + [
        ['Dyehouse ERP / production planner',
         'Order delivery dates and machine loading',
         'Water, salt and the downstream evaporator entirely'],
        ['CETP / ZLD plant SCADA',
         'Treating whatever arrives at the inlet, reliably',
         'That the inlet load was decided hours earlier, upstream'],
        ['CPCB OCEMS online monitoring',
         'Regulatory compliance reporting of effluent',
         'Causation — it measures outcomes, not the decisions behind them'],
        ['ESG / sustainability reporting',
         'Disclosing last quarter accurately',
         'Anything about tomorrow’s schedule'],
        ['Dye supplier technical service',
         'Recipe and chemistry for a given shade',
         'Lot sequence, and the plant’s own steam cost']
      ].map(function (r) {
        return '<tr><td class="row-label">' + esc(r[0]) + '</td><td>' +
          esc(r[1]) + '</td><td class="muted">' + esc(r[2]) + '</td></tr>';
      }).join('') + '</tbody></table></div>' +
    '<p class="small muted" style="margin-top:10px">Each of these works. The ' +
    'gap is <em>between</em> them: the planning decision and the treatment ' +
    'consequence sit in different systems, different departments and often ' +
    'different companies. ChangeLoop is the layer that prices one into the ' +
    'other.</p></div>' +

  '<div class="btn-row">' +
    '<button class="btn btn-primary" data-go="decision">' +
      'See the decision →</button>' +
    '<button class="btn" data-go="scale">Proof that it matters</button>' +
  '</div></div>';
}

function heroMetrics() {
  var i = S.state.impact;
  var nothing = S.state.sequencing_status !== 'APPROVED' &&
    S.state.washoff_status !== 'RELEASED';
  return '<div class="metrics">' +
    '<div class="metric is-water"><div class="metric-label">' +
      'Freshwater avoided ' + ev('MODELLED') + '</div><div class="metric-value">' +
      val(i.freshwater_avoided_l, 'L') + '</div><div class="metric-foot">' +
      '<span class="num">' + num(i.stress_equivalent_avoided_l_eq, 0) +
      '</span> L-eq stress weighted</div></div>' +
    '<div class="metric is-salt"><div class="metric-label">Salt load avoided</div>' +
      '<div class="metric-value">' + val(i.salt_avoided_kg, 'kg') + '</div>' +
      '<div class="metric-foot">this is what sets evaporator duty</div></div>' +
    '<div class="metric is-energy"><div class="metric-label">' +
      'Evaporator steam avoided</div><div class="metric-value">' +
      val(i.mee_thermal_avoided_kwh, 'kWh') + '</div>' +
      '<div class="metric-foot">thermal, at the ZLD plant</div></div>' +
    '<div class="metric is-carbon"><div class="metric-label">' +
      'CO₂e avoided</div><div class="metric-value">' +
      val(i.co2e_avoided_kg, 'kg') + '</div><div class="metric-foot">' +
      inr(i.cost_avoided_inr) + ' per shift</div></div></div>' +
    (nothing ? '<p class="small muted" style="margin-top:9px">Nothing is ' +
      'credited yet, because no decision has been approved. These figures ' +
      'reflect the decisions actually taken — currently none.</p>' : '');
}

function stepsBar() {
  var st = S.state;
  var steps = [
    { n: 'Optimise', s: st.optimisation ? 'done' : 'active',
      t: st.optimisation ? st.optimisation.candidates_evaluated + ' candidates'
        : 'not run' },
    { n: 'Approve plan',
      s: st.sequencing_status === 'APPROVED' ? 'done'
        : st.sequencing_status === 'REJECTED' ? 'blocked'
        : st.optimisation ? 'active' : '',
      t: st.sequencing_status },
    { n: 'Wash-off telemetry',
      s: st.washoff ? (st.washoff_status === 'LOCKED_OUT' ? 'blocked' : 'done')
        : '',
      t: st.washoff_status },
    { n: 'Release',
      s: st.washoff_status === 'RELEASED' ? 'done'
        : st.washoff_status === 'LOCKED_OUT' ? 'blocked'
        : st.washoff_status === 'AWAITING' ? 'active' : '',
      t: st.washoff_status === 'AWAITING' ? 'awaiting human'
        : st.washoff_status },
    { n: 'Ledger', s: st.impact.validation.all_pass ? 'done' : 'blocked',
      t: st.impact.validation.all_pass ? 'invariants pass' : 'FAILED' }
  ];
  return '<div class="steps">' + steps.map(function (s, i) {
    return '<div class="step ' + s.s + '"><div class="step-idx">Step ' +
      (i + 1) + '</div><div class="step-name">' + esc(s.n) + '</div>' +
      '<div class="step-state">' + esc(String(s.t).replace(/_/g, ' ')) +
      '</div></div>';
  }).join('') + '</div>';
}

/* ---------- 02 decision ---------- */
function viewDecision() {
  var st = S.state;
  if (!st.optimisation) {
    return head('Decision', 'Lot sequence and process strategy') +
      '<div class="sec-body"><div class="state-msg">' +
      '<h3>No optimisation has been run</h3><p>The optimiser enumerates every ' +
      'lot order against every process strategy, scores each on the full ' +
      'downstream consequence, and discards any that breaches a hard ' +
      'constraint.</p><button class="btn btn-primary" data-act="optimise">' +
      'Run optimiser</button></div></div>';
  }
  var o = st.optimisation;
  if (o.status !== 'FEASIBLE') {
    return head('Decision', 'No feasible plan') + '<div class="sec-body">' +
      '<div class="callout stop"><div class="callout-title">' +
      esc(o.status.replace(/_/g, ' ')) + '</div>' + esc(o.reason || '') +
      '</div></div>';
  }
  var decided = st.sequencing_status !== 'PENDING';

  return head('Decision — ' + modeName(),
    'Three plans, scored on identical coefficients',
    'The recommendation is the lowest total consequence among plans that ' +
    'satisfy every hard constraint. Option C exists to make the constraint ' +
    'layer visible: it saves the most freshwater, and ChangeLoop refuses it.'
  ) + '<div class="sec-body">' +

  '<div class="block"><div class="block-head"><h2 class="block-title">Search' +
    '</h2><span class="block-note">' + esc(o.method) + ' · ' +
    (o.optimality === 'PROVEN_GLOBAL_OPTIMUM'
      ? 'optimum <strong>proven</strong>, not approximated'
      : 'local optimum, not proven global') + '</span></div>' +
    '<div class="options">' + o.options.map(optCard).join('') + '</div></div>' +

  '<div class="block"><div class="block-head"><h2 class="block-title">' +
    'Why this plan</h2><span class="block-note">' + ev('MODELLED') +
    '</span></div><div class="grid-2">' +
    '<div class="callout good"><div class="callout-title">Recommendation</div>' +
      '<p style="font-weight:600">' + esc(o.rationale.recommendation) + '</p>' +
      '<ul class="reasons">' + o.rationale.why.map(function (w) {
        return '<li>' + esc(w) + '</li>'; }).join('') + '</ul></div>' +
    '<div class="stack">' +
      '<div class="callout warn"><div class="callout-title">Uncertainty</div>' +
        esc(o.rationale.uncertainty) + '</div>' +
      '<div class="callout"><div class="callout-title">' +
        'What would change this</div><ul class="reasons">' +
        o.rationale.what_would_change_this.map(function (w) {
          return '<li>' + esc(w) + '</li>'; }).join('') + '</ul></div>' +
    '</div></div></div>' +

  '<div class="block"><div class="block-head"><h2 class="block-title">' +
    'Not claimed as novel</h2></div><div class="callout"><p>' +
    esc(o.not_claimed) + '</p></div></div>' +

  '<div class="block"><div class="block-head"><h2 class="block-title">' +
    'Human decision</h2><span class="block-note">' +
    'a rejection is recorded and credits exactly zero</span></div>' +
    (decided
      ? '<div class="callout ' +
        (st.sequencing_status === 'APPROVED' ? 'good' : 'warn') + '">' +
        '<div class="callout-title">' + esc(st.sequencing_status) + '</div>' +
        '<p>Recorded against <strong>' + esc(st.sequencing_actor || 'unknown') +
        '</strong> in the tamper-evident ledger. ' +
        (st.sequencing_status === 'APPROVED'
          ? 'The plan is now the executed order and strategy.'
          : 'The arrival order is retained and no saving is credited.') +
        '</p><div class="btn-row" style="margin-top:10px">' +
        '<button class="btn btn-sm" data-go="washoff">' +
        'Continue to wash-off gate →</button></div></div>'
      : '<div class="callout"><p>ChangeLoop will not infer a decision. ' +
        'Approving commits the plan; rejecting keeps the arrival order. Both ' +
        'are recorded with the actor.</p>' +
        '<div class="btn-row" style="margin-top:12px">' +
        '<button class="btn btn-primary" data-act="approve">' +
        'Approve recommendation</button>' +
        '<button class="btn btn-danger" data-act="reject">' +
        'Reject, keep arrival order</button></div></div>') +
  '</div>' +

  '<div class="block">' + lotTable() + '</div></div>';
}

function optCard(x) {
  var blocked = !x.feasible;
  var cls = 'opt' + (x.is_recommended ? ' is-rec' : '') +
    (blocked ? ' is-blocked' : '');
  var badge = x.is_recommended
    ? '<span class="opt-badge rec">Recommended</span>'
    : blocked ? '<span class="opt-badge stop">Refused — infeasible</span>'
    : '<span class="opt-badge base">Baseline</span>';
  var d = x.delta_vs_baseline || {};
  var isBase = x.option_id === 'OPTION_A';

  return '<article class="' + cls + '"><div class="opt-head">' +
    '<div class="opt-tag">' + badge + '<span>' +
    esc(x.option_id.replace('_', ' ')) + '</span></div>' +
    '<h3 class="opt-title">' + esc(x.title) + '</h3>' +
    '<p class="opt-desc">' + esc(x.description) + '</p>' +
    '<div class="seq">' + seqChips(x.order) + '</div>' +
    '<div class="inline-tags"><span class="ev">' + esc(x.strategy.name) +
    '</span>' + (x.strategy_cost_inr > 0
      ? '<span class="small muted">lever cost ' + inr(x.strategy_cost_inr) +
        '</span>' : '') + '</div></div>' +
    '<div class="opt-rows">' +
      oRow('Freshwater intake', val(x.freshwater_intake_l, 'L'),
        isBase ? '' : deltaDown(d.freshwater_l, 'L')) +
      oRow('Stress weighted', val(x.stress_equivalent_l_eq, 'L-eq', 0),
        isBase ? '' : deltaDown(d.stress_l_eq, '', 0)) +
      oRow('Total salt load', val(x.total_salt_kg, 'kg'),
        isBase ? '' : deltaDown(d.salt_kg, 'kg')) +
      oRow('RO reject', val(x.ro_reject_l, 'L'), '') +
      oRow('Evaporator steam', val(x.mee_thermal_kwh, 'kWh'),
        isBase ? '' : deltaDown(d.mee_thermal_kwh, '')) +
      oRow('CO₂e', val(x.co2e_kg, 'kg'),
        isBase ? '' : deltaDown(d.co2e_kg, '')) +
      oRow('Total cost', inr(x.cost_inr),
        isBase ? '' : deltaDown(d.cost_inr, '', 0)) +
      oRow('Schedule lateness', val(x.total_late_h, 'h'), '') +
    '</div><div class="opt-foot">' +
      (blocked
        ? '<div class="violation"><span aria-hidden="true">✕</span><div>' +
          x.violations.map(esc).join('<br>') + '</div></div>'
        : '<p class="small muted">All hard constraints satisfied. Objective ' +
          inr(x.objective_inr) + ' of total consequence.</p>') +
    '</div></article>';
}

function oRow(k, v, d) {
  return '<div class="opt-row"><span class="k">' + esc(k) + '</span>' +
    '<span class="v">' + v + (d ? ' &nbsp;' + d : '') + '</span></div>';
}

function seqChips(order) {
  var lots = S.state.lots, arrival = S.state.arrival_order;
  return order.map(function (id, i) {
    var lot = null;
    for (var j = 0; j < lots.length; j++) {
      if (lots[j].lot_id === id) { lot = lots[j]; break; }
    }
    lot = lot || {};
    var moved = arrival[i] !== id;
    return (i ? '<span class="seq-arrow" aria-hidden="true">›</span>' : '') +
      '<span class="seq-chip' + (moved ? ' moved' : '') + '" title="' +
      esc(lot.shade_name + ' — ' + lot.depth_owf + '% owf') + '">' +
      '<span class="seq-swatch" style="background:' +
      esc(lot.shade_hex || '#999') + '"></span>' + esc(id) + '</span>';
  }).join('');
}

function lotTable() {
  return '<div class="block-head"><h2 class="block-title">Order book</h2>' +
    '<span class="block-note">' + ev('SIMULATED') +
    ' five-lot reference queue</span></div>' +
    '<div class="tbl-wrap"><table class="tbl"><thead><tr><th>Lot</th>' +
    '<th>Shade</th><th class="num">Depth</th><th class="num">Fabric</th>' +
    '<th class="num">Salt dose</th><th class="num">Wash-off</th>' +
    '<th class="num">Due</th><th>Priority</th></tr></thead><tbody>' +
    S.state.lots.map(function (l) {
      return '<tr><td class="row-label">' + esc(l.lot_id) +
        '<div class="row-sub">' + esc(l.buyer_ref) + '</div></td>' +
        '<td><span class="seq-chip"><span class="seq-swatch" style="background:' +
        esc(l.shade_hex) + '"></span>' + esc(l.shade_name) + '</span></td>' +
        '<td class="num">' + num(l.depth_owf, 2) + ' %owf</td>' +
        '<td class="num">' + num(l.fabric_kg, 0) + ' kg</td>' +
        '<td class="num">' + num(l.salt_dose_g_per_l, 1) + ' g/L</td>' +
        '<td class="num">' + num(l.washoff_baths, 0) + '</td>' +
        '<td class="num">' + num(l.due_h, 1) + ' h</td>' +
        '<td>' + (l.priority === 1
          ? '<span class="ev ev-ASSUMED">Firm ship date</span>'
          : '<span class="muted small">P' + l.priority + '</span>') +
        '</td></tr>';
    }).join('') + '</tbody></table></div>' +
    '<p class="small muted" style="margin-top:9px">Salt dose and wash-off ' +
    'baths are computed from shade depth, not looked up. The firm ship date on ' +
    'L-4412 is what makes the freshwater-minimal order infeasible.</p>';
}

/* ---------- 03 wash-off ---------- */
function viewWashoff() {
  var st = S.state, w = st.washoff;
  var faults = [
    ['none', 'No fault'], ['sensor_dropout', 'Probe dropout'],
    ['sensor_frozen', 'Probe frozen'], ['sensor_drift', 'Calibration drift'],
    ['colour_spike', 'Residual dye slug'],
    ['thermal_deficit', 'Bath under temperature']
  ];
  var faultBar = '<div class="block"><div class="block-head">' +
    '<h2 class="block-title">Inject a fault</h2><span class="block-note">' +
    'every one of these must force lockout, not a pass</span></div>' +
    '<div class="btn-row">' + faults.map(function (f) {
      return '<button class="btn btn-sm' +
        ((st.fault_mode || 'none') === f[0] ? ' btn-primary' : '') +
        '" data-fault="' + f[0] + '">' + esc(f[1]) + '</button>';
    }).join('') + '</div></div>';

  if (!w) {
    return head('Wash-off gate', 'When is the wash-off actually finished?') +
      '<div class="sec-body"><div class="state-msg">' +
      '<h3>No wash-off run yet</h3><p>Dyehouses run fixed-time wash-off ' +
      'because a fixed time is defensible. The schedule is padded for the ' +
      'deepest shade, so lots that clear early keep rinsing for nothing.</p>' +
      '<button class="btn btn-primary" data-fault="none">' +
      'Run wash-off telemetry</button></div>' + faultBar + '</div>';
  }

  var g = w.gate;
  var cls = g.state === 'AWAITING_HUMAN_RELEASE' ? 'await'
    : g.state === 'LOCKED_OUT' ? 'locked' : 'mon';

  return head('Wash-off gate — lot ' + w.lot_id,
    'Fail-closed release, never automatic',
    'Ending wash-off early on unfixed dye causes bleeding and a failed ' +
    'fastness test. The lot is then re-processed, which costs <em>more</em> ' +
    'water, steam and salt than the baths that were skipped. The gate is not ' +
    'bureaucracy — it is what keeps the saving real.'
  ) + '<div class="sec-body">' +

  '<div class="block"><div class="gate"><div class="gate-head">' +
    '<span class="gate-state ' + cls + '">' +
    esc(g.state.replace(/_/g, ' ')) + '</span>' +
    '<span class="gate-msg">' + esc(g.message) + '</span>' +
    '<span class="ev ev-SIMULATED">SIMULATED TELEMETRY</span></div>' +
    '<div class="checks">' + [
      ['conductivity_asymptote', 'Conductivity at release limit'],
      ['residual_colour_within_limit', 'Residual colour within limit'],
      ['fixation_temperature_held', 'Fixation temperature held'],
      ['dual_probe_agreement', 'Dual probes agree'],
      ['data_completeness', 'Telemetry complete']
    ].map(function (c) {
      var pass = g.checks[c[0]];
      return '<div class="check ' + (pass ? 'pass' : 'fail') + '">' +
        '<span class="check-mark" aria-hidden="true">' +
        (pass ? '✓' : '✕') + '</span><span class="check-name">' +
        esc(c[1]) + '</span><span class="check-detail">' +
        (pass ? 'pass' : 'fail') + '</span></div>';
    }).join('') + '</div>' +
    '<div style="padding:14px 16px;border-top:1px solid var(--rule)">' +
    '<p class="small muted"><strong>Release authority:</strong> ' +
    esc(g.authority) + ' &nbsp;·&nbsp; automatic_release = ' +
    '<span class="mono-sm">' + String(g.automatic_release) + '</span>, ' +
    'hardcoded, with no code path that sets it true.</p></div></div></div>' +

  '<div class="block"><div class="block-head"><h2 class="block-title">' +
    'Decay curve across wash-off baths</h2><span class="block-note">' +
    w.scheduled_baths + ' baths scheduled · endpoint ' +
    (w.endpoint_bath == null ? 'not reached' : 'bath ' + (w.endpoint_bath + 1)) +
    '</span></div>' + washoffChart(w) + '</div>' +

  '<div class="block"><div class="block-head"><h2 class="block-title">' +
    'Avoidable if released</h2><span class="block-note">' +
    'water integrated from the flow signal, not a per-minute constant' +
    '</span></div><div class="metrics">' +
    '<div class="metric"><div class="metric-label">Baths avoidable</div>' +
      '<div class="metric-value">' + val(w.baths_avoidable, '', 0) + '</div>' +
      '<div class="metric-foot">of ' + w.scheduled_baths + ' scheduled</div></div>' +
    '<div class="metric is-water"><div class="metric-label">Water</div>' +
      '<div class="metric-value">' + val(w.water_avoidable_l, 'L') + '</div>' +
      '<div class="metric-foot">integral of flow over skipped baths</div></div>' +
    '<div class="metric is-salt"><div class="metric-label">Carried salt</div>' +
      '<div class="metric-value">' + val(w.salt_avoidable_kg, 'kg') + '</div>' +
      '<div class="metric-foot">reduces evaporator duty</div></div>' +
    '<div class="metric is-energy"><div class="metric-label">Rinse heating</div>' +
      '<div class="metric-value">' + val(w.thermal_avoidable_kwh, 'kWh') +
      '</div><div class="metric-foot">confidence: ' + esc(w.confidence) +
      '</div></div></div>' +
    (g.state === 'AWAITING_HUMAN_RELEASE'
      ? '<div class="btn-row" style="margin-top:14px">' +
        '<button class="btn btn-primary" data-act="release">' +
        'Grant early release</button><button class="btn" data-act="norelease">' +
        'Decline, run full cycle</button></div>'
      : g.state === 'LOCKED_OUT'
        ? '<div class="callout stop" style="margin-top:14px">' +
          '<div class="callout-title">Release is locked out</div><p>' +
          esc(g.lockout_reason) + '</p><p>Try it anyway — the request is ' +
          'refused at the gate <em>and</em> at the API, and the refusal is ' +
          'written to the ledger.</p><div class="btn-row" style="margin-top:10px">' +
          '<button class="btn btn-danger" data-act="release">' +
          'Attempt release</button></div></div>'
        : '<p class="small muted" style="margin-top:12px">No endpoint was ' +
          'reached before the scheduled baths completed, so there is nothing ' +
          'to release. Short schedules on pale shades have no slack, and the ' +
          'system reports zero rather than manufacturing a saving.</p>') +
    (st.washoff_status === 'RELEASED'
      ? '<div class="callout good" style="margin-top:12px">' +
        '<div class="callout-title">Released</div>Granted by <strong>' +
        esc(st.washoff_actor) + '</strong> and recorded.</div>' : '') +
  '</div>' + faultBar +

  '<div class="block"><div class="block-head"><h2 class="block-title">' +
    'Release limits</h2><span class="block-note">' + ev('ASSUMED') +
    ' — must be loaded per site</span></div><dl class="defs">' +
    row('Conductivity', '<span class="num">' +
      num(st.release_limits.conductivity_release_ms_cm, 2) + '</span> mS/cm') +
    row('Residual colour', '<span class="num">' +
      num(st.release_limits.colour_release_admi, 0) + '</span> ADMI') +
    row('Fixation temperature', '<span class="num">' +
      num(st.release_limits.fixation_min_temp_c, 0) + '</span> °C minimum') +
    row('Basis', esc(st.release_limits.basis)) +
    row('If released wrongly', esc(st.release_limits.failure_consequence)) +
    '</dl></div></div>';
}

function washoffChart(w) {
  var W = 760, H = 240, L = 56, R = 20, T = 18, B = 42;
  var n = w.scheduled_baths, byBath = [], i;
  for (i = 0; i < n; i++) {
    var cs = [], cols = [];
    w.samples.forEach(function (x) {
      if (x.bath_index !== i) return;
      if (x.conductivity_ms_cm != null) cs.push(x.conductivity_ms_cm);
      if (x.residual_colour_admi != null) cols.push(x.residual_colour_admi);
    });
    byBath.push({
      cond: cs.length ? cs.reduce(function (a, b) { return a + b; }, 0) / cs.length : null,
      colour: cols.length ? Math.max.apply(null, cols) : null
    });
  }
  var maxC = 1, maxCol = 1;
  byBath.forEach(function (b) {
    if (b.cond > maxC) maxC = b.cond;
    if (b.colour > maxCol) maxCol = b.colour;
  });
  function x(k) { return L + (n <= 1 ? 0 : (W - L - R) * k / (n - 1)); }
  function yC(v) { return T + (H - T - B) * (1 - v / maxC); }
  function yCol(v) { return T + (H - T - B) * (1 - v / maxCol); }

  function line(key, scale) {
    var d = [], first = true;
    byBath.forEach(function (b, k) {
      if (b[key] == null) return;
      d.push((first ? 'M' : 'L') + x(k).toFixed(1) + ',' + scale(b[key]).toFixed(1));
      first = false;
    });
    return d.join(' ');
  }

  var limitY = yC(S.state.release_limits.conductivity_release_ms_cm);
  var savedFrom = w.baths_avoidable > 0 ? x(n - w.baths_avoidable) : null;

  return '<div class="chart"><svg viewBox="0 0 ' + W + ' ' + H + '" ' +
    'role="img" aria-label="Conductivity and residual colour decay across ' +
    'wash-off baths">' +
    [0.25, 0.5, 0.75].map(function (f) {
      var y = T + (H - T - B) * f;
      return '<line class="ch-grid" x1="' + L + '" x2="' + (W - R) +
        '" y1="' + y + '" y2="' + y + '"/>';
    }).join('') +
    (savedFrom != null
      ? '<rect class="ch-saved" x="' + savedFrom + '" y="' + T + '" width="' +
        (W - R - savedFrom) + '" height="' + (H - T - B) + '"/>' +
        '<text class="ch-tick" x="' + (savedFrom + 8) + '" y="' + (T + 14) +
        '" style="fill:var(--good)">' + w.baths_avoidable +
        ' bath(s) avoidable — ' + num(w.water_avoidable_l, 0) + ' L</text>'
      : '') +
    '<line class="ch-limit" x1="' + L + '" x2="' + (W - R) + '" y1="' +
      limitY + '" y2="' + limitY + '"/>' +
    '<text class="ch-tick" x="' + (L + 4) + '" y="' + (limitY - 5) +
      '" style="fill:var(--good)">conductivity release limit</text>' +
    '<path class="ch-line-cond" d="' + line('cond', yC) + '"/>' +
    '<path class="ch-line-colour" d="' + line('colour', yCol) + '"/>' +
    byBath.map(function (b, k) {
      return (b.cond == null ? '' : '<circle class="ch-pt" cx="' + x(k) +
        '" cy="' + yC(b.cond) + '" r="3.5" stroke="var(--water)"/>') +
        (b.colour == null ? '' : '<circle class="ch-pt" cx="' + x(k) +
        '" cy="' + yCol(b.colour) + '" r="3.5" stroke="var(--salt)"/>');
    }).join('') +
    '<line class="ch-axis" x1="' + L + '" x2="' + (W - R) + '" y1="' +
      (H - B) + '" y2="' + (H - B) + '"/>' +
    '<line class="ch-axis" x1="' + L + '" x2="' + L + '" y1="' + T +
      '" y2="' + (H - B) + '"/>' +
    byBath.map(function (b, k) {
      return '<text class="ch-tick" text-anchor="middle" x="' + x(k) +
        '" y="' + (H - B + 16) + '">' + (k + 1) + '</text>';
    }).join('') +
    '<text class="ch-tick" text-anchor="middle" x="' + ((L + W - R) / 2) +
      '" y="' + (H - 6) + '">wash-off bath number</text>' +
    '<text class="ch-tick" x="4" y="' + (T + 8) + '">' + num(maxC, 1) +
      ' mS/cm</text>' +
    '<text class="ch-tick" x="4" y="' + (H - B - 2) + '">0</text></svg>' +
    '<div class="legend"><span class="legend-item">' +
    '<span class="legend-swatch" style="background:var(--water)"></span>' +
    'Conductivity (salt washout)</span><span class="legend-item">' +
    '<span class="legend-swatch" style="background:var(--salt)"></span>' +
    'Residual colour (ADMI)</span><span class="legend-item">' +
    '<span class="legend-swatch" style="background:var(--good)"></span>' +
    'Release limit</span></div></div>';
}

/* ---------- 04 consequence ---------- */
function viewConsequence() {
  var i = S.state.impact;
  var base = i.baseline_scenario, ach = i.achieved_scenario;

  return head('Consequence', 'From a scheduling decision to a stack of coal',
    'Every box below is computed by the same code path for both the baseline ' +
    'and the achieved case, so the difference between them is a real ' +
    'difference and not two models disagreeing. Click Trace on any row to see ' +
    'its formula and coefficients.'
  ) + '<div class="sec-body">' +

  '<div class="block"><div class="block-head"><h2 class="block-title">' +
    'Consequence chain — achieved case</h2><span class="block-note">' +
    ev('MODELLED') + '</span></div>' + chainDiagram(ach) + '</div>' +

  '<div class="block"><div class="block-head"><h2 class="block-title">' +
    'Attribution — which decision produced what</h2>' +
    '<span class="block-note">an unapproved decision contributes exactly zero' +
    '</span></div><div class="tbl-wrap"><table class="tbl"><thead><tr>' +
    '<th>Decision</th><th>Status</th><th class="num">Water avoided</th>' +
    '<th class="num">Salt avoided</th></tr></thead><tbody>' +
    '<tr><td class="row-label">Lot sequence &amp; process strategy' +
      '<div class="row-sub">changeover burden and rinse strategy — ' +
      'process demand is never claimed</div></td><td>' +
      statusTag(i.sequencing_status) + '</td><td class="num">' +
      num(i.sequencing_water_avoided_l, 0) + ' L</td><td class="num">' +
      num(i.sequencing_salt_avoided_kg, 2) + ' kg</td></tr>' +
    '<tr><td class="row-label">Wash-off early release' +
      '<div class="row-sub">released baths only, integrated from flow</div>' +
      '</td><td>' + statusTag(i.washoff_status) + '</td><td class="num">' +
      num(i.washoff_water_avoided_l, 0) + ' L</td><td class="num">' +
      num(i.washoff_salt_avoided_kg, 2) + ' kg</td></tr>' +
    '</tbody></table></div>' +
    (i.notes && i.notes.length
      ? '<div class="callout" style="margin-top:12px">' +
        '<div class="callout-title">Accounting notes</div><ul class="reasons">' +
        i.notes.map(function (n) { return '<li>' + esc(n) + '</li>'; }).join('') +
        '</ul></div>' : '') + '</div>' +

  '<div class="block"><div class="block-head"><h2 class="block-title">' +
    'Baseline against achieved</h2></div><div class="tbl-wrap">' +
    '<table class="tbl"><thead><tr><th>Quantity</th><th class="num">Baseline' +
    '</th><th class="num">Achieved</th><th class="num">Avoided</th>' +
    '<th class="num">%</th><th></th></tr></thead><tbody>' +
    [['Freshwater intake', 'L', i.baseline_freshwater_intake_l,
      i.achieved_freshwater_intake_l, i.freshwater_avoided_l,
      'freshwater_avoided_l'],
     ['Total salt load', 'kg', i.baseline_salt_kg, i.achieved_salt_kg,
      i.salt_avoided_kg, null],
     ['RO reject volume', 'L', i.baseline_reject_l, i.achieved_reject_l,
      i.reject_avoided_l, null],
     ['Evaporator steam', 'kWh', i.baseline_mee_thermal_kwh,
      i.achieved_mee_thermal_kwh, i.mee_thermal_avoided_kwh,
      'mee_thermal_avoided_kwh'],
     ['CO₂e', 'kg', i.baseline_co2e_kg, i.achieved_co2e_kg,
      i.co2e_avoided_kg, 'co2e_avoided_kg'],
     ['Total cost', '₹', i.baseline_cost_inr, i.achieved_cost_inr,
      i.cost_avoided_inr, 'cost_avoided_inr']
    ].map(function (r) {
      var pct = r[2] > 0 ? (r[4] / r[2] * 100) : 0;
      return '<tr><td class="row-label">' + r[0] +
        ' <span class="muted small">' + esc(r[1]) + '</span></td>' +
        '<td class="num">' + num(r[2], 0) + '</td><td class="num">' +
        num(r[3], 0) + '</td><td class="num">' + deltaDown(r[4], '', 0) +
        '</td><td class="num">' + num(pct, 1) + '%</td><td>' +
        (r[5] ? '<button class="btn btn-sm btn-ghost" data-trace="' + r[5] +
          '">Trace</button>' : '') + '</td></tr>';
    }).join('') +
    '<tr><td class="row-label">Stress-weighted freshwater</td>' +
      '<td class="num">—</td><td class="num">—</td>' +
      '<td class="num">' + deltaDown(i.stress_equivalent_avoided_l_eq, 'L-eq', 0) +
      '</td><td class="num">&#215;' + num(i.stress_weight, 2) + '</td>' +
      '<td><button class="btn btn-sm btn-ghost" ' +
      'data-trace="stress_equivalent_avoided_l_eq">Trace</button></td></tr>' +
    '</tbody></table></div></div>' +

  '<div class="block"><div class="block-head"><h2 class="block-title">' +
    'Accounting invariants</h2><span class="block-note">' +
    (i.validation.all_pass ? 'all ' + i.validation.checks.length + ' pass'
      : i.validation.failed_count + ' FAILED') + '</span></div>' +
    '<div class="gate"><div class="checks">' +
    i.validation.checks.map(function (c) {
      return '<div class="check ' + (c.pass ? 'pass' : 'fail') + '">' +
        '<span class="check-mark" aria-hidden="true">' +
        (c.pass ? '✓' : '✕') + '</span><span class="check-name">' +
        esc(c.rule) + '</span><span class="check-detail">' + esc(c.detail) +
        '</span></div>';
    }).join('') + '</div></div>' +
    '<p class="small muted" style="margin-top:9px">These run on every read of ' +
    'the ledger. If any one fails, the impact figure is not fit to display and ' +
    'the product says so rather than rendering it anyway.</p></div>' +

  '<div class="block"><div class="block-head"><h2 class="block-title">' +
    'Which constraint binds</h2></div><div class="grid-2">' +
    bindCard('Baseline', base) + bindCard('Achieved', ach) +
    '</div></div></div>';
}

function bindCard(label, sc) {
  if (!sc) return '';
  var salt = sc.zld.binding_constraint === 'SALT_BALANCE';
  return '<div class="callout ' + (salt ? 'insight' : '') + '">' +
    '<div class="callout-title">' + esc(label) + ' — ' +
    esc(sc.zld.binding_constraint.replace('_', ' ')) + '</div><dl class="defs">' +
    row('Effluent TDS', '<span class="num">' +
      num(sc.zld.effluent_tds_mg_l, 0) + '</span> mg/L') +
    row('RO recovery', '<span class="num">' +
      num(sc.zld.ro_recovery_frac * 100, 1) + '</span>%') +
    row('Reject TDS', '<span class="num">' +
      num(sc.zld.reject_tds_mg_l, 0) + '</span> mg/L') +
    '</dl><p class="small" style="margin-top:9px">' + (salt
      ? 'Salt-limited. Reducing salt reduces evaporator duty proportionally; ' +
        'reducing water alone would not.'
      : 'Hydraulically limited. Here the membrane array, not the salt balance, ' +
        'sets the reject volume.') + '</p></div>';
}

function statusTag(s) {
  var good = s === 'APPROVED' || s === 'RELEASED';
  var bad = s === 'REJECTED' || s === 'LOCKED_OUT';
  return '<span class="ev ' + (good ? 'ev-MEASURED' : bad ? 'ev-ASSUMED' : '') +
    '">' + esc(String(s).replace(/_/g, ' ')) + '</span>';
}

/* the signature diagram */
function chainDiagram(sc) {
  if (!sc) return '';
  var W = 980, H = 300;
  var boxes = [
    { x: 8, y: 92, w: 132, h: 76, label: 'Dyehouse',
      v: num(sc.water.process_demand_l, 0), u: 'L water demand',
      note: 'lot order + strategy' },
    { x: 172, y: 92, w: 132, h: 76, label: 'Effluent',
      v: num(sc.salt.total_salt_kg, 1), u: 'kg salt',
      note: num(sc.zld.effluent_tds_mg_l, 0) + ' mg/L TDS' },
    { x: 336, y: 92, w: 132, h: 76, label: 'Reverse osmosis',
      v: num(sc.zld.ro_recovery_frac * 100, 1), u: '% recovery',
      note: sc.zld.binding_constraint === 'SALT_BALANCE' ? 'salt-limited'
        : 'hydraulic limit', accent: true },
    { x: 500, y: 16, w: 132, h: 72, label: 'Permeate reused',
      v: num(sc.water.permeate_reuse_l, 0), u: 'L back to process',
      note: 'displaces fresh' },
    { x: 500, y: 172, w: 132, h: 72, label: 'Reject to evaporator',
      v: num(sc.zld.reject_l, 0), u: 'L', note: 'set by salt mass',
      accent: true },
    { x: 664, y: 172, w: 132, h: 72, label: 'Multi-effect evaporator',
      v: num(sc.zld.mee_thermal_kwh, 0), u: 'kWh thermal',
      note: '179 kWh/m³ derived' },
    { x: 828, y: 172, w: 136, h: 72, label: 'Boiler emissions',
      v: num(sc.carbon.mee_thermal_co2e_kg, 0), u: 'kg CO₂e',
      note: 'coal-fired steam' },
    { x: 828, y: 16, w: 136, h: 72, label: 'Freshwater makeup',
      v: num(sc.water.freshwater_intake_l, 0), u: 'L from basin',
      note: num(sc.stress_equivalent_l_eq, 0) + ' L-eq' }
  ];

  function box(b) {
    return '<rect class="' + (b.accent ? 'dg-box-accent' : 'dg-box') +
      '" x="' + b.x + '" y="' + b.y + '" width="' + b.w + '" height="' +
      b.h + '" rx="2"/>' +
      '<text class="dg-label" x="' + (b.x + 10) + '" y="' + (b.y + 18) + '">' +
      esc(b.label) + '</text>' +
      '<text class="dg-value" x="' + (b.x + 10) + '" y="' + (b.y + 40) + '">' +
      esc(b.v) + '</text>' +
      '<text class="dg-unit" x="' + (b.x + 10) + '" y="' + (b.y + 53) + '">' +
      esc(b.u) + '</text>' +
      '<text class="dg-note" x="' + (b.x + 10) + '" y="' + (b.y + 67) + '">' +
      esc(b.note) + '</text>';
  }
  function arrow(x1, y1, x2, y2, cls, ac) {
    return '<path class="' + cls + '" d="M' + x1 + ',' + y1 + ' L' + x2 + ',' +
      y2 + '"/><path class="' + ac + '" d="M' + x2 + ',' + y2 +
      ' l-6,-3.2 l0,6.4 z"/>';
  }
  function elbow(x1, y1, x2, y2, cls, ac) {
    return '<path class="' + cls + '" d="M' + x1 + ',' + y1 + ' H' +
      ((x1 + x2) / 2) + ' V' + y2 + ' H' + (x2 - 7) + '"/>' +
      '<path class="' + ac + '" d="M' + x2 + ',' + y2 +
      ' l-6,-3.2 l0,6.4 z"/>';
  }

  return '<div class="diagram-wrap"><svg viewBox="0 0 ' + W + ' ' + H + '" ' +
    'role="img" aria-label="Consequence chain from dyehouse water demand ' +
    'through reverse osmosis to boiler emissions">' +
    arrow(140, 130, 165, 130, 'dg-flow-water', 'dg-arrow-w') +
    arrow(304, 130, 329, 130, 'dg-flow-salt', 'dg-arrow-s') +
    elbow(468, 120, 500, 52, 'dg-flow-water', 'dg-arrow-w') +
    elbow(468, 140, 500, 208, 'dg-flow-salt', 'dg-arrow-s') +
    arrow(632, 208, 657, 208, 'dg-flow-salt', 'dg-arrow-s') +
    arrow(796, 208, 821, 208, 'dg-flow-energy', 'dg-arrow-e') +
    elbow(632, 52, 828, 52, 'dg-flow-water', 'dg-arrow-w') +
    boxes.map(box).join('') +
    '<text class="dg-note" x="8" y="286">Water</text>' +
    '<line class="dg-flow-water" x1="48" y1="282" x2="86" y2="282"/>' +
    '<text class="dg-note" x="98" y="286">Salt-bearing stream</text>' +
    '<line class="dg-flow-salt" x1="212" y1="282" x2="250" y2="282"/>' +
    '<text class="dg-note" x="262" y="286">Energy / emissions</text>' +
    '<line class="dg-flow-energy" x1="382" y1="282" x2="420" y2="282"/>' +
    '<text class="dg-note" x="440" y="286">Closed loop: freshwater makeup ' +
    'equals what the evaporator destroyed.</text></svg></div>';
}

/* ---------- 05 evidence ---------- */
function viewEvidence() {
  if (!S.evidence) {
    api('/api/evidence').then(function (d) {
      S.evidence = d; if (S.view === 'evidence') render();
    });
    return head('Evidence', 'Every coefficient, with its origin') +
      '<div class="sec-body"><div class="state-msg"><span class="spinner">' +
      '</span>Loading registry&hellip;</div></div>';
  }
  var e = S.evidence, sum = e.summary;

  return head('Evidence', 'Every coefficient, with its origin',
    'No number may be used in a calculation unless it is registered with a ' +
    'unit, a derivation or source, and an evidence class. Nothing in this ' +
    'prototype is <strong>MEASURED</strong> — that class exists so a ' +
    'pilot can promote values into it.'
  ) + '<div class="sec-body">' +

  '<div class="block"><div class="metrics">' +
    Object.keys(sum).map(function (k) {
      return '<div class="metric"><div class="metric-label">' + ev(k) +
        '</div><div class="metric-value">' + val(sum[k], '', 0) +
        '</div><div class="metric-foot">coefficients</div></div>';
    }).join('') +
    '<div class="metric"><div class="metric-label">' + ev('MEASURED') +
    '</div><div class="metric-value">' + val(0, '', 0) +
    '</div><div class="metric-foot">nothing here is metered</div></div>' +
  '</div></div>' +

  '<div class="block"><div class="block-head"><h2 class="block-title">' +
    'Coefficient registry</h2><span class="block-note">' +
    'core/factors.py — the single source of truth</span></div>' +
    '<div class="tbl-wrap"><table class="tbl"><thead><tr><th>Coefficient</th>' +
    '<th class="num">Value</th><th>Unit</th><th>Class</th><th>Basis</th>' +
    '</tr></thead><tbody>' + e.coefficients.map(function (c) {
      return '<tr><td class="row-label">' + esc(c.label) +
        '<div class="row-sub mono-sm">' + esc(c.key) + '</div></td>' +
        '<td class="num">' + num(c.value, c.value < 1 ? 5 : 2) + '</td>' +
        '<td class="mono-sm">' + esc(c.unit) + '</td><td>' + ev(c.evidence) +
        (c.tunable ? '' : '<div class="row-sub">fixed</div>') + '</td>' +
        '<td class="small">' + esc(c.basis) + '</td></tr>';
    }).join('') + '</tbody></table></div></div>' +

  '<div class="block"><div class="block-head"><h2 class="block-title">' +
    'Basin stress weighting — honesty boundary</h2>' +
    '<span class="block-note">' + ev('ASSUMED') + '</span></div>' +
    '<div class="callout warn"><div class="callout-title">' +
    'Read this before quoting any L-eq figure</div><dl class="defs">' +
    row('Formula', '<span class="formula">' +
      esc(e.basin_methodology.formula) + '</span>') +
    row('What this is', esc(e.basin_methodology.what_this_is)) +
    row('What it is <strong>not</strong>',
      esc(e.basin_methodology.what_this_is_not)) +
    row('Before external use', esc(e.basin_methodology.before_external_use)) +
    '</dl></div></div>' +

  '<div class="block"><div class="block-head"><h2 class="block-title">' +
    'Claim register</h2><span class="block-note">' +
    'every external claim, with its evidence level and safe wording' +
    '</span></div><div class="tbl-wrap"><table class="tbl"><thead><tr>' +
    '<th>Claim</th><th>Level</th><th>Safe wording</th></tr></thead><tbody>' +
    e.claim_register.claims.map(function (c) {
      return '<tr><td>' + esc(c.claim) + '</td><td><span class="ev">' +
        esc(c.level) + '</span><div class="row-sub">' +
        esc(e.claim_register.evidence_levels[c.level] || '') + '</div></td>' +
        '<td class="small muted">' + esc(c.safe_wording) + '</td></tr>';
    }).join('') + '</tbody></table></div>' +
    '<div class="callout stop" style="margin-top:12px">' +
    '<div class="callout-title">Forbidden wordings</div><ul class="reasons">' +
    e.claim_register.forbidden_wordings.map(function (f) {
      return '<li>' + esc(f) + '</li>'; }).join('') + '</ul></div></div>' +
  '</div>';
}

/* ---------- 06 ledger ---------- */
function viewLedger() {
  var st = S.state, integ = st.ledger_integrity, recs = st.ledger_records || [];

  return head('Ledger', 'Tamper-evident decision record',
    'An append-only hash chain with a keyed MAC over each link. It answers ' +
    'one question well: can a record have been edited after the fact? Under a ' +
    'polluter-pays regime that is the question that matters.'
  ) + '<div class="sec-body">' +

  '<div class="block"><div class="callout ' +
    (integ.intact ? 'good' : 'stop') + '"><div class="callout-title">' +
    (integ.intact ? 'Chain intact' : 'CHAIN BROKEN') + '</div><p>' +
    esc(integ.detail) + ' <span class="num">' + integ.records +
    '</span> records verified by recomputing every link from its contents.</p>' +
    '<p class="hash" style="margin-top:7px">head: ' + esc(integ.head_hash) +
    '</p><div class="btn-row" style="margin-top:10px">' +
    '<button class="btn btn-sm" data-act="verify">Re-verify chain now</button>' +
    '</div></div></div>' +

  '<div class="block"><div class="block-head"><h2 class="block-title">' +
    'What this is, and what it is not</h2></div><div class="grid-2">' +
    '<div class="callout good"><div class="callout-title">What it proves</div>' +
      '<p>' + esc(integ.key.proves) + '</p>' +
      '<p class="small muted" style="margin-top:7px">Mechanism: ' +
      esc(integ.key.mechanism) + '</p></div>' +
    '<div class="callout warn"><div class="callout-title">' +
      'What it does not prove</div><p>' + esc(integ.key.does_not_prove) +
      '</p><p style="margin-top:7px"><strong>Not a blockchain.</strong> ' +
      esc(integ.key.not_a_blockchain) + '</p>' +
      '<p class="small muted" style="margin-top:7px">Key source: ' +
      esc(integ.key.source) + (integ.key.is_secret ? ''
        : ' — a published constant, not a secret. Anything else would be ' +
          'security theatre.') + '</p></div></div></div>' +

  '<div class="block"><div class="block-head"><h2 class="block-title">' +
    'Records</h2><span class="block-note">' +
    'newest first · refusals and rejections included</span></div>' +
    '<div class="tbl-wrap"><div class="chain">' + (recs.length
      ? recs.map(function (r) {
          return '<div class="chain-row"><div class="chain-seq">#' + r.seq +
            '</div><div><div class="chain-action">' + esc(r.action) +
            '</div><div class="chain-detail">' + esc(r.detail) +
            '</div></div><div class="chain-meta">' + esc(r.actor) + '<br>' +
            esc(r.timestamp) + '<br><span class="hash">' +
            esc(String(r.record_hash).slice(0, 16)) + '…</span></div></div>';
        }).join('')
      : '<div class="state-msg">No records yet.</div>') +
    '</div></div></div>' +

  '<div class="block"><div class="block-head"><h2 class="block-title">Export' +
    '</h2><span class="block-note">the same ledger the screens read' +
    '</span></div><div class="callout"><p>The export carries the impact ' +
    'figures, the full coefficient registry, the basin methodology ' +
    'disclosure and the chain verification, plus a SHA-256 over the whole ' +
    'payload.</p><div class="btn-row" style="margin-top:11px">' +
    '<button class="btn" data-act="export">View export JSON</button>' +
    '<button class="btn" data-act="download">Download</button></div></div>' +
  '</div></div>';
}

/* ---------- 07 business case ---------- */
function viewCase() {
  var bc = S.businessCase;
  var fields = [
    ['lots_per_year', 'Dye lots per year', 9000],
    ['freshwater_avoided_per_lot_l', 'Freshwater avoided per lot (L)', 1108],
    ['salt_avoided_per_lot_kg', 'Salt avoided per lot (kg)', 12.5],
    ['freshwater_cost_inr_per_m3', 'Freshwater cost (₹/m³)', 45],
    ['recycled_water_cost_inr_per_m3', 'Recycled water cost (₹/m³)', 135],
    ['steam_cost_inr_per_kwh_th', 'Steam cost (₹/kWh thermal)', 2.4],
    ['salt_cost_inr_per_kg', 'Salt cost (₹/kg)', 9],
    ['implementation_cost_inr', 'Implementation cost (₹)', 450000],
    ['annual_subscription_inr', 'Annual subscription (₹)', 240000]
  ];

  return head('Business case', 'Your numbers, not ours',
    'ChangeLoop refuses to compute a business case from assumed values. The ' +
    'default state of this screen is a request for your tariffs, because a ' +
    'projection built on a vendor’s assumptions is not a business case.'
  ) + '<div class="sec-body">' +

  '<div class="block"><div class="block-head"><h2 class="block-title">' +
    'Site inputs</h2><span class="block-note">' +
    'pre-filled with the reference figures — replace with yours' +
    '</span></div><div class="form-grid">' + fields.map(function (f) {
      return '<div class="field"><label for="bc_' + f[0] + '">' + esc(f[1]) +
        '</label><input id="bc_' + f[0] + '" type="number" step="any" min="0" ' +
        'value="' + f[2] + '"></div>';
    }).join('') + '</div><div class="btn-row" style="margin-top:14px">' +
    '<button class="btn btn-primary" data-act="calc-case">Calculate</button>' +
    '</div></div>' +

  (bc && bc.status === 'CALCULATED' ? caseResult(bc)
    : bc ? '<div class="callout stop"><div class="callout-title">' +
      esc(String(bc.status).replace(/_/g, ' ')) + '</div>' +
      esc(bc.notice || '') + '</div>' : '') +

  '<div class="block"><div class="block-head"><h2 class="block-title">' +
    'Who buys, who uses, who pays</h2></div><div class="tbl-wrap">' +
    '<table class="tbl"><thead><tr><th>Role</th><th>What they care about</th>' +
    '<th>Their objection, and the answer</th></tr></thead><tbody>' +
    [['Unit owner — buys and pays',
      'Survival under ZLD compliance cost. Steam and salt are real cash.',
      '"Show me it works on my shift before I pay." Answered by shadow mode.'],
     ['Production planner — uses it',
      'Not missing a ship date. Water is not their metric.',
      '"Will this make me late?" Answered by hard constraints that a water ' +
      'saving cannot override.'],
     ['Quality manager — holds the veto',
      'No off-shade lot, ever.',
      '"Early release risks my fastness test." Answered by the fail-closed gate.'],
     ['CETP / ZLD operator — benefits',
      'Lower evaporator load and a steadier inlet TDS.',
      '"I do not control the dyehouse." That gap is exactly what this closes.'],
     ['Buyer / brand — pulls demand',
      'Scope 3 water and carbon in their supply chain.',
      '"Can you evidence it?" Answered by the traceable ledger and export.']
    ].map(function (r) {
      return '<tr><td class="row-label">' + esc(r[0]) + '</td><td>' +
        esc(r[1]) + '</td><td class="small muted">' + esc(r[2]) + '</td></tr>';
    }).join('') + '</tbody></table></div></div></div>';
}

function caseResult(bc) {
  var q = bc.annual_quantities, b = bc.benefit_breakdown_inr;
  return '<div class="block"><div class="block-head"><h2 class="block-title">' +
    'Result</h2><span class="block-note">' + ev('MODELLED') +
    ' from your inputs</span></div><div class="metrics">' +
    '<div class="metric is-good"><div class="metric-label">' +
      'Annual net benefit</div><div class="metric-value">' +
      inr(bc.annual_net_benefit_inr) + '</div>' +
      '<div class="metric-foot">after subscription</div></div>' +
    '<div class="metric"><div class="metric-label">Payback</div>' +
      '<div class="metric-value">' + val(bc.payback_years, 'yr') + '</div>' +
      '<div class="metric-foot">on ' + inr(bc.implementation_cost_inr) +
      ' capex</div></div>' +
    '<div class="metric"><div class="metric-label">3-year NPV at 12%</div>' +
      '<div class="metric-value">' + inr(bc.npv_3yr_at_12pct_inr) + '</div>' +
      '<div class="metric-foot">ROI ' + num(bc.annual_roi_percent, 0) +
      '% per year</div></div>' +
    '<div class="metric is-energy"><div class="metric-label">' +
      'Evaporator steam avoided</div><div class="metric-value">' +
      val(q.evaporator_steam_avoided_kwh_th / 1000, 'MWh') + '</div>' +
      '<div class="metric-foot">per year, thermal</div></div></div>' +
    '<div class="grid-2" style="margin-top:16px">' +
    '<div><div class="block-head"><h3 class="block-title">' +
      'Benefit breakdown</h3></div><div class="tbl-wrap"><table class="tbl">' +
      '<tbody>' + Object.keys(b).map(function (k) {
        return '<tr><td>' + esc(k.replace(/_/g, ' ')) + '</td>' +
          '<td class="num">' + inr(b[k]) + '</td></tr>';
      }).join('') + '<tr><td class="row-label">Gross annual</td>' +
      '<td class="num row-label">' + inr(bc.annual_gross_benefit_inr) +
      '</td></tr></tbody></table></div>' +
      '<p class="small muted" style="margin-top:8px">The water line is priced ' +
      'at your <strong>recycled</strong> rate, not your freshwater rate. In a ' +
      'closed loop the litre you avoid is the expensive one you would ' +
      'otherwise have had to treat.</p></div>' +
    '<div><div class="block-head"><h3 class="block-title">Sensitivity</h3>' +
      '</div><div class="tbl-wrap"><table class="tbl"><thead><tr>' +
      '<th>Scenario</th><th class="num">Net</th><th class="num">Payback</th>' +
      '</tr></thead><tbody>' + bc.sensitivity.map(function (s) {
        return '<tr><td>' + esc(s.scenario) + '</td><td class="num">' +
          inr(s.annual_net_inr) + '</td><td class="num">' +
          num(s.payback_years, 2) + ' yr</td></tr>';
      }).join('') + '</tbody></table></div>' +
      '<div class="callout" style="margin-top:12px">' +
      '<div class="callout-title">Deliberately excluded</div>' +
      '<ul class="reasons">' + bc.excluded_from_this_calculation.map(
        function (x) { return '<li>' + esc(x) + '</li>'; }).join('') +
      '</ul></div></div></div></div>';
}

/* ---------- 08 scale & proof ---------- */
function viewScale() {
  if (!S.ablation) {
    api('/api/ablation?mode=' + encodeURIComponent(S.mode))
      .then(function (d) {
        S.ablation = d; if (S.view === 'scale') render(); });
  }
  if (!S.sensitivity) {
    api('/api/sensitivity').then(function (d) {
      S.sensitivity = d; if (S.view === 'scale') render(); });
  }
  if (!S.modeCompare) {
    api('/api/modes/compare').then(function (d) {
      S.modeCompare = d; if (S.view === 'scale') render(); });
  }
  if (!S.cluster) {
    api('/api/cluster-projection').then(function (d) {
      S.cluster = d; if (S.view === 'scale') render(); });
  }
  if (!S.pilot) {
    api('/api/pilot').then(function (d) {
      S.pilot = d; if (S.view === 'scale') render(); });
  }
  var ab = S.ablation, se = S.sensitivity, mc = S.modeCompare,
      cl = S.cluster, pl = S.pilot;

  return head('Scale & proof', 'Does the architecture earn its complexity?',
    'Three self-critical tests, all reproducible from the API: remove each ' +
    'layer and measure what is lost; move every coefficient to its bounds and ' +
    'see whether the decision survives; and change the binding constraint to ' +
    'check the optimiser is responding rather than returning a fixed answer.'
  ) + '<div class="sec-body">' +

  '<div class="block"><div class="block-head"><h2 class="block-title">' +
    'Ablation — remove one layer at a time</h2>' +
    '<span class="block-note">' + ev('MODELLED') +
    ' · under ' + esc(modeName()) +
    ' · /api/ablation</span></div>' + (ab
    ? '<div class="tbl-wrap"><table class="tbl"><thead><tr><th>Variant</th>' +
      '<th class="num">Freshwater reported</th>' +
      '<th class="num">vs full</th><th class="num">Steam</th>' +
      '<th class="num">Breach</th><th>Capability lost</th>' +
      '</tr></thead><tbody>' +
      ab.variants.map(function (v) {
        var cls = v.variant === 'full' ? ' class="is-rec"'
          : v.firm_breaches > 0 ? ' class="is-blocked"' : '';
        return '<tr' + cls + '><td class="row-label">' + esc(v.label) +
          '</td><td class="num">' + num(v.freshwater_avoided_l, 0) + ' L</td>' +
          '<td class="num">' + (v.reported_vs_full_pct == null ? '—'
            : num(v.reported_vs_full_pct, 0) + '%' + (v.overstates
              ? ' <span class="ev ev-ASSUMED">over-reports</span>'
              : '')) + '</td>' +
          '<td class="num">' + num(v.mee_thermal_avoided_kwh, 0) + ' kWh</td>' +
          '<td class="num">' + (v.firm_breaches > 0
            ? '<span class="ev ev-ASSUMED">' + v.firm_breaches + '</span>'
            : '0') + '</td><td class="small muted">' +
          esc(v.capability_lost) + (v.overstatement_note
            ? '<div class="row-sub" style="color:var(--stop)">' +
              esc(v.overstatement_note) + '</div>' : '') + '</td></tr>';
      }).join('') + '</tbody></table></div>' +
      '<div class="callout insight" style="margin-top:12px">' +
      '<div class="callout-title">What this proves</div><p>' +
      esc(ab.conclusion) + '</p>' +
      '<p class="small muted" style="margin-top:8px">Change the ' +
      'binding constraint in the masthead and this study re-runs under ' +
      'that mode. A layer can be inert under one price set and decisive ' +
      'under another, and the table says which.</p></div>'
    : '<div class="state-msg"><span class="spinner"></span>' +
      'Running ablation&hellip;</div>') + '</div>' +

  '<div class="block"><div class="block-head"><h2 class="block-title">' +
    'Sensitivity — are the assumptions load-bearing?</h2>' +
    '<span class="block-note">' + ev('DERIVED') +
    ' · /api/sensitivity</span></div>' + (se
    ? '<div class="callout ' + (se.decision_robust ? 'good' : 'warn') + '">' +
      '<div class="callout-title">' + (se.decision_robust
        ? 'Decision robust across the whole sweep'
        : 'Decision sensitive in ' + se.recommendation_changed_count +
          ' sweep runs') + '</div><p>' + esc(se.interpretation) + '</p></div>' +
      '<div class="tbl-wrap" style="margin-top:12px"><table class="tbl">' +
      '<thead><tr><th>Coefficient</th><th>Class</th><th class="num">Base</th>' +
      '<th class="num">Cost swing</th><th>Low bound</th><th>High bound</th>' +
      '</tr></thead><tbody>' + se.coefficients.map(function (c) {
        return '<tr><td class="row-label">' + esc(c.label) +
          '<div class="row-sub mono-sm">' + esc(c.coefficient) + '</div></td>' +
          '<td>' + ev(c.evidence) + '</td><td class="num">' +
          num(c.base_value, c.base_value < 1 ? 3 : 2) + '</td>' +
          '<td class="num">' + inr(c.cost_swing_inr) + '</td>' +
          c.variants.map(function (v) {
            return '<td class="small"><span class="num">' +
              num(v.value, v.value < 1 ? 2 : 0) + '</span> → ' +
              esc(v.recommended_strategy || '—') +
              (v.recommendation_changed
                ? ' <span class="ev ev-ASSUMED">changes plan</span>' : '') +
              '</td>';
          }).join('') + '</tr>';
      }).join('') + '</tbody></table></div>' +
      '<p class="small muted" style="margin-top:9px">The lot ORDER never ' +
      'changes. What flips is the process STRATEGY, and it flips in exactly ' +
      'the cases that make evaporator energy more expensive. That is the ' +
      'model behaving correctly, and it tells a site which two numbers to ' +
      'meter first.</p>'
    : '<div class="state-msg"><span class="spinner"></span>' +
      'Sweeping coefficients&hellip;</div>') + '</div>' +

  '<div class="block"><div class="block-head"><h2 class="block-title">' +
    'Constraint response — does it change its mind?</h2>' +
    '<span class="block-note">/api/modes/compare</span></div>' + (mc
    ? '<div class="tbl-wrap"><table class="tbl"><thead><tr>' +
      '<th>Binding constraint</th><th>Recommended strategy</th>' +
      '<th class="num">Freshwater</th><th class="num">Steam</th>' +
      '<th class="num">Cost</th><th class="num">Late</th></tr></thead><tbody>' +
      mc.modes.map(function (m) {
        return '<tr><td class="row-label">' + esc(m.mode_name) +
          '<div class="row-sub">' + esc(m.trigger || '') + '</div></td>' +
          '<td>' + esc(m.strategy_name || m.status) + '</td>' +
          '<td class="num">' + num(m.freshwater_intake_l, 0) + ' L</td>' +
          '<td class="num">' + num(m.mee_thermal_kwh, 0) + ' kWh</td>' +
          '<td class="num">' + inr(m.cost_inr) + '</td>' +
          '<td class="num">' + num(m.total_late_h, 1) + ' h</td></tr>';
      }).join('') + '</tbody></table></div>' +
      '<div class="callout insight" style="margin-top:12px">' +
      '<div class="callout-title">' + mc.distinct_recommended_plans +
      ' distinct plans across the modes</div><p>' + esc(mc.interpretation) +
      '</p><p style="margin-top:8px">Under normal economics the site ' +
      'rationally skips the low-salt chemistry — the dye premium costs ' +
      'more than the steam it saves. Price water scarcity or carbon, and the ' +
      'same engine starts recommending it. That is this product’s whole ' +
      'argument in one table.</p></div>'
    : '<div class="state-msg"><span class="spinner"></span>' +
      'Comparing modes&hellip;</div>') + '</div>' +

  '<div class="block"><div class="block-head"><h2 class="block-title">' +
    'Cluster scale</h2><span class="block-note">' + ev('PROJECTED') +
    ' — a projection, not a result</span></div>' + (cl
    ? '<div class="metrics">' +
      '<div class="metric is-water"><div class="metric-label">' +
        'Freshwater avoided</div><div class="metric-value">' +
        val(cl.freshwater_avoided_million_litres_per_year, 'ML/yr') +
        '</div><div class="metric-foot">across ' + num(cl.units, 0) +
        ' units</div></div>' +
      '<div class="metric is-salt"><div class="metric-label">Salt avoided' +
        '</div><div class="metric-value">' +
        val(cl.salt_avoided_tonnes_per_year, 't/yr') + '</div>' +
        '<div class="metric-foot">less crystalliser load</div></div>' +
      '<div class="metric is-energy"><div class="metric-label">' +
        'Evaporator steam</div><div class="metric-value">' +
        val(cl.evaporator_steam_avoided_mwh_per_year, 'MWh/yr') + '</div>' +
        '<div class="metric-foot">thermal</div></div>' +
      '<div class="metric is-carbon"><div class="metric-label">' +
        'CO₂e avoided</div><div class="metric-value">' +
        val(cl.co2e_avoided_tonnes_per_year, 't/yr') + '</div>' +
        '<div class="metric-foot">boiler emissions</div></div></div>' +
      '<div class="callout warn" style="margin-top:12px">' +
      '<div class="callout-title">Honesty</div><p>' + esc(cl.honesty) +
      '</p></div>' : '') +
    '<div class="callout" style="margin-top:12px">' +
    '<div class="callout-title">Why the cluster is the right unit</div>' +
    '<p>Units in a cluster share one common effluent treatment plant. The ' +
    'effluent model, the basin weighting and the steam cost are shared, so ' +
    'the second and third unit cost far less to onboard than the first. The ' +
    'CETP itself is the natural distribution channel — it already has a ' +
    'commercial relationship with every unit, and it directly benefits from a ' +
    'lower, steadier inlet salt load.</p></div></div>' +

  '<div class="block"><div class="block-head"><h2 class="block-title">' +
    'Pilot — how we would know it worked</h2>' +
    '<span class="block-note">' + ev('PLANNED') + '</span></div>' + (pl
    ? '<div class="callout insight"><div class="callout-title">' +
      'The question the pilot answers</div><p>' +
      esc(pl.question_the_pilot_answers) + '</p></div>' +
      '<div class="tbl-wrap" style="margin-top:12px"><table class="tbl">' +
      '<thead><tr><th class="num">Phase</th><th>Name</th><th>Weeks</th>' +
      '<th>Objective</th><th>Exit criteria</th></tr></thead><tbody>' +
      pl.phases.map(function (p) {
        return '<tr><td class="num">' + p.phase + '</td>' +
          '<td class="row-label">' + esc(p.name) + '</td>' +
          '<td class="mono-sm">' + esc(p.weeks) + '</td>' +
          '<td class="small">' + esc(p.objective) + '</td>' +
          '<td class="small muted">' + ((p.exit_criteria || []).map(esc)
            .join('<br>') || esc(p.note || p.guardrail || '—')) +
          '</td></tr>';
      }).join('') + '</tbody></table></div>' +
      '<div class="callout stop" style="margin-top:12px">' +
      '<div class="callout-title">Stop conditions</div><ul class="reasons">' +
      pl.stop_conditions.map(function (s) {
        return '<li>' + esc(s) + '</li>'; }).join('') + '</ul></div>' +
      '<div class="callout warn" style="margin-top:12px">' +
      '<div class="callout-title">What we will not claim</div><p>' +
      esc(pl.what_we_will_not_claim) + '</p></div>' : '') + '</div>' +
  '</div>';
}

/* ========================================================================== */
/* wiring                                                                     */
/* ========================================================================== */

function wire() {
  var v = document.getElementById('view');

  Array.prototype.forEach.call(v.querySelectorAll('[data-go]'), function (b) {
    b.onclick = function () {
      S.view = b.dataset.go; renderRail(); render(); window.scrollTo(0, 0);
    };
  });

  Array.prototype.forEach.call(v.querySelectorAll('[data-fault]'),
    function (b) {
      b.onclick = function () {
        guard(function () {
          return post('/api/washoff/run', { fault_mode: b.dataset.fault })
            .then(function (st) {
              S.state = st;
              var g = st.washoff.gate;
              toast(g.state === 'LOCKED_OUT'
                ? 'Locked out: ' + g.lockout_reason
                : 'Wash-off complete. Gate: ' + g.state.replace(/_/g, ' '),
                g.state === 'LOCKED_OUT');
            });
        });
      };
    });

  Array.prototype.forEach.call(v.querySelectorAll('[data-act]'), function (b) {
    b.onclick = function () { handleAct(b.dataset.act); };
  });

  Array.prototype.forEach.call(v.querySelectorAll('[data-trace]'),
    function (b) {
      b.onclick = function () { openTrace(b.dataset.trace); };
    });
}

function handleAct(act) {
  if (act === 'optimise') {
    return guard(function () {
      return post('/api/optimise', { mode: S.mode }).then(function (st) {
        S.state = st;
        toast('Optimiser evaluated ' + st.optimisation.candidates_evaluated +
          ' candidates.');
      });
    });
  }
  if (act === 'approve' || act === 'reject') {
    return guard(function () {
      return post('/api/decision/sequence',
        { approve: act === 'approve', actor: 'Shift planner' },
        'seq-' + Date.now()).then(function (st) {
          S.state = st;
          toast(act === 'approve'
            ? 'Approved and recorded. The plan is now the executed order.'
            : 'Rejected and recorded. Arrival order retained, nothing credited.');
          if (act === 'approve') S.view = 'washoff';
        });
    });
  }
  if (act === 'release' || act === 'norelease') {
    return guard(function () {
      return post('/api/washoff/release',
        { approve: act === 'release', actor: 'Quality supervisor' },
        'rel-' + Date.now()).then(function (st) {
          S.state = st;
          toast(act === 'release' ? 'Released and recorded.'
            : 'Declined. Full cycle will run and nothing is credited.');
          if (act === 'release') S.view = 'consequence';
        });
    });
  }
  if (act === 'verify') {
    return guard(function () {
      return api('/api/ledger/verify').then(function (r) {
        return api('/api/state').then(function (st) {
          S.state = st;
          toast(r.intact
            ? 'Chain verified: ' + r.records +
              ' records, every link recomputed.'
            : 'CHAIN BROKEN at #' + r.first_break_at_seq, !r.intact);
        });
      });
    });
  }
  if (act === 'export' || act === 'download') {
    return guard(function () {
      return api('/api/export').then(function (x) {
        if (act === 'download') {
          var blob = new Blob([JSON.stringify(x, null, 2)],
            { type: 'application/json' });
          var a = document.createElement('a');
          a.href = URL.createObjectURL(blob);
          a.download = 'changeloop-export-' + x.export_id.slice(0, 8) + '.json';
          a.click();
          URL.revokeObjectURL(a.href);
          toast('Export downloaded. SHA-256 ' +
            x.export_sha256.slice(0, 16) + '…');
        } else {
          sheet('Export payload',
            '<p class="small muted">SHA-256 over the whole payload: ' +
            '<span class="hash">' + esc(x.export_sha256) + '</span></p>' +
            '<div class="formula" style="margin-top:12px;max-height:50vh;' +
            'overflow:auto">' + esc(JSON.stringify(x, null, 2)) + '</div>');
        }
      });
    });
  }
  if (act === 'calc-case') {
    return guard(function () {
      var body = {};
      Array.prototype.forEach.call(
        document.querySelectorAll('[id^="bc_"]'), function (el) {
          body[el.id.slice(3)] = Number(el.value);
        });
      return post('/api/business-case', body).then(function (r) {
        S.businessCase = r;
        toast('Business case computed from your inputs.');
      }).catch(function (e) {
        S.businessCase = e.payload || { status: 'ERROR', notice: e.message };
        throw e;
      });
    });
  }
}

function openTrace(metric) {
  api('/api/trace?metric=' + encodeURIComponent(metric)).then(function (t) {
    sheet('How this number was produced',
      '<h3 style="font-size:15px;margin-bottom:10px">' + esc(t.metric) +
      '</h3><div class="formula">' + esc(t.formula) + '</div>' +
      '<dl class="defs" style="margin-top:16px">' +
      row('Evidence', ev(t.evidence.split(' ')[0]) +
        ' <span class="small muted">' + esc(t.evidence) + '</span>') +
      row('Upstream chain', '<ul class="reasons">' +
        t.upstream.map(function (u) {
          return '<li class="mono-sm">' + esc(u) + '</li>'; }).join('') +
        '</ul>') + '</dl>' +
      (t.coefficient_detail && t.coefficient_detail.length
        ? '<div class="block-head" style="margin-top:18px">' +
          '<h3 class="block-title">Coefficients involved</h3></div>' +
          '<div class="tbl-wrap"><table class="tbl"><tbody>' +
          t.coefficient_detail.map(function (c) {
            return '<tr><td class="row-label">' + esc(c.label) +
              '<div class="row-sub small">' + esc(c.basis) + '</div></td>' +
              '<td class="num nowrap">' + num(c.value, c.value < 1 ? 5 : 2) +
              '<div class="row-sub mono-sm">' + esc(c.unit) + '</div></td>' +
              '<td>' + ev(c.evidence) + '</td></tr>';
          }).join('') + '</tbody></table></div>' : ''));
  }).catch(function (e) { toast(e.message, true); });
}

function sheet(title, html) {
  document.getElementById('sheetTitle').textContent = title;
  document.getElementById('sheetBody').innerHTML = html;
  var d = document.getElementById('sheet');
  if (!d.open) d.showModal();
}

document.getElementById('sheetClose').onclick = function () {
  document.getElementById('sheet').close();
};

/* keyboard: 1-8 jump between sections */
document.addEventListener('keydown', function (e) {
  if (e.target.matches && e.target.matches('input, select, textarea')) return;
  if (document.getElementById('sheet').open) return;
  var n = parseInt(e.key, 10);
  if (n >= 1 && n <= VIEWS.length) {
    S.view = VIEWS[n - 1].id;
    renderRail(); render(); window.scrollTo(0, 0);
  }
});

boot();
