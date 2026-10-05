"""Golden path + invariant + safety verification for ChangeLoop."""
import sys
sys.path.insert(0, ".")
import core

print("=" * 72)
print("GOLDEN PATH")
print("=" * 72)
s = core.Session()
s.run_optimisation()
o = s.optimisation
print("search     :", o["method"])
print("optimality :", o["optimality"])
for x in o["options"]:
    print("  {:9s} {:16s} feasible={} fresh={:>9.1f} L  MEE={:>8.1f} kWh  "
          "cost={:>10.2f}".format(
              x["option_id"], x["strategy_id"], x["feasible"],
              x["freshwater_intake_l"], x["mee_thermal_kwh"], x["cost_inr"]))
    for v in x["violations"]:
        print("      REFUSED:", v)

s.decide_sequence(True, "Shift planner")
print("adopted plan:", s.current_order, "/", s.selected_strategy)
s.run_washoff(None)
w = s.washoff
print("washoff    : lot", w["lot_id"], "gate", w["gate"]["state"],
      "baths avoidable", w["baths_avoidable"])
s.release_washoff(True, "Quality supervisor")

i = s.impact()
print()
print("INVARIANTS :", "ALL PASS" if i["validation"]["all_pass"] else "FAILED")
for c in i["validation"]["checks"]:
    print("   {}  {}".format("ok  " if c["pass"] else "FAIL", c["rule"]))
print()
print("ATTRIBUTION")
print("  sequencing+strategy : {:>9.1f} L water  {:>7.2f} kg salt".format(
    i["sequencing_water_avoided_l"], i["sequencing_salt_avoided_kg"]))
print("  washoff release     : {:>9.1f} L water  {:>7.2f} kg salt".format(
    i["washoff_water_avoided_l"], i["washoff_salt_avoided_kg"]))
print()
print("TOTALS (baseline -> achieved)")
print("  freshwater : {:>10.1f} -> {:>10.1f}  avoided {:>9.1f} L "
      "({:>5.1f}%)".format(
          i["baseline_freshwater_intake_l"], i["achieved_freshwater_intake_l"],
          i["freshwater_avoided_l"],
          i["freshwater_avoided_l"] / max(1, i["baseline_freshwater_intake_l"])
          * 100))
print("  stress-eq  : {:>9.1f} L-eq at weight {:.2f}".format(
    i["stress_equivalent_avoided_l_eq"], i["stress_weight"]))
print("  salt       : {:>10.2f} -> {:>10.2f}  avoided {:>9.2f} kg".format(
    i["baseline_salt_kg"], i["achieved_salt_kg"], i["salt_avoided_kg"]))
print("  MEE steam  : {:>10.1f} -> {:>10.1f}  avoided {:>9.1f} kWh".format(
    i["baseline_mee_thermal_kwh"], i["achieved_mee_thermal_kwh"],
    i["mee_thermal_avoided_kwh"]))
print("  CO2e       : {:>10.1f} -> {:>10.1f}  avoided {:>9.1f} kg".format(
    i["baseline_co2e_kg"], i["achieved_co2e_kg"], i["co2e_avoided_kg"]))
print("  cost INR   : {:>10.0f} -> {:>10.0f}  avoided {:>9.0f}".format(
    i["baseline_cost_inr"], i["achieved_cost_inr"], i["cost_avoided_inr"]))
print()
st = s.state()
print("ledger     :", st["ledger_integrity"]["records"], "records, intact =",
      st["ledger_integrity"]["intact"])

print()
print("=" * 72)
print("SAFETY - every fault must force lockout and credit zero")
print("=" * 72)
fails = 0
for fm in ["sensor_dropout", "sensor_frozen", "sensor_drift",
           "colour_spike", "thermal_deficit"]:
    s2 = core.Session()
    s2.run_optimisation()
    s2.decide_sequence(True)
    s2.run_washoff(fm)
    gate = s2.washoff["gate"]
    res = s2.release_washoff(True)
    blocked = "error" in res
    credited = s2.impact()["washoff_water_avoided_l"]
    ok = (gate["state"] == "LOCKED_OUT" and blocked and credited == 0.0)
    if not ok:
        fails += 1
    print("  {:17s} gate={:22s} release_blocked={:5s} credited={:.1f}  {}"
          .format(fm, gate["state"], str(blocked), credited,
                  "OK" if ok else "*** FAIL ***"))

print()
print("=" * 72)
print("REJECTION - a rejected recommendation must credit exactly zero")
print("=" * 72)
s3 = core.Session()
s3.run_optimisation()
s3.decide_sequence(False, "Shift planner", "Buyer escalation on L-4412")
i3 = s3.impact()
rej_ok = (i3["freshwater_avoided_l"] == 0.0
          and i3["sequencing_water_avoided_l"] == 0.0
          and i3["validation"]["all_pass"])
print("  freshwater avoided after rejection:", i3["freshwater_avoided_l"],
      "L  invariants:", i3["validation"]["all_pass"],
      "  ", "OK" if rej_ok else "*** FAIL ***")
if not rej_ok:
    fails += 1

print()
print("=" * 72)
print("DETERMINISM - 10 identical runs must agree exactly")
print("=" * 72)
sig = set()
for _ in range(10):
    sx = core.Session()
    sx.run_optimisation()
    sx.decide_sequence(True)
    sx.run_washoff(None)
    sx.release_washoff(True)
    ix = sx.impact()
    sig.add((tuple(sx.current_order), sx.selected_strategy,
             round(ix["freshwater_avoided_l"], 3),
             round(ix["salt_avoided_kg"], 3),
             round(ix["mee_thermal_avoided_kwh"], 3),
             round(ix["co2e_avoided_kg"], 3),
             round(ix["cost_avoided_inr"], 2)))
det_ok = len(sig) == 1
print("  distinct outcomes across 10 runs:", len(sig),
      "  ", "OK" if det_ok else "*** FAIL ***")
if not det_ok:
    fails += 1

print()
print("=" * 72)
print("TAMPER DETECTION - editing a ledger row must break the chain")
print("=" * 72)
import sqlite3
from core import provenance
chk = provenance.verify_chain()
print("  before tamper: intact =", chk["intact"], "records =", chk["records"])
conn = sqlite3.connect(str(provenance.DEFAULT_DB_PATH))
try:
    conn.execute("UPDATE decision_ledger SET detail = ? WHERE seq = 2",
                 ("silently altered after the fact",))
    conn.commit()
finally:
    conn.close()
chk2 = provenance.verify_chain()
tamper_ok = (not chk2["intact"])
print("  after tamper : intact =", chk2["intact"], "break at seq =",
      chk2["first_break_at_seq"], "  ", "OK" if tamper_ok else "*** FAIL ***")
print("  detail:", chk2["detail"])
if not tamper_ok:
    fails += 1
provenance.reset()

print()
print("=" * 72)
print("RESULT:", "ALL CHECKS PASS" if fails == 0 else
      "{} CHECK(S) FAILED".format(fails))
print("=" * 72)
sys.exit(1 if fails else 0)
