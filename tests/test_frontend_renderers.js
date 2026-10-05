/**
 * ChangeLoop Frontend View Renderers, State Transitions & UI Component Test Suite
 *
 * Validates in Node.js:
 * 1. Clean execution of all 13 view renderers with zero ReferenceErrors or TypeErrors.
 * 2. Template literal integrity: zero 'undefined' or 'NaN' in generated DOM markup.
 * 3. 8-step guided judge tour configuration and action handlers.
 * 4. Helper formatting functions (escape, num, metric, badge, header).
 * 5. Facility and process node switching (Aulnay, Burgos, Settimo, Vorselaar).
 * 6. Audio synthesizer feedback tone generation (zero missing assets).
 */
const fs = require('fs');
const path = require('path');
const vm = require('vm');
const assert = require('assert');

const projectRoot = path.resolve(__dirname, '..');
const appJsCode = fs.readFileSync(path.join(projectRoot, 'frontend', 'app.js'), 'utf8');

// Mock browser environment
const recordedTimers = [];
const mockStorage = {};
const createdElements = [];

const mockElement = (tag = 'div') => {
  const el = {
    tagName: tag.toUpperCase(),
    textContent: '',
    innerHTML: '',
    value: '',
    dataset: {},
    style: {},
    classList: {
      _classes: new Set(),
      add: (c) => el.classList._classes.add(c),
      remove: (c) => el.classList._classes.delete(c),
      toggle: (c, force) => {
        if (force === undefined) {
          if (el.classList._classes.has(c)) el.classList._classes.delete(c);
          else el.classList._classes.add(c);
        } else if (force) {
          el.classList._classes.add(c);
        } else {
          el.classList._classes.delete(c);
        }
      },
      contains: (c) => el.classList._classes.has(c)
    },
    setAttribute: () => {},
    getAttribute: () => null,
    removeAttribute: () => {},
    appendChild: (child) => { createdElements.push(child); return child; },
    removeChild: () => {},
    click: () => {},
    addEventListener: () => {}
  };
  return el;
};

const domStore = {
  toast: mockElement('div'),
  page: mockElement('div'),
  sidebar: mockElement('aside'),
  demoDock: mockElement('div'),
  soundToggle: mockElement('button'),
  viewEyebrow: mockElement('span'),
  viewName: mockElement('span'),
  sidebarPlant: mockElement('span'),
  gatewayClock: mockElement('span'),
  topbarClock: mockElement('span'),
  topbarOpName: mockElement('b'),
  topbarOpTitle: mockElement('small'),
  topbarAvatar: mockElement('div'),
  judgeDialog: mockElement('dialog'),
  judgeEyebrow: mockElement('span'),
  judgeTitle: mockElement('h2'),
  judgeText: mockElement('p'),
  judgeActionArea: mockElement('div'),
  judgeProgress: mockElement('div'),
  gwMeshNodeTitle: mockElement('span'),
  skidPlantName: mockElement('b'),
  skidBatchName: mockElement('small'),
  skidWaterSaved: mockElement('div'),
  skidSavedTrend: mockElement('div'),
  skidTurbidity: mockElement('div'),
  skidTurbTrend: mockElement('div'),
  skidSeqDev: mockElement('div'),
  skidDevTrend: mockElement('div')
};

const mockDocument = {
  getElementById: (id) => domStore[id] || mockElement('div'),
  querySelector: (sel) => {
    if (sel.startsWith('#')) return domStore[sel.slice(1)] || mockElement('div');
    return mockElement('div');
  },
  querySelectorAll: (sel) => {
    if (sel.includes('.nav button')) {
      return [
        { dataset: { view: 'overview' }, classList: mockElement().classList },
        { dataset: { view: 'planning' }, classList: mockElement().classList },
        { dataset: { view: 'optimizer' }, classList: mockElement().classList },
        { dataset: { view: 'cleaning' }, classList: mockElement().classList },
        { dataset: { view: 'cascade' }, classList: mockElement().classList },
        { dataset: { view: 'analytics' }, classList: mockElement().classList },
        { dataset: { view: 'scenarios' }, classList: mockElement().classList },
        { dataset: { view: 'pilot' }, classList: mockElement().classList }
      ];
    }
    return [];
  },
  createElement: (tag) => mockElement(tag),
  body: mockElement('body'),
  addEventListener: () => {}
};

const mockWindow = {
  scrollTo: () => {},
  addEventListener: () => {},
  localStorage: {
    getItem: (k) => mockStorage[k] || null,
    setItem: (k, v) => { mockStorage[k] = String(v); },
    removeItem: (k) => { delete mockStorage[k]; }
  },
  AudioContext: class {
    createOscillator() {
      return {
        connect: () => {},
        start: () => {},
        stop: () => {},
        frequency: {
          setValueAtTime: () => {},
          exponentialRampToValueAtTime: () => {},
          linearRampToValueAtTime: () => {}
        }
      };
    }
    createGain() {
      return {
        connect: () => {},
        gain: {
          setValueAtTime: () => {},
          exponentialRampToValueAtTime: () => {}
        }
      };
    }
    get currentTime() { return 1.0; }
  }
};

