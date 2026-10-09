/* Render test for the ChangeLoop front end.
 *
 * Loads frontend/app.js under a minimal DOM stub, feeds it REAL payloads from
 * the running API, then calls every view function and asserts that it
 * produces markup without throwing and without leaking "undefined" or "NaN"
 * into the output.
 *
 * Run:  node tests/test_frontend_render.js          (server must be up)
 */
'use strict';

const fs = require('fs');
const path = require('path');
const vm = require('vm');

const BASE = process.env.CL_BASE || 'http://127.0.0.1:8000';
const APP = path.join(__dirname, '..', 'frontend', 'app.js');

let failures = 0;
function check(name, ok, detail) {
  if (ok) {
    console.log('  ok    ' + name);
  } else {
    failures++;
    console.log('  FAIL  ' + name + (detail ? '  -> ' + detail : ''));
  }
}

/* ---------- minimal DOM stub ---------- */
function makeEl(id) {
  const el = {
    id: id,
    innerHTML: '',
    textContent: '',
    className: '',
    dataset: {},
    style: {},
    open: false,
    value: '',
    onclick: null,
    onchange: null,
    children: [],
    setAttribute() {},
    getAttribute() { return null; },
    querySelectorAll() { return []; },
    showModal() { this.open = true; },
    close() { this.open = false; },
    matches() { return false; },
    closest() { return null; },
    click() {},
    appendChild() {},
    focus() {},
    addEventListener() {},
    scrollIntoView() {},
    classList: {
      _s: {},
      add(c) { this._s[c] = true; },
      remove(c) { delete this._s[c]; },
      contains(c) { return !!this._s[c]; }
    },
  };
  return el;
}

const els = {};
function getEl(id) {
  if (!els[id]) els[id] = makeEl(id);
  return els[id];
}

/* the new shell queries these by id at load */
['brandCtx','siteSel','modeSel','ctxAsset','ctxResource','ctxData',
 'ctxSystem','cmdBtn','resetBtn','nav','view','sheet','sheetBd','sheetKind',
 'sheetTitle','sheetBody','sheetClose','cp','cpBd','cpInput','cpList','toast']
  .forEach(function (id) { getEl(id); });

const documentStub = {
  documentElement: {
    _attrs: {},
    setAttribute(k, v) { this._attrs[k] = v; },
    getAttribute(k) { return this._attrs[k] || null; },
  },
  getElementById: getEl,
  querySelectorAll() { return []; },
  createElement() { return makeEl('created'); },
  addEventListener() {},
};

