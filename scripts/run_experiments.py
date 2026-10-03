"""Run 100 deterministic synthetic schedule scenarios and write an auditable summary."""
import json, statistics, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend.server import sequence_payload

ROOT=Path(__file__).resolve().parents[1]
rows=[]
for seed in range(2026, 2126):
    r=sequence_payload({"seed":seed})
    b=r["baseline"]["water_demand_l"]; o=r["optimized"]["water_demand_l"]
    rows.append({"seed":seed,"status":r["status"],"baseline_l":b,"optimized_l":o,"reduction_l":round(b-o,2),"reduction_pct":round((b-o)/b*100,2) if b else 0})
def summary(field):
    values=[x[field] for x in rows]
    return {"mean":round(statistics.mean(values),2),"median":round(statistics.median(values),2),"std_dev":round(statistics.stdev(values),2),"minimum":round(min(values),2),"maximum":round(max(values),2),"p10":round(sorted(values)[9],2),"p90":round(sorted(values)[89],2)}
out={"classification":"SYNTHETIC_DATA","notice":"Simulation — not L'Oréal production data.","dataset_version":"synthetic-2026.1","optimizer_version":"greedy-2026.1","assumption_version":"changeover-rules-2026.1","seeds":"2026–2125","scenario_count":len(rows),"feasible_rate":sum(x['status']=='FEASIBLE' for x in rows)/len(rows),"reduction_l":summary('reduction_l'),"reduction_pct":summary('reduction_pct'),"scenarios":rows}
(ROOT/'data').mkdir(exist_ok=True)
(ROOT/'data'/'synthetic_experiment_2026.1.json').write_text(json.dumps(out,indent=2))
print(json.dumps({k:v for k,v in out.items() if k not in ['scenarios']},indent=2))
