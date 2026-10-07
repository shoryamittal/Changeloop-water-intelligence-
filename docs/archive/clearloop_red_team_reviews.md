> **Archived.** Two hostile reviews of the earlier ClearLoop prototype.
> Kept for the method rather than the findings: each persona is forced
> to produce five strengths, ten weaknesses, ten questions, five reasons
> to reject and five highest-impact fixes. The fixed counts drag out
> criticism a looser review never reaches. Worth re-running against the
> current system. See [README](README.md).

---

# Hostile competition review — round 1

## Judge 1: Plant director

**Strengths:** explicit sequence rationale; deadline weight; failure fallback; human gate; deterministic demo.

**Weaknesses / questions:** Can it respect campaign, allergen, tank, staffing and CIP constraints? How is a schedule accepted by production? What happens on a late batch? Why would operators trust the recommendation? Which historian and planning interfaces are needed? How long is configuration? Which part changes validated work? What stops a bad recommendation? Who owns the exception path? How is uptime protected?

**Reasons to reject:** claims more control than it has; unvalidated transition rules; missing real constraints; poor operator workflow; unclear pilot boundary.

**Highest-value changes:** keep the system advisory; document missing constraints; add explicit infeasibility explanation; require planner approval; scope pilot to a single line and selected transitions.

## Judge 2: Sustainability director

**Strengths:** upstream framing; source discipline; no double counting; recovery is separate; limitations visible.

**Weaknesses / questions:** What metering establishes the baseline? Is this withdrawal, demand, or consumption? What quality governs reuse? What is the local water context? Could sequence changes shift other impacts? How are chemicals considered? Is recovery additional? What prevents false reuse claims? What is the boundary? How is impact audited?

**Reasons to reject:** ambiguous water vocabulary; reuse presented as approved; unmeasured impacts; unsupported equivalencies; disconnected sustainability strategy.

**Highest-value changes:** retain metric definitions, common baseline ledger, traceable source register, and site validation condition; add a meter plan in the pilot.

## Judge 3: AI/ML expert

**Strengths:** no autonomous safety decision; simulated fault states; interpretable heuristic; seed visible; synthetic label.

**Weaknesses / questions:** Where is held-out validation? Why ML over rules? What is endpoint ground truth? How is calibration measured? How are drift and OOD detected? How are labels acquired? What is override analysis? How is missingness handled? What is the threshold? Who signs off model change?

**Reasons to reject:** simulated performance dressed as validation; sensor surrogate taken as cleanliness; no model governance; no ground truth; opaque claims.

**Highest-value changes:** do not claim accuracy; use rules until a labeled pilot dataset exists; create a model-card and monitoring plan.

## Judge 4: CFO / business judge

**Strengths:** refuses unsupported ROI; configurable scope; avoids double counting; clear validation stage; operational mechanism is concrete.

**Weaknesses / questions:** What is the cost to integrate? Who pays for instrumentation? What is the counterfactual? What downtime is avoided? What is the sensitivity to water price? What is the value of capacity? What is deployment cost? What is maintenance? What is payback? Why scale before pilot?

**Reasons to reject:** invented economics; benefits overlap; weak ownership; expensive integration; no implementation path.

**Highest-value changes:** show no economics until data is provided; use a transparent template with source fields; prove technical and operational feasibility first.

## Judge 5: Competition judge

**Strengths:** memorable upstream thesis; three linked layers; defensible caution; simple demo sequence; polished single-screen story.

**Weaknesses / questions:** Is it truly differentiated? Can it be shown in three minutes? Why is it a L’Oréal fit? What is real? What is simulated? What does a pilot prove? Why sequence first? Why not an existing MES? What one feature matters most? What has been tested? What would fail?

**Reasons to reject:** dashboard theater; too many unproven features; weak evidence; unclear challenge fit; absence of official rubric.

**Highest-value changes:** supply official brief; present only Prevent → Adapt → Cascade; lead with limitations; demo the failure state; use the source register live.

## Improvement status

| Change | Status |
|---|---|
| Visible synthetic and integration labels | Implemented |
| Common-baseline incremental ledger | Implemented |
| Failure state with manual fallback | Implemented |
| Human safety gate | Implemented |
| Official requirements mapping | Blocked: official material absent |
| Real pilot validation | Architected; plant data absent |

---

# Final war room — round 2

This review evaluates the current executable synthetic prototype. “Improvement” means an implemented change only when marked implemented.

## A. Plant director

**Five strengths:** advisory control boundary; baseline retention; decision trace; explicit fault fallback; scoped one-line pilot.

