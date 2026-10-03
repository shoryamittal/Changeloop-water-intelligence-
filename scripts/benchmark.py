"""Measure local function latency for the deterministic demonstration, not plant performance."""
import json, statistics, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend.server import cleaning, impact, sequence_payload

def measure(name, fn, count=100):
    samples=[]
    for _ in range(count):
        start=time.perf_counter(); fn(); samples.append((time.perf_counter()-start)*1000)
    return {"operation":name,"runs":count,"mean_ms":round(statistics.mean(samples),3),"p95_ms":round(sorted(samples)[int(count*.95)-1],3),"max_ms":round(max(samples),3)}
out={"classification":"REAL","scope":"Local function timing on the current development environment; not production sizing.","results":[measure("optimize",lambda:sequence_payload({})),measure("cleaning_simulation",lambda:cleaning()),measure("impact",lambda:impact({}))]}
print(json.dumps(out,indent=2))
