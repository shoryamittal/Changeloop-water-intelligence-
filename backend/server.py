"""AquaFlux local demonstration server. All operating data is synthetic."""
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse
import json, random, math, time, uuid

ROOT = Path(__file__).resolve().parents[1]
RULES = json.loads((ROOT / "config" / "changeover_rules.json").read_text())
AUDIT = []

def record(action, detail):
    AUDIT.append({"event_id":str(uuid.uuid4()),"timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "action": action, "detail": detail, "classification": "SIMULATED"})

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
        if float(batch["deadline_h"]) < 0: return f"Deadline is already infeasible for {batch['id']}."
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
    q=body["batches"] if "batches" in body else batches(body.get("seed",2030))
    error=validate_queue(q)
    if error:
        record("OPTIMIZE_REJECTED",error)
        return {"status":"NO FEASIBLE PLAN UNDER CURRENT CONSTRAINTS", "classification":"SYNTHETIC_DATA", "notice":"Simulation — not L'Oréal production data.", "constraint_explanation":error}
    w=float(body.get("water_weight",1)); d=float(body.get("deadline_weight",1))
    ordered, trans=score_order(q,w,d)
    baseline_objective, baseline=evaluate_order(q,w,d)
    candidate_objective, trans=evaluate_order(ordered,w,d)
    retained = candidate_objective >= baseline_objective
    if retained: ordered, trans, candidate_objective = q, baseline, baseline_objective
    result={"status":"FEASIBLE", "classification":"SYNTHETIC_DATA", "notice":"Simulation — not L'Oréal production data.", "baseline": {"order":[x["id"] for x in q],"water_demand_l":round(sum(x["litres"] for x in baseline),1),"objective":round(baseline_objective,1)}, "optimized":{"order":[x["id"] for x in ordered],"water_demand_l":round(sum(x["litres"] for x in trans),1),"objective":round(candidate_objective,1),"transitions":trans}, "method":"Greedy constructive heuristic; baseline candidate retained when the heuristic cannot improve the configured objective. It does not prove global optimality.","baseline_retained":retained}
    record("OPTIMIZE", "Synthetic batch queue optimized")
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
    volume=float(body.get("volume_l",120)); ph=body.get("quality","unknown")
    if volume < 0:
        return {"classification":"ILLUSTRATIVE_SCENARIO","notice":"Simulation — not L'Oréal production data.","screening":"INSUFFICIENT INFORMATION","available_volume_l":0,"recommended_destination":None,"required_checks":["Correct invalid negative volume before screening"]}
    status="INSUFFICIENT INFORMATION" if ph=="unknown" else ("POTENTIALLY REUSABLE SUBJECT TO VALIDATION" if ph=="screened" else "TREATMENT REQUIRED")
    return {"classification":"ILLUSTRATIVE_SCENARIO","notice":"Simulation — not L'Oréal production data. No reuse is approved.","available_volume_l":volume,"screening":status,"recommended_destination":"Non-product-contact utility use — illustrative only" if status.startswith("POTENTIALLY") else None,"required_checks":["site water-quality criteria","regulatory review","cross-contamination review","human approval"]}

def impact(body):
    seq=sequence_payload(body); base=seq["baseline"]["water_demand_l"]; prevent=seq["optimized"]["water_demand_l"]
    requested_adapt=float(body.get("adapt_incremental_l", 24)); recovered=max(0,float(body.get("recovered_l", 42)))
    adapt=min(max(0,requested_adapt),prevent)
    return {"classification":"MODEL_OUTPUT","notice":"Modeled synthetic scenario, not L'Oréal production data.","common_baseline_l":base,"prevent_incremental_l":round(max(0,base-prevent),1),"adapt_incremental_l":adapt,"adapt_requested_l":requested_adapt,"cascade_potential_l":recovered,"water_demand_after_prevent_adapt_l":round(max(0,prevent-adapt),1),"accounting_note":"Cascade is reported separately as potential reuse and is not added to water-demand avoidance."}

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
        if route=="/api/audit-log": return self.send_json({"items":AUDIT})
        if route=="/api/assumptions": return self.send_json({"classification":"ENGINEERING_ASSUMPTION","rules":RULES})
        if route=="/api/pilot": return self.send_json(pilot())
        if route=="/api/models": return self.send_json(models())
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
        return self.send_json({"error":"Unknown route"},404)

if __name__=="__main__":
    import os; os.chdir(ROOT); print("AquaFlux running at http://localhost:8000")
    ThreadingHTTPServer(("",8000),App).serve_forever()