const sandbox = {
  window: mockWindow,
  document: mockDocument,
  console: console,
  setTimeout: (fn, delay) => {
    const id = setTimeout(fn, 0); // Execute quickly
    recordedTimers.push(id);
    return id;
  },
  setInterval: (fn, delay) => {
    const id = setInterval(() => {}, 999999); // Stub interval
    recordedTimers.push(id);
    return id;
  },
  clearInterval: (id) => clearInterval(id),
  clearTimeout: (id) => clearTimeout(id),
  fetch: () => Promise.resolve({
    json: () => Promise.resolve({
      batches: [],
      matrix: {},
      session_id: 'TEST_SESSION',
      demo_step: '01_PLAN',
      total_water_demand_avoided_l: 414.0
    })
  })
};

vm.createContext(sandbox);

function runTests() {
  console.log('='.repeat(70));
  console.log(' RUNNING FRONTEND VIEW RENDERERS & UI COMPONENT TEST SUITE');
  console.log('='.repeat(70));

  let passed = 0;
  let failed = 0;

  function test(name, fn) {
    process.stdout.write(`[*] Testing: ${name} ... `);
    try {
      fn();
      console.log('PASSED');
      passed++;
    } catch (err) {
      console.log(`FAILED!\n  Error: ${err.message}`);
      failed++;
    }
  }

  // 1. Script compilation and evaluation
  test('Load and evaluate frontend/app.js in execution context', () => {
    const bridge = `
      globalThis.__EXPORTED = {
        state, views, escape, num, badge, source, metric, header,
        judgeSteps, changePlant, changeLine, playChime,
        overview, planning, optimizer, cleaning, cascade,
        analytics, scenarios, business, pilot, alerts, defense,
        dossier, trust,
        GLOBAL_BENCHMARKS, setBenchmarkParadigm, setScalingLines,
        renderGlobalWaterBenchmark, renderEnterpriseScalingSimulator,
        renderDecisionChainContinuityStrip
      };
    `;
    vm.runInContext(appJsCode + '\n' + bridge, sandbox);
    assert(sandbox.__EXPORTED, 'Export bridge must be populated');
    assert(sandbox.__EXPORTED.state, 'state object must be defined');
    assert(sandbox.__EXPORTED.views, 'views dictionary must be defined');
  });

  // 2. Formatting utilities
  test('Sanitization and formatting helpers (escape, num, metric, badge)', () => {
    const exp = sandbox.__EXPORTED;
    const escaped = exp.escape('<script>alert("xss")</script>&');
    assert.strictEqual(escaped, '&lt;script&gt;alert(&quot;xss&quot;)&lt;/script&gt;&amp;');

    const formattedNum = exp.num(14250.75, 1);
    assert(formattedNum.includes('14,250.8') || formattedNum.includes('14250.8'), `Expected 14,250.8, got ${formattedNum}`);

    const badgeHtml = exp.badge('TEST STATUS', 'good');
    assert(badgeHtml.includes('status-badge good') && badgeHtml.includes('TEST STATUS'));
  });

  // 3. Audio chime synthesizer
  test('Native Web Audio synthesizer feedback generation', () => {
    const exp = sandbox.__EXPORTED;
    exp.state.audioEnabled = true;
    exp.playChime('success');
    exp.playChime('cutoff');
    exp.playChime('alert');
    assert.strictEqual(exp.state.audioEnabled, true);
  });

  // 4. Test all 13 views
  const viewKeys = [
    'overview', 'planning', 'optimizer', 'cleaning', 'cascade',
    'analytics', 'scenarios', 'business', 'pilot', 'alerts',
    'defense', 'dossier', 'trust'
  ];

  for (const vKey of viewKeys) {
    test(`Render View: ${vKey.toUpperCase()} (HTML output & template integrity)`, () => {
      const exp = sandbox.__EXPORTED;
      exp.state.view = vKey;
      const renderer = exp[vKey];
      assert(typeof renderer === 'function', `Renderer for view '${vKey}' must be a function`);

      const html = renderer();
      assert(typeof html === 'string', `Renderer for '${vKey}' must return an HTML string`);
      assert(html.length > 200, `Markup for '${vKey}' must not be empty (got ${html.length} chars)`);

      // Ensure no raw undefined or NaN was accidentally interpolated into HTML text
      const hasUndefined = />[^<]*\bundefined\b[^<]*</.test(html) || /class="[^"]*\bundefined\b[^"]*"/.test(html);
      const hasNaN = />[^<]*\bNaN\b[^<]*</.test(html);
      assert(!hasUndefined, `View '${vKey}' interpolated 'undefined' in DOM markup`);
      assert(!hasNaN, `View '${vKey}' interpolated 'NaN' in DOM markup`);
    });
  }

  // 5. Guided Judge Tour configuration
  test('8-Step 3-Minute Guided Judge Tour steps validation', () => {
    const exp = sandbox.__EXPORTED;
    const steps = exp.judgeSteps;
    assert(Array.isArray(steps), 'judgeSteps must be an array');
    assert.strictEqual(steps.length, 8, `Expected exactly 8 steps, got ${steps.length}`);

    steps.forEach((step, idx) => {
      assert(step.view, `Step ${idx + 1} must specify a target view`);
      assert(step.title, `Step ${idx + 1} must have a title`);
      assert(step.text, `Step ${idx + 1} must have descriptive text`);
      assert(typeof step.action === 'function', `Step ${idx + 1} must have an executable action`);
    });
  });

  // 6. Facility switching
  test('Industrial facility node switcher (Aulnay, Burgos, Settimo, Vorselaar)', () => {
    const exp = sandbox.__EXPORTED;
    exp.changePlant('burgos');
    assert.strictEqual(exp.state.plant, 'burgos');

    exp.changePlant('settimo');
    assert.strictEqual(exp.state.plant, 'settimo');

    exp.changePlant('aulnay');
    assert.strictEqual(exp.state.plant, 'aulnay');
  });

  // 7. Global Water Benchmark Matrix
  test('Global Water Benchmark Matrix rendering & paradigm switching', () => {
    const exp = sandbox.__EXPORTED;
    assert(exp.GLOBAL_BENCHMARKS, 'GLOBAL_BENCHMARKS object must exist');
    assert(exp.GLOBAL_BENCHMARKS.changeloop, 'ChangeLoop paradigm definition must exist');
    assert(exp.GLOBAL_BENCHMARKS.legacy, 'Legacy CIP paradigm definition must exist');

    const html = exp.renderGlobalWaterBenchmark();
    assert(html.includes('GLOBAL WATER MANAGEMENT BENCHMARK'), 'Benchmark title must render');
    assert(html.includes('Why ChangeLoop Beats Every Alternative'), 'Subtitle must render');
    assert(!html.includes('undefined'), 'No undefined values in benchmark HTML');

    // Test paradigm switcher
    exp.setBenchmarkParadigm('legacy');
    assert.strictEqual(exp.state.selectedBenchmarkParadigm, 'legacy');
    exp.setBenchmarkParadigm('changeloop');
    assert.strictEqual(exp.state.selectedBenchmarkParadigm, 'changeloop');
  });

  // 8. Enterprise Scaling Simulator
  test('Enterprise Scaling Simulator rendering & line scaling math', () => {
    const exp = sandbox.__EXPORTED;
    const html1 = exp.renderEnterpriseScalingSimulator();
    assert(html1.includes('Enterprise Fleet Scaling Simulator'), 'Simulator title must render');
    assert(html1.includes('€355,000'), '1-line operating savings must render');
    assert(html1.includes('3.2'), 'Payback must include 3.2 Months');

    // Test scaling to 4 lines
    exp.setScalingLines(4);
    assert.strictEqual(exp.state.scalingNumLines, 4);
    const html4 = exp.renderEnterpriseScalingSimulator();
    assert(html4.includes('€1,420,000'), '4-line annual savings must be €1,420,000');
    assert(!html4.includes('NaN'), 'No NaN values in simulator HTML');

    // Reset back to 1 line
    exp.setScalingLines(1);
    assert.strictEqual(exp.state.scalingNumLines, 1);
  });

  // 9. Decision-Chain Continuity Strip
  test('Decision-Chain Continuity Strip rendering across all operational stages', () => {
    const exp = sandbox.__EXPORTED;
    const stages = ['planning', 'optimizer', 'cleaning', 'cascade', 'analytics'];
    
    stages.forEach(stage => {
      const stripHtml = exp.renderDecisionChainContinuityStrip(stage);
      assert(stripHtml.includes('CONNECTED DECISION CHAIN'), `Strip for ${stage} must include title`);
      assert(stripHtml.includes('decision-chain-continuity-strip'), `Strip for ${stage} must include wrapper class`);
      assert(stripHtml.includes('ACTIVE WORKFLOW STAGE'), `Strip for ${stage} must indicate active workflow stage`);
      assert(!stripHtml.includes('undefined'), `Strip for ${stage} must not contain undefined`);
      assert(!stripHtml.includes('NaN'), `Strip for ${stage} must not contain NaN`);
    });
  });

  // Cleanup recorded timers
  recordedTimers.forEach(id => {
    clearTimeout(id);
    clearInterval(id);
  });

  console.log('='.repeat(70));
  console.log(` SUMMARY: ${passed} PASSED, ${failed} FAILED`);
  console.log('='.repeat(70));

  if (failed > 0) {
    process.exit(1);
  } else {
    process.exit(0);
  }
}

runTests();
