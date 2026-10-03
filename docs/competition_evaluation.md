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