async function main() {
  /* ---------- pull real payloads ---------- */
  const get = async (p) => {
    const r = await fetch(BASE + p);
    if (!r.ok) throw new Error(p + ' -> ' + r.status);
    return r.json();
  };

  // Drive the golden path so the views have populated state to render.
  const postJson = async (p, body) => {
    const r = await fetch(BASE + p, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body || {}),
    });
    return r.json();
  };

  await postJson('/api/session/reset', {});
  await postJson('/api/optimise', {});
  await postJson('/api/decision/sequence', { approve: true });
  await postJson('/api/washoff/run', {});
  await postJson('/api/washoff/release', { approve: true });

  const [state, sites, modes, insight, ablation, sens, modeCmp, evidence,
         pilot, cluster, forecast, matrix, narrative, plantNormal,
         plantDrought, policyLevers] = await Promise.all([
    get('/api/state'), get('/api/sites'), get('/api/modes'),
    get('/api/insight/salt-is-water'), get('/api/ablation'),
    get('/api/sensitivity'), get('/api/modes/compare'), get('/api/evidence'),
    get('/api/pilot'), get('/api/cluster-projection'),
    get('/api/forecast'), get('/api/changeover-matrix'),
    get('/api/narrative'),
    // the plant view draws both: today's plan, and the same plant with
    // scarcity priced. Without the second one its headline section is
    // skipped and the test would pass over the markup it most needs to
    // check.
    get('/api/plant?mode=NORMAL'), get('/api/plant?mode=DROUGHT'),
    // the switching-price sweep re-runs the optimiser a few hundred
    // times, so it is slow; fetching it here keeps the view's own
    // request out of the sandbox, which has no network at all.
    get('/api/policy?mode=NORMAL'),
  ]);
  const businessCase = await postJson('/api/business-case', {
    lots_per_year: 9000,
    freshwater_avoided_per_lot_l: 1108,
    salt_avoided_per_lot_kg: 12.5,
    freshwater_cost_inr_per_m3: 45,
    recycled_water_cost_inr_per_m3: 185,
    steam_cost_inr_per_kwh_th: 2.03,
    salt_cost_inr_per_kg: 9,
    implementation_cost_inr: 450000,
    annual_subscription_inr: 240000,
  });

  /* ---------- run app.js in a sandbox ---------- */
  const sandbox = {
    document: documentStub,
    window: {
      matchMedia() { return { matches: false }; },
      scrollTo() {},
    },
    localStorage: {
      getItem() { return null; },
      setItem() {},
    },
    // boot() runs on load and would race the payloads we inject below,
    // overwriting them with empty objects. Make the sandbox fetch reject so
    // boot() bails out immediately and leaves our injected state alone.
    fetch: () => Promise.reject(new Error('sandboxed: no network')),
    setTimeout, clearTimeout, setInterval: function () { return 0; },
    Promise, Blob: function () {}, URL: {
      createObjectURL() { return 'blob:x'; }, revokeObjectURL() {},
    },
    console,
    Math, Number, String, Object, Array, JSON, isFinite, parseInt, Date,
  };
  sandbox.globalThis = sandbox;

  const ctx = vm.createContext(sandbox);
  vm.runInContext(fs.readFileSync(APP, 'utf8'), ctx, { filename: 'app.js' });

  // Inject the real payloads into the module's state object.
  const S = vm.runInContext('S', ctx);
  S.state = state;
  S.sites = sites;
  S.modes = modes.modes;
  S.insight = insight;
  S.ablation = ablation;
  S.sensitivity = sens;
  S.modeCompare = modeCmp;
  S.evidence = evidence;
  S.pilot = pilot;
  S.cluster = cluster;
  S.businessCase = businessCase;
  S.forecast = forecast;
  S.matrix = matrix.matrix;
  S.narrative = narrative;
  S.plant = plantNormal;
  S.plantDrought = plantDrought;
  S.policy = policyLevers;

  const VIEWS = vm.runInContext('VIEWS', ctx);

  console.log('FRONT END RENDER TEST');
  console.log('='.repeat(64));

  for (const v of VIEWS) {
    S.view = v.id;
    let html = null;
    let err = null;
    try {
      vm.runInContext('render()', ctx);
      html = getEl('view').innerHTML;
    } catch (e) {
      err = e;
    }
    check('render ' + v.id, !err && html && html.length > 400,
      err ? err.message : 'produced ' + (html ? html.length : 0) + ' chars');

    if (html) {
      check('  ' + v.id + ' has no "undefined"',
        html.indexOf('undefined') === -1);
      check('  ' + v.id + ' has no "NaN"', html.indexOf('NaN') === -1);
      check('  ' + v.id + ' has no "[object Object]"',
        html.indexOf('[object Object]') === -1);

      /* The plain-language band is the answer to "a screener will not get
         past the vocabulary". It must be present on Command, must carry
         the one-sentence hook, and must show the two halves of the proof
         the engine computed rather than numbers we typed. */
      if (v.id === 'command') {
        check('  command renders the plain-language band',
          html.indexOf('class="pb"') !== -1);
        check('  band carries the jargon-free hook',
          html.indexOf('the coal bill is set by how much salt') !== -1);
        check('  band shows the water half of the proof (0.0%)',
          /pb-flat[\s\S]{0,240}0\.0%/.test(html));
        check('  band shows the salt half of the proof (-20.0%)',
          /pb-move[\s\S]{0,240}-20\.0%/.test(html));
        check('  band shows the published-band validation',
          html.indexOf('published band 20–30%') !== -1 ||
          html.indexOf('published band 20') !== -1);
        check('  band offers the reasoning ladder',
          html.indexOf('data-why="reasoning"') !== -1);
        check('  band states the equation',
          html.indexOf('V_reject = M_salt / C_reject_max') !== -1);
      }
    }
  }

  /* ---------- an unoptimised session must render empty states ---------- */
  await postJson('/api/session/reset', {});
  S.state = await get('/api/state');
  S.businessCase = null;
  for (const v of VIEWS) {
    S.view = v.id;
    let err = null;
    try { vm.runInContext('render()', ctx); } catch (e) { err = e; }
    check('empty-state render ' + v.id, !err, err ? err.message : '');
  }

  /* ---------- a locked-out session must render ---------- */
  await postJson('/api/optimise', {});
  await postJson('/api/decision/sequence', { approve: true });
  await postJson('/api/washoff/run', { fault_mode: 'sensor_drift' });
  S.state = await get('/api/state');
  S.view = 'water';
  let err = null;
  try { vm.runInContext('render()', ctx); } catch (e) { err = e; }
  const lockHtml = getEl('view').innerHTML;
  check('locked-out water view renders', !err, err ? err.message : '');
  check('locked-out shows LOCKED OUT',
    lockHtml.indexOf('LOCKED OUT') !== -1 ||
    lockHtml.indexOf('locked out') !== -1);

  console.log('='.repeat(64));
  console.log(failures === 0 ? 'ALL RENDER CHECKS PASS'
    : failures + ' RENDER CHECK(S) FAILED');
  process.exit(failures ? 1 : 0);
}

main().catch((e) => {
  console.error('render test could not run:', e.message);
  if (e.cause) console.error('  cause:', e.cause.code || e.cause.message);
  console.error(e.stack);
  process.exit(2);
});