**Ten weaknesses:** no campaigns; no tank constraints; no staffing rules; no validated recipes; no MES connection; soft rather than hard deadline model; no durable audit; no operator role model; no changeover execution workflow; no field data.

**Ten questions:** Who configures rules? Which batches are in scope? What is mandatory cleaning? Can a planner override? What happens to late batches? How is schedule accepted? Can it run offline? What controls require change? How is downtime measured? Who owns support?

**Five rejection reasons:** unsafe autonomy implied; missing real constraints; poor exception handling; operational burden exceeds benefit; simulation shown as pilot evidence.

**Five highest-impact improvements:** planner decision audit **implemented**; invalid-input explanation **implemented**; pilot scope **implemented**; durable audit **architected**; plant constraint configuration **architected**.

## B. Sustainability director

**Five strengths:** source register; public-context precision; no double counting; separate reuse potential; defined metric boundary.

**Ten weaknesses:** no meter plan in UI; no withdrawal metric; no discharge metric; no treatment boundary; no local water context; no chemistry impact; no carbon method; no materiality analysis; illustrative adaptive input; illustrative recovery input.

**Ten questions:** Where is baseline meter data? What water metric improves? What is reuse quality? Who approves it? Does treatment change? Is a stream truly displaced? What is the watershed impact? What is the measurement frequency? Who audits it? How are chemicals handled?

**Five rejection reasons:** water metrics blur together; reuse called saved water; unsupported CO2 claim; unsupported circularity claim; opaque boundary.

**Five highest-impact improvements:** ledger invariants **implemented**; metric definitions **implemented**; meter plan **documented**; plant treatment boundary **pending data**; site water context **pending location**.

## C. AI/ML expert

**Five strengths:** avoids unsupported ML; explains synthetic signal; fault simulation; no automatic safety release; model-governance target state.

**Ten weaknesses:** no labels; no heldout evaluation; no calibration; no trained model; no feature attribution; no threshold validation; no drift detector beyond simulation; no model registry; no human-override analysis; no OOD data.

**Ten questions:** Why ML? What is ground truth? How is cleanliness defined? What is precision? How are false positives handled? How is drift measured? Who approves a model version? What data are retained? Can rules suffice? What causes an override?

**Five rejection reasons:** synthetic signal described as AI; performance implied without test data; cleanliness inferred from conductivity; opaque failure behavior; production model claim.

**Five highest-impact improvements:** rule-first framing **implemented**; synthetic labels **implemented**; safe fallback **implemented**; heldout validation **blocked by real labels**; model card **documented as architecture**.

## D. CFO / business judge

**Five strengths:** refuses fake ROI; separates capacity from revenue; exposes assumptions; keeps direct and potential impacts distinct; pilot scope is small.

**Ten weaknesses:** no implementation estimate; no water-cost input; no maintenance cost; no training cost; no capacity utilization; no sensitivity chart; no decision owner; no payback boundary; no pilot budget; no scale economics.

**Ten questions:** Who pays? What is the counterfactual? How are benefits measured? What cost is avoided? What instrumentation is required? What integration cost exists? How is capacity valued? What is the minimum pilot? What must be true for scale? What stops investment?

**Five rejection reasons:** invented financial claim; double-counted benefit; hidden implementation burden; weak owner; no measurement plan.

**Five highest-impact improvements:** no-ROI boundary **implemented**; business-case input template **documented**; sensitivity interface **deferred pending real inputs**; pilot measurement plan **documented**; owner model **pending sponsor data**.

## E. Competition jury

**Five strengths:** memorable upstream premise; three-layer story; deterministic demo; visible fault demonstration; credible limitation language.

**Ten weaknesses:** official brief absent; no rubric mapping; limited visual differentiation; one-screen demo can feel dense; no official brand requirements; no presentation deck; no real pilot evidence; no outcome video; no side-by-side ablation chart; no durable live audit panel.

**Ten questions:** Why L’Oréal? Why now? Why this approach? What is real? What is simulated? Why not Waterloop alone? Why not a rule? What does the pilot prove? What will a user do next? What is memorable?

**Five rejection reasons:** generic factory framing; missing official alignment; dashboard theater; too many assumptions; unsupported outcome claim.

**Five highest-impact improvements:** deterministic default **implemented**; scenario explorer **implemented**; decision trace **implemented**; official material ingestion **blocked**; presentation aligned to rubric **blocked**.

## Round-2 verdict

The prototype can credibly demonstrate an upstream decision-support hypothesis. It cannot credibly claim plant validation, financial value, a trained ML model, or deployment readiness. The largest remaining external dependency is the official brief, followed by agreed pilot data and constraints.
