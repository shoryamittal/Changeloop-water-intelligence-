"""Create 5,000 causal synthetic transition records for demo and model-development exercises."""
import json, random, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend.server import batches, burden

ROOT=Path(__file__).resolve().parents[1]
r=random.Random(2026); rows=[]
for index in range(5000):
    a,b=batches(5000+index,2)
    transition=burden(a,b)
    failure=r.choices(["normal","missing","spike","drift"],[.86,.06,.04,.04])[0]
    water=max(0,round(transition["litres"]+r.gauss(0,transition["litres"]*.08),2))
    minutes=max(0,round(transition["minutes"]+r.gauss(0,transition["minutes"]*.1),2))
    rows.append({"record_id":f"SYN-{index+1:05}","classification":"SYNTHETIC_DATA","from_family":a["family"],"to_family":b["family"],"from_shade":a["shade"],"to_shade":b["shade"],"from_viscosity":a["viscosity"],"to_viscosity":b["viscosity"],"residue_difficulty":b["residue"],"special_cleaning_flag":b["special"],"modeled_water_l":water,"modeled_duration_min":minutes,"sensor_condition":failure,"operator_override":failure!="normal" and r.random()<.45})
out={"dataset_version":"synthetic-changeovers-2026.1","classification":"SYNTHETIC_DATA","notice":"Synthetic demonstration dataset — not L'Oréal proprietary data.","random_seed":2026,"record_count":len(rows),"records":rows}
(ROOT/"data"/"synthetic_changeovers_2026.1.json").write_text(json.dumps(out,indent=2))
print(f"Generated {len(rows)} synthetic transition records.")
