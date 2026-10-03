"""ClearLoop local demonstration server. All operating data is synthetic."""
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse
import json, random, math, time, uuid, sqlite3

ROOT = Path(__file__).resolve().parents[1]
RULES = json.loads((ROOT / "config" / "changeover_rules.json").read_text())
AUDIT = []
DB_PATH = ROOT / "data" / "clearloop_demo.db"

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS audit_logs (
            event_id TEXT PRIMARY KEY, timestamp TEXT NOT NULL, action TEXT NOT NULL,
            detail TEXT NOT NULL, classification TEXT NOT NULL)""")

def audit_events():
    try:
        init_db()
        with sqlite3.connect(DB_PATH) as conn:
            rows=conn.execute("SELECT event_id, timestamp, action, detail, classification FROM audit_logs ORDER BY timestamp DESC").fetchall()
        return [dict(zip(["event_id","timestamp","action","detail","classification"],row)) for row in rows]
    except sqlite3.Error:
        return list(reversed(AUDIT))

def record(action, detail):
    event={"event_id":str(uuid.uuid4()),"timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "action": action, "detail": detail, "classification": "SIMULATED"}
    AUDIT.append(event)
    try:
        init_db()
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("INSERT INTO audit_logs VALUES (?, ?, ?, ?, ?)",tuple(event.values()))
        event["persistence"]="sqlite"
    except sqlite3.Error:
        event["persistence"]="memory_fallback"
    return event

def batches(seed=2030, count=12):
    r = random.Random(seed)
    families = ["care", "colour", "styling"]
    shades = ["light", "medium", "dark"]
    residues = ["low", "medium", "high"]
    return [{"id": f"B-{i+1:02}", "family": r.choice(families), "shade": r.choice(shades), "viscosity": r.choice(["low", "high"]), "residue": r.choice(residues), "special": r.random() < .16, "priority": r.randint(1,3), "deadline_h": r.randint(10,54)} for i in range(count)]

def validate_queue(queue):
    required={"id","family","shade","viscosity","residue","special","priority","deadline_h"}
    if not isinstance(queue,list) or not queue: return "No batches supplied."
    ids=[]
    for batch in queue:
        if not isinstance(batch,dict) or required-set(batch): return "A batch is missing required fields."
        if batch["residue"] not in RULES["base_litres_by_residue"]: return "Unknown residue class."
        try: deadline=float(batch["deadline_h"])
        except (TypeError, ValueError): return f"Deadline is invalid for {batch['id']}."
        if not math.isfinite(deadline) or deadline < 0: return f"Deadline is already infeasible for {batch['id']}."
        ids.append(batch["id"])
    if len(ids)!=len(set(ids)): return "Duplicate batch identifiers are not allowed."
    return None

def burden(a, b):
    m = 1.0
    tags=[]
    if a["family"] == b["family"]: tags.append("same formula family")
    if a["shade"] == "dark" and b["shade"] == "light": m *= RULES["transition_multipliers"]["dark_to_light"]; tags.append("dark-to-light transition")
    if a["viscosity"] == "high" and b["viscosity"] == "low": m *= RULES["transition_multipliers"]["viscous_to_low"]; tags.append("high-to-low viscosity")
    if b["special"]: m *= RULES["transition_multipliers"]["special_clean"]; tags.append("special-cleaning flag")
    base_l = RULES["base_litres_by_residue"][b["residue"]]
    base_m = RULES["base_minutes_by_residue"][b["residue"]]
    return {"litres": round(base_l*m,1), "minutes": round(base_m*m,1), "reasons": tags or ["base residue burden"], "classification":"ENGINEERING_ASSUMPTION"}

def score_order(queue, water_weight=1, deadline_weight=1):
    remaining=list(queue); ordered=[remaining.pop(0)]; transitions=[]; elapsed=0
    while remaining:
        current=ordered[-1]
        def cost(x):
            p=burden(current,x); late=max(0, elapsed+p["minutes"]/60-x["deadline_h"])
            return water_weight*p["litres"] + deadline_weight*late*160
        nxt=min(remaining,key=cost); p=burden(current,nxt); elapsed += p["minutes"]/60
        transitions.append({"from":current["id"],"to":nxt["id"],**p}); ordered.append(nxt); remaining.remove(nxt)
    return ordered, transitions

def evaluate_order(order, water_weight=1, deadline_weight=1):
    """Return the same transparent objective for every candidate schedule."""
    elapsed=0; transitions=[]; objective=0
    for i in range(len(order)-1):
        p=burden(order[i],order[i+1]); elapsed += p["minutes"]/60
        late=max(0, elapsed-order[i+1]["deadline_h"])
        objective += water_weight*p["litres"] + deadline_weight*late*160
        transitions.append({"from":order[i]["id"],"to":order[i+1]["id"],**p})
    return objective, transitions

def sequence_payload(body):
    if not isinstance(body,dict):
        record("OPTIMIZE_REJECTED","Request body must be an object.")
        return {"status":"NO FEASIBLE PLAN UNDER CURRENT CONSTRAINTS", "classification":"SYNTHETIC_DATA", "notice":"Simulation — not L'Oréal production data.", "constraint_explanation":"Request body must be an object."}
    q=body["batches"] if "batches" in body else batches(body.get("seed",2030))
    error=validate_queue(q)
    if error:
        record("OPTIMIZE_REJECTED",error)
        return {"status":"NO FEASIBLE PLAN UNDER CURRENT CONSTRAINTS", "classification":"SYNTHETIC_DATA", "notice":"Simulation — not L'Oréal production data.", "constraint_explanation":error}
    try: w=float(body.get("water_weight",1)); d=float(body.get("deadline_weight",1))
    except (TypeError, ValueError):
        return {"status":"NO FEASIBLE PLAN UNDER CURRENT CONSTRAINTS", "classification":"SYNTHETIC_DATA", "notice":"Simulation — not L'Oréal production data.", "constraint_explanation":"Objective weights must be numeric."}
    if not math.isfinite(w) or not math.isfinite(d) or w < 0 or d < 0:
        return {"status":"NO FEASIBLE PLAN UNDER CURRENT CONSTRAINTS", "classification":"SYNTHETIC_DATA", "notice":"Simulation — not L'Oréal production data.", "constraint_explanation":"Objective weights must be finite and non-negative."}
    ordered, trans=score_order(q,w,d)
    baseline_objective, baseline=evaluate_order(q,w,d)
    candidate_objective, trans=evaluate_order(ordered,w,d)
    retained = candidate_objective >= baseline_objective
    if retained: ordered, trans, candidate_objective = q, baseline, baseline_objective
    optimization_id=str(uuid.uuid4())
    result={"status":"FEASIBLE", "optimization_id":optimization_id, "classification":"SYNTHETIC_DATA", "notice":"Simulation — not L'Oréal production data.", "baseline": {"order":[x["id"] for x in q],"water_demand_l":round(sum(x["litres"] for x in baseline),1),"objective":round(baseline_objective,1)}, "optimized":{"order":[x["id"] for x in ordered],"water_demand_l":round(sum(x["litres"] for x in trans),1),"objective":round(candidate_objective,1),"transitions":trans}, "method":"Greedy constructive heuristic; baseline candidate retained when the heuristic cannot improve the configured objective. It does not prove global optimality.","baseline_retained":retained}
    record("OPTIMIZE", f"Synthetic optimization run {optimization_id}")
    return result

def cleaning(seed=2026, failure=None):
    r=random.Random(seed); n=42; endpoint=30+r.randint(-3,4); readings=[]
    for minute in range(n):
        progress=min(1,minute/max(endpoint,1)); cond=1.1+11*(1-progress)**2+r.gauss(0,.18); turb=0.3+7*(1-progress)**2+r.gauss(0,.14)
        quality="valid"
        if failure=="missing" and 17<=minute<=22: cond=None; turb=None; quality="missing"
        if failure=="spike" and minute==19: cond=99; quality="invalid spike"
        if failure=="drift" and minute>=18: cond += (minute-17)*.32; turb += (minute-17)*.08; quality="drift suspected"
        readings.append({"minute":minute,"conductivity":None if cond is None else round(max(0,cond),2),"turbidity":None if turb is None else round(max(0,turb),2),"temperature":round(24+r.gauss(0,.35),1),"flow":round(8+r.gauss(0,.25),2),"quality":quality})
    critical=any(x["quality"] != "valid" for x in readings)
    probability=0 if critical else round(min(.96,max(.35,.52+(n-endpoint)/38)),2)
    return {"classification":"SYNTHETIC_DATA","notice":"Simulation — not L'Oréal production data.","baseline_minutes":42,"predicted_endpoint_minute":None if critical else endpoint,"endpoint_probability":probability,"confidence":"INSUFFICIENT DATA" if critical else ("moderate" if probability<.75 else "high"),"safety_gate":{"model_message":"INSUFFICIENT DATA — HUMAN/VALIDATED PROCEDURE REQUIRED" if critical else "Endpoint likely reached — requires human approval.","automatic_release":False,"required":"Site-specific validated criteria and human approval"},"readings":readings}

def cascade(body):
    try: volume=float(body.get("volume_l",120))
    except (TypeError, ValueError): volume=-1
    ph=body.get("quality","unknown")
    if volume < 0:
        return {"classification":"ILLUSTRATIVE_SCENARIO","notice":"Simulation — not L'Oréal production data.","screening":"INSUFFICIENT INFORMATION","available_volume_l":0,"recommended_destination":None,"required_checks":["Correct invalid negative volume before screening"]}
    status="INSUFFICIENT INFORMATION" if ph=="unknown" else ("POTENTIALLY REUSABLE SUBJECT TO VALIDATION" if ph=="screened" else "TREATMENT REQUIRED")
    return {"classification":"ILLUSTRATIVE_SCENARIO","notice":"Simulation — not L'Oréal production data. No reuse is approved.","available_volume_l":volume,"screening":status,"recommended_destination":"Non-product-contact utility use — illustrative only" if status.startswith("POTENTIALLY") else None,"required_checks":["site water-quality criteria","regulatory review","cross-contamination review","human approval"]}

def impact(body):
    seq=sequence_payload(body)
    if seq["status"] != "FEASIBLE":
        return {"classification":"MODEL_OUTPUT","notice":"Modeled synthetic scenario, not L'Oréal production data.","status":seq["status"],"constraint_explanation":seq["constraint_explanation"]}
    base=seq["baseline"]["water_demand_l"]; prevent=seq["optimized"]["water_demand_l"]
    try: requested_adapt=float(body.get("adapt_incremental_l", 24)); recovered=max(0,float(body.get("recovered_l", 42)))
    except (TypeError, ValueError):
        return {"classification":"MODEL_OUTPUT","notice":"Modeled synthetic scenario, not L'Oréal production data.","status":"INSUFFICIENT DATA","constraint_explanation":"Impact inputs must be numeric."}
    adapt=min(max(0,requested_adapt),prevent)
    return {"classification":"MODEL_OUTPUT","notice":"Modeled synthetic scenario, not L'Oréal production data.","common_baseline_l":base,"prevent_incremental_l":round(max(0,base-prevent),1),"adapt_incremental_l":adapt,"adapt_requested_l":requested_adapt,"cascade_potential_l":recovered,"water_demand_after_prevent_adapt_l":round(max(0,prevent-adapt),1),"accounting_note":"Cascade is reported separately as potential reuse and is not added to water-demand avoidance."}

def business_case(body):
    fields=["changeovers_per_year","water_avoided_per_changeover_l","water_cost_per_l","implementation_cost","annual_software_cost"]
    missing=[]; values={}
    for field in fields:
        try: values[field]=float(body[field])
        except (KeyError, TypeError, ValueError): missing.append(field)
    if missing:
        return {"classification":"ILLUSTRATIVE_SCENARIO","status":"INSUFFICIENT DATA","notice":"Enter verified site inputs. This prototype contains no L'Oréal costs or savings assumptions.","required_fields":missing}
    if any(not math.isfinite(value) or value < 0 for value in values.values()):
        return {"classification":"ILLUSTRATIVE_SCENARIO","status":"INSUFFICIENT DATA","notice":"All business-case inputs must be finite and non-negative."}
    direct=values["changeovers_per_year"]*values["water_avoided_per_changeover_l"]*values["water_cost_per_l"]
    annual_net=direct-values["annual_software_cost"]
    capex=values["implementation_cost"]
    payback_years=None if annual_net<=0 else round(capex/annual_net,2)
    roi=None if capex<=0 else round(annual_net/capex*100,1)
    scenarios=[]
    for label,factor in [("Conservative",.7),("Base",1),("Optimistic",1.3)]:
        benefit=direct*factor-values["annual_software_cost"]
        scenarios.append({"scenario":label,"water_avoidance_factor":factor,"annual_net_benefit":round(benefit,2),"payback_years":None if benefit<=0 else round(capex/benefit,2)})
    record("BUSINESS_CASE","Illustrative calculator run with user-entered site inputs")
    return {"classification":"ILLUSTRATIVE_SCENARIO","status":"CALCULATED","notice":"Illustrative calculation from user-entered inputs. Not L'Oréal economics and not a guaranteed outcome.","inputs":values,"direct_water_cost_benefit":round(direct,2),"annual_net_benefit":round(annual_net,2),"payback_years":payback_years,"annual_roi_percent":roi,"sensitivity":scenarios,"limitation":"Capacity, chemical, energy and revenue effects are excluded until their methodology and source data are defined."}

def pilot():
    return {"classification":"ARCHITECTED","notice":"Target integration architecture — not connected to L'Oréal systems.","mode":"Advisory only; existing validated procedure remains authoritative.","scope":"One line and selected quality-approved transitions.","success_criteria":["No unacceptable quality deviation","Deadline compliance","Measurable comparable baseline","Operational acceptance","Adequate data availability"],"stop_conditions":["Quality deviation","Sensor failure","Unvalidated reuse route","Critical system error","Production risk"]}

def models():
    return {"classification":"ARCHITECTED","endpoint_model":{"status":"Not trained on plant data","approach":"Rules and synthetic signal simulation only","release_authority":"Site-specific validated criteria and human approval"},"monitoring":{"track":["data availability","invalid reading rate","operator override rate","prediction error after ground truth exists"],"action":"Flag model; revert to validated procedure"}}

class App(SimpleHTTPRequestHandler):
    def log_message(self, *_): pass
    def send_json(self, value, code=200):
        raw=json.dumps(value).encode(); self.send_response(code); self.send_header("Content-Type","application/json"); self.send_header("X-Request-ID",str(uuid.uuid4())); self.send_header("Content-Length",str(len(raw))); self.end_headers(); self.wfile.write(raw)
    def do_GET(self):
        route=urlparse(self.path).path
        if route=="/api/batches": return self.send_json({"classification":"SYNTHETIC_DATA","items":batches()})
        if route=="/api/cleaning": return self.send_json(cleaning())
        if route=="/api/audit-log": return self.send_json({"items":audit_events(),"storage":"sqlite with in-memory fallback"})
        if route=="/api/assumptions": return self.send_json({"classification":"ENGINEERING_ASSUMPTION","rules":RULES})
        if route=="/api/pilot": return self.send_json(pilot())
        if route=="/api/models": return self.send_json(models())
        if route=="/api/business-case": return self.send_json({"classification":"ILLUSTRATIVE_SCENARIO","status":"INPUT REQUIRED","required_fields":["changeovers_per_year","water_avoided_per_changeover_l","water_cost_per_l","implementation_cost","annual_software_cost"],"notice":"Enter verified site inputs. This prototype contains no L'Oréal costs or savings assumptions."})
        if route=="/api/health": return self.send_json({"status":"ok","classification":"REAL","storage":"in-memory demonstration session"})
        if route.startswith("/api/"): return self.send_json({"error":"Unknown route"},404)
        self.path="/frontend/index.html" if route=="/" else route
        return super().do_GET()
    def do_POST(self):
        try:
            length=int(self.headers.get("Content-Length",0)); body=json.loads(self.rfile.read(length) or b"{}")
        except (ValueError, json.JSONDecodeError): return self.send_json({"error":"Invalid JSON request body"},400)
        route=urlparse(self.path).path
        if route=="/api/optimize": return self.send_json(sequence_payload(body))
        if route=="/api/cleaning/start": record("CLEANING_SIMULATION","Started"); return self.send_json(cleaning(body.get("seed",2030),body.get("failure")))
        if route=="/api/water/analyze": record("WATER_SCREEN","Illustrative reuse screen"); return self.send_json(cascade(body))
        if route=="/api/impact/calculate": return self.send_json(impact(body))
        if route=="/api/business-case": return self.send_json(business_case(body))
        if route=="/api/optimization/decision":
            decision=body.get("decision") if isinstance(body,dict) else None
            if decision not in {"accept_recommendation","retain_baseline"}:
                return self.send_json({"error":"Decision must be accept_recommendation or retain_baseline."},400)
            event=record("PLANNER_DECISION",f"{decision} for synthetic optimization {body.get('optimization_id','unknown')}")
            return self.send_json({"classification":"SIMULATED","notice":"Planner decision recorded in this in-memory demonstration session; no plant schedule was changed.","event":event})
        return self.send_json({"error":"Unknown route"},404)

if __name__=="__main__":
    import os; os.chdir(ROOT); init_db(); print("AquaFlux running at http://localhost:8000")
    ThreadingHTTPServer(("",8000),App).serve_forever()
