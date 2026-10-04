"""ClearLoop Combinatorial Changeover Optimizer.
Implements Greedy constructive heuristics and 2-Opt local search refinement
with strict baseline retention safeguards and deadline penalty functions.
"""
from typing import List, Dict, Tuple, Any, Optional
import math
import uuid
from .cleanability import calculate_burden, validate_queue, generate_batches

def evaluate_order(order: List[Dict[str, Any]], water_weight: float = 1.0, deadline_weight: float = 1.0, rules: Optional[Dict[str, Any]] = None) -> Tuple[float, List[Dict[str, Any]]]:
    """Authoritative objective evaluation for any candidate schedule order.
    Objective = water_weight * litres + deadline_weight * lateness_penalty.
    """
    elapsed = 0.0
    transitions = []
    objective = 0.0
    for i in range(len(order) - 1):
        p = calculate_burden(order[i], order[i + 1], rules)
        elapsed += p["minutes"] / 60.0
        late = max(0.0, elapsed - float(order[i + 1]["deadline_h"]))
        objective += water_weight * p["litres"] + deadline_weight * late * 160.0
        transitions.append({
            "from": order[i]["id"],
            "to": order[i + 1]["id"],
            **p
        })
    return objective, transitions

def score_order_greedy(queue: List[Dict[str, Any]], water_weight: float = 1.0, deadline_weight: float = 1.0, rules: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """Greedy Nearest-Neighbor constructive heuristic."""
    remaining = list(queue)
    ordered = [remaining.pop(0)]
    elapsed = 0.0
    while remaining:
        current = ordered[-1]
        def cost(x: Dict[str, Any]) -> float:
            p = calculate_burden(current, x, rules)
            late = max(0.0, elapsed + p["minutes"] / 60.0 - float(x["deadline_h"]))
            return water_weight * p["litres"] + deadline_weight * late * 160.0
        nxt = min(remaining, key=cost)
        p = calculate_burden(current, nxt, rules)
        elapsed += p["minutes"] / 60.0
        ordered.append(nxt)
        remaining.remove(nxt)
    return ordered

def score_order_two_opt(initial_order: List[Dict[str, Any]], water_weight: float = 1.0, deadline_weight: float = 1.0, max_passes: int = 25, rules: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """2-Opt Local Search refinement to untangle tour crossovers."""
    best_order = list(initial_order)
    best_obj, _ = evaluate_order(best_order, water_weight, deadline_weight, rules)
    n = len(best_order)
    if n < 4:
        return best_order
    improved = True
    passes = 0
    while improved and passes < max_passes:
        improved = False
        passes += 1
        for i in range(1, n - 1):
            for j in range(i + 1, n):
                candidate = best_order[:i] + best_order[i:j+1][::-1] + best_order[j+1:]
                cand_obj, _ = evaluate_order(candidate, water_weight, deadline_weight, rules)
                if cand_obj < best_obj - 1e-4:
                    best_order = candidate
                    best_obj = cand_obj
                    improved = True
                    break
            if improved:
                break
    return best_order

def optimize_schedule(body: Dict[str, Any]) -> Dict[str, Any]:
    """Execute complete optimization workflow with input validation,
    heuristics execution, baseline retention safeguard, and traceability.
    """
    if not isinstance(body, dict):
        return {
            "status": "NO FEASIBLE PLAN UNDER CURRENT CONSTRAINTS",
            "classification": "SYNTHETIC_DATA",
            "notice": "Simulation — not L'Oréal production data.",
            "constraint_explanation": "Request body must be an object."
        }
    q = body["batches"] if "batches" in body else generate_batches(body.get("seed", 2030))
    error = validate_queue(q)
    if error:
        return {
            "status": "NO FEASIBLE PLAN UNDER CURRENT CONSTRAINTS",
            "classification": "SYNTHETIC_DATA",
            "notice": "Simulation — not L'Oréal production data.",
            "constraint_explanation": error
        }
    try:
        w = float(body.get("water_weight", 1.0))
        d = float(body.get("deadline_weight", 1.0))
    except (TypeError, ValueError):
        return {
            "status": "NO FEASIBLE PLAN UNDER CURRENT CONSTRAINTS",
            "classification": "SYNTHETIC_DATA",
            "notice": "Simulation — not L'Oréal production data.",
            "constraint_explanation": "Objective weights must be numeric."
        }
    if not math.isfinite(w) or not math.isfinite(d) or w < 0 or d < 0:
        return {
            "status": "NO FEASIBLE PLAN UNDER CURRENT CONSTRAINTS",
            "classification": "SYNTHETIC_DATA",
            "notice": "Simulation — not L'Oréal production data.",
            "constraint_explanation": "Objective weights must be finite and non-negative."
        }

    # Evaluate Baseline
    baseline_objective, baseline = evaluate_order(q, w, d)
    base_water = round(sum(x["litres"] for x in baseline), 1)

    # Candidate 1: Greedy constructive heuristic
    greedy_order = score_order_greedy(q, w, d)
    greedy_obj, greedy_trans = evaluate_order(greedy_order, w, d)
    greedy_water = round(sum(x["litres"] for x in greedy_trans), 1)

    # Candidate 2: 2-Opt Local Search refinement
    two_opt_order = score_order_two_opt(greedy_order, w, d)
    two_opt_obj, two_opt_trans = evaluate_order(two_opt_order, w, d)
    two_opt_water = round(sum(x["litres"] for x in two_opt_trans), 1)

    # Algorithm selection
    algo_req = body.get("algorithm", "best")
    if algo_req == "greedy":
        candidate_order, candidate_obj, trans, algo_name = greedy_order, greedy_obj, greedy_trans, "Greedy Nearest-Neighbor"
    elif algo_req == "two_opt":
        candidate_order, candidate_obj, trans, algo_name = two_opt_order, two_opt_obj, two_opt_trans, "2-Opt Local Search Refinement"
    else:
        if two_opt_obj <= greedy_obj:
            candidate_order, candidate_obj, trans, algo_name = two_opt_order, two_opt_obj, two_opt_trans, "2-Opt Local Search Refinement"
        else:
            candidate_order, candidate_obj, trans, algo_name = greedy_order, greedy_obj, greedy_trans, "Greedy Nearest-Neighbor"

    # Baseline Retention Safeguard
    retained = candidate_obj >= baseline_objective
    if retained:
        candidate_order, trans, candidate_obj, algo_name = q, baseline, baseline_objective, "Baseline (Retained Safeguard)"

    optimization_id = str(uuid.uuid4())
    cand_water = round(sum(x["litres"] for x in trans), 1)

    return {
        "status": "FEASIBLE",
        "optimization_id": optimization_id,
        "classification": "SYNTHETIC_DATA",
        "notice": "Simulation — not L'Oréal production data.",
        "baseline": {
            "order": [x["id"] for x in q],
            "water_demand_l": base_water,
            "objective": round(baseline_objective, 1),
            "duration_min": round(sum(x["minutes"] for x in baseline), 1)
        },
        "optimized": {
            "order": [x["id"] for x in candidate_order],
            "water_demand_l": cand_water,
            "objective": round(candidate_obj, 1),
            "duration_min": round(sum(x["minutes"] for x in trans), 1),
            "transitions": trans
        },
        "algorithm_used": algo_name,
        "algorithm_comparison": {
            "baseline": {"water_l": base_water, "objective": round(baseline_objective, 1)},
            "greedy": {"water_l": greedy_water, "objective": round(greedy_obj, 1)},
            "two_opt": {"water_l": two_opt_water, "objective": round(two_opt_obj, 1)}
        },
        "method": "Greedy constructive heuristic; baseline candidate retained when the heuristic cannot improve the configured objective. It does not prove global optimality.",
        "baseline_retained": retained
    }
