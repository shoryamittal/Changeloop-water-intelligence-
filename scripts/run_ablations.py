"""Run an explicit synthetic ablation; results are not plant performance estimates."""
import json, statistics, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend.server import sequence_payload

ROOT=Path(__file__).resolve().parents[1]
rows=[]
for seed in range(2026,2126):
    result=sequence_payload({"seed":seed})
    baseline=result["baseline"]["water_demand_l"]
    prevent=result["optimized"]["water_demand_l"]
    adaptive_increment=min(24,baseline)
    full_increment=min(24,prevent)
    rows.append({
        "seed":seed,
        "baseline_l":baseline,
        "prevent_l":prevent,
        "adapt_only_illustrative_l":round(max(0,baseline-adaptive_increment),1),
        "prevent_adapt_l":round(max(0,prevent-full_increment),1),
        "cascade_potential_l":42,
    })
def stats(field):
    values=[row[field] for row in rows]
    return {"mean":round(statistics.mean(values),2),"median":round(statistics.median(values),2),"minimum":round(min(values),2),"maximum":round(max(values),2)}
out={
    "classification":"SYNTHETIC_DATA",
    "notice":"Simulation — not L'Oréal production data. Adaptive and cascade values are illustrative assumptions.",
    "scenario_count":len(rows),
    "random_seed_range":"2026–2125",
    "water_demand_l":{key:stats(key) for key in ["baseline_l","prevent_l","adapt_only_illustrative_l","prevent_adapt_l"]},
    "cascade":"Potential reuse is reported separately and is not added to water-demand reduction.",
    "scenarios":rows,
}
(ROOT/"data"/"synthetic_ablation_2026.1.json").write_text(json.dumps(out,indent=2))
print(json.dumps({key:value for key,value in out.items() if key!="scenarios"},indent=2))
