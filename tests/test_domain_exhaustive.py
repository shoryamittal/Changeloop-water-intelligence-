"""ClearLoop Domain & Optimizer Exhaustive Test Suite.
Covers:
- Phase 3: Changeover burden matrix, difficult transitions, formulation chemistry,
  edge cases (empty queue, 1-batch, 2-batch, duplicate IDs, fixed batches, deadlines).
- Phase 4: Optimizer property tests (permutation invariants, set equality,
  no duplicates, no unexpected batch creation, monotonic objective improvement).
"""
import unittest
import copy
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import core
from core.cleanability import PLANNING_BATCHES, PLANNING_MATRIX_SPEC, calculate_burden, generate_batches
from core.optimizer import (
    evaluate_order, score_order_greedy, score_order_two_opt, optimize_schedule
)

class DomainExhaustiveTests(unittest.TestCase):
    """Rigorous tests for cosmetic cleanability physics and 2-Opt combinatorial engine."""

    def test_01_changeover_burden_identical_family(self):
        """Transitions within same product family are tagged and calculate expected litres."""
        b1 = PLANNING_BATCHES["B-217"]
        b2 = PLANNING_BATCHES["B-218"]
        burden = calculate_burden(b1, b2)
        self.assertIsInstance(burden, dict)
        self.assertIn("litres", burden)
        self.assertIn("minutes", burden)
        self.assertGreater(burden["litres"], 0)
        self.assertGreater(burden["minutes"], 0)
        self.assertIn("same formula family", burden["reasons"])

    def test_02_changeover_burden_difficult_transitions(self):
        """Dark-to-light transitions trigger penalty multipliers and explicit rationale tags."""
        b_dark = PLANNING_BATCHES["B-220"]   # shade: dark
        b_light = PLANNING_BATCHES["B-221"]  # shade: light
        burden = calculate_burden(b_dark, b_light)
        self.assertIn("dark-to-light transition", burden["reasons"])
        self.assertGreaterEqual(burden["litres"], 100.0)

    def test_03_authoritative_planning_matrix_spec(self):
        """Authoritative pairwise planning matrix has complete coverage and non-negative values."""
        batch_ids = list(PLANNING_BATCHES.keys())
        for f_id in batch_ids:
            self.assertIn(f_id, PLANNING_MATRIX_SPEC)
            targets = PLANNING_MATRIX_SPEC[f_id]
            for t_id in batch_ids:
                self.assertIn(t_id, targets, f"Missing matrix transition {f_id} -> {t_id}")
                spec = targets[t_id]
                self.assertGreaterEqual(spec["litres"], 0)
                self.assertGreaterEqual(spec["minutes"], 0)

        # Bottleneck cell invariant: B-220 -> B-218 is the 450 L plant bottleneck
        bottleneck = PLANNING_MATRIX_SPEC["B-220"]["B-218"]
        self.assertEqual(bottleneck["litres"], 450)
        self.assertEqual(bottleneck["minutes"], 68)
        self.assertTrue(bottleneck.get("isBottleneck"))

    def test_04_optimizer_empty_queue(self):
        """Optimizer handles empty queue without unhandled exception."""
        res = optimize_schedule({"batches": []})
        self.assertEqual(res["status"], "NO FEASIBLE PLAN UNDER CURRENT CONSTRAINTS")
        self.assertIn("No batches supplied", res["constraint_explanation"])

    def test_05_optimizer_single_batch(self):
        """Single batch requires 0 transitions, 0 water demand, 0 duration."""
        sample_batches = generate_batches(2030, 5)
        single_batch = [sample_batches[0]]
        res = optimize_schedule({"batches": single_batch})
        self.assertEqual(res["status"], "FEASIBLE")
        self.assertEqual(len(res["optimized"]["order"]), 1)
        self.assertEqual(res["optimized"]["water_demand_l"], 0.0)
        self.assertEqual(res["optimized"]["duration_min"], 0.0)
        self.assertEqual(len(res["optimized"]["transitions"]), 0)

    def test_06_optimizer_two_batches(self):
        """Two batches yield exactly 1 transition, evaluating both orders."""
        sample_batches = generate_batches(2030, 5)
        batches = [sample_batches[0], sample_batches[1]]
        res = optimize_schedule({"batches": batches})
        self.assertEqual(res["status"], "FEASIBLE")
        self.assertEqual(len(res["optimized"]["order"]), 2)
        self.assertEqual(len(res["optimized"]["transitions"]), 1)
        self.assertLessEqual(res["optimized"]["water_demand_l"], res["baseline"]["water_demand_l"])

    def test_07_optimizer_preserves_batch_multiset_invariant(self):
        """Invariant: Optimized output order must be an exact bijection (permutation) of input batches."""
        for seed in [101, 555, 2026, 2030, 9999]:
            res = optimize_schedule({"seed": seed, "algorithm": "two_opt"})
            self.assertEqual(res["status"], "FEASIBLE")

            in_ids = res["baseline"]["order"]
            out_ids = res["optimized"]["order"]

            # Invariant 1: Length equality
            self.assertEqual(len(in_ids), len(out_ids), f"Length mismatch on seed {seed}")

            # Invariant 2: Set equality (no missing batches, no hallucinated batches)
            self.assertEqual(set(in_ids), set(out_ids), f"Set mismatch on seed {seed}")

            # Invariant 3: No duplicate IDs
            self.assertEqual(len(out_ids), len(set(out_ids)), f"Duplicate IDs detected on seed {seed}")

    def test_08_optimizer_monotonic_safeguard(self):
        """Invariant: 2-Opt local search refinement candidate objective is never worse than baseline."""
        for seed in range(2025, 2045):
            res = optimize_schedule({"seed": seed, "algorithm": "two_opt"})
            self.assertEqual(res["status"], "FEASIBLE")
            base_obj = res["baseline"]["objective"]
            opt_obj = res["optimized"]["objective"]
            self.assertLessEqual(opt_obj, base_obj + 1e-4, f"Degraded objective on seed {seed}: {opt_obj} > {base_obj}")

    def test_09_optimizer_already_optimal_sequence(self):
        """If a sequence cannot be improved, baseline safeguard preserves order safely."""
        sample_batches = generate_batches(2030, 5)
        obj_base, _ = evaluate_order(sample_batches, water_weight=1.0, deadline_weight=1.0)
        res = score_order_two_opt(sample_batches, water_weight=1.0, deadline_weight=1.0)
        obj_after, _ = evaluate_order(res, water_weight=1.0, deadline_weight=1.0)
        self.assertLessEqual(obj_after, obj_base + 1e-4)

    def test_10_optimizer_duplicate_ids_handling(self):
        """Queues with duplicate IDs are rejected safely by queue validation."""
        sample_batches = generate_batches(2030, 5)
        batch_a = copy.deepcopy(sample_batches[0])
        batch_b = copy.deepcopy(sample_batches[0])
        res = optimize_schedule({"batches": [batch_a, batch_b]})
        self.assertEqual(res["status"], "NO FEASIBLE PLAN UNDER CURRENT CONSTRAINTS")

    def test_11_optimizer_algorithm_comparison_coherence(self):
        """Algorithm comparison table reports baseline, greedy, and two_opt coherently."""
        res = optimize_schedule({"seed": 2030, "algorithm": "two_opt"})
        comp = res.get("algorithm_comparison", {})
        self.assertIn("baseline", comp)
        self.assertIn("greedy", comp)
        self.assertIn("two_opt", comp)
        # 2-Opt is at least as good as baseline
        self.assertLessEqual(comp["two_opt"]["objective"], comp["baseline"]["objective"] + 1e-4)

    def test_12_non_claim_of_global_optimality(self):
        """System documents heuristic 2-Opt nature rather than claiming unverified global optimality."""
        res = optimize_schedule({"seed": 2030, "algorithm": "two_opt"})
        self.assertIn("Local Search", res["algorithm_used"])
        self.assertNotIn("Globally Optimal", res["algorithm_used"])

if __name__ == "__main__":
    unittest.main()
