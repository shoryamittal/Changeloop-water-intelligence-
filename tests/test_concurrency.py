# -*- coding: utf-8 -*-
"""Concurrency tests for the coefficient registry.

WHY THIS FILE EXISTS
--------------------
`core/scenarios.py` runs its sensitivity and ablation studies by
temporarily replacing entries in the global `core.factors.FACTORS`
registry. The threading HTTP server serves requests in parallel. So a
request answered while a study is mid-sweep could read a patched
coefficient and return a number computed against a value the caller never
asked for - silently, with a 200 status and no way to detect it from the
response.

This was not hypothetical. The frontend render test began failing
intermittently on exactly one assertion - the "cut salt 20%" proof came
back as something other than -20.0% - because the test fires thirteen API
calls concurrently and `/api/ablation` was patching the registry
underneath `/api/narrative`.

For a system whose entire claim is that every displayed number is
traceable to a registered coefficient, a reader that can observe a torn
registry is the most serious defect available. These tests fail if the
reader-side locking is ever removed.
"""
import threading
import time
import unittest

from core import factors, narrative, scenarios, zld


class RegistryLocking(unittest.TestCase):

    def test_readers_and_writers_share_one_lock(self):
        """A second lock would serialise writers against each other while
        leaving readers free to tear. The lock must be the registry's."""
        self.assertIs(
            scenarios._REGISTRY_LOCK, factors.REGISTRY_LOCK,
            "core.scenarios is not using core.factors.REGISTRY_LOCK. A "
            "separate writer-side lock leaves every reader - every API "
            "request - free to observe a half-patched registry.")

    def test_lock_is_reentrant(self):
        """ablation() calls factors.get() while already holding the lock.
        A plain Lock would deadlock the server on the first study."""
        with factors.REGISTRY_LOCK:
            with factors.REGISTRY_LOCK:
                self.assertGreater(factors.get("mee_steam_economy"), 0.0)

    def test_sensitivity_restores_every_coefficient(self):
        """A study that leaks a patched value would corrupt every later
        request, not just the concurrent one."""
        before = {k: f.value for k, f in factors.FACTORS.items()}
        scenarios.sensitivity()
        after = {k: f.value for k, f in factors.FACTORS.items()}
        self.assertEqual(
            before, after,
            "sensitivity() did not restore the registry. A leaked patch "
            "silently changes every number the system reports from here "
            "on.")

    def test_ablation_restores_every_coefficient(self):
        before = {k: f.value for k, f in factors.FACTORS.items()}
        scenarios.ablation()
        after = {k: f.value for k, f in factors.FACTORS.items()}
        self.assertEqual(before, after,
                         "ablation() did not restore the registry.")


class ReadsAreNeverTorn(unittest.TestCase):
    """The regression test for the bug that was actually found.

    Hammer the salt-vs-water proof from several threads while studies
    patch the registry from others. The proof is deterministic - it must
    be exactly 0.0% for water and -20.0% for salt, every single time. Any
    other value means a reader saw a patched coefficient.
    """

    ITERATIONS = 40
    READERS = 6
    WRITERS = 3

    # The proof is a PERCENTAGE, so a patch that applies to both halves of
    # the comparison cancels out of it. That is why the percentage stayed
    # at -20.0% even while the registry was being torn, and why testing it
    # alone would have been a test that cannot fail.
    #
    # The published-band validation is an ABSOLUTE figure - 18,340 mg/L
    # divided by the 60,000 mg/L reject ceiling - so it moves the moment
    # that ceiling is patched. sensitivity() drives the ceiling to 90,000
    # (giving 20.4%) and ablation() to 10,000,000 (giving 0.2%). Those are
    # the exact wrong values that were being served.
    EXPECTED_REJECT_PCT_AT_CPCB_INLET = 30.6

    def test_published_validation_is_stable_under_concurrent_studies(self):
        bad = []
        stop = threading.Event()
        lock = threading.Lock()
        want = self.EXPECTED_REJECT_PCT_AT_CPCB_INLET

        def reader():
            for _ in range(self.ITERATIONS):
                if stop.is_set():
                    return
                try:
                    v = narrative.validation()
                    got = v["points"][-1]["predicted_reject_frac_pct"]
                    s = zld.sensitivity_salt_vs_water()
                    w = s["cut_water_20pct_only"]["mee_energy_change_pct"]
                    m = s["cut_salt_20pct_only"]["mee_energy_change_pct"]
                except Exception as exc:          # noqa: BLE001
                    with lock:
                        bad.append("reader raised {!r}".format(exc))
                    return
                if abs(got - want) > 0.05:
                    with lock:
                        bad.append(
                            "torn read: reject fraction at CPCB's measured "
                            "18,340 mg/L inlet came back as {:.1f}%, "
                            "expected {:.1f}%. A patched reject ceiling was "
                            "visible to a reader.".format(got, want))
                    return
                if abs(w - 0.0) > 1e-9 or abs(m - (-20.0)) > 1e-6:
                    with lock:
                        bad.append(
                            "torn read: water {:+.6f}% salt {:+.6f}% "
                            "(expected +0.0% / -20.0%)".format(w, m))
                    return

        def writer():
            for n in range(3):
                if stop.is_set():
                    return
                try:
                    # alternate the two studies: they patch the reject
                    # ceiling to different wrong values
                    if n % 2:
                        scenarios.ablation()
                    else:
                        scenarios.sensitivity()
                except Exception as exc:          # noqa: BLE001
                    with lock:
                        bad.append("writer raised {!r}".format(exc))
                    return

        threads = ([threading.Thread(target=reader, daemon=True)
                    for _ in range(self.READERS)] +
                   [threading.Thread(target=writer, daemon=True)
                    for _ in range(self.WRITERS)])
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=120)
        stop.set()

        alive = [t for t in threads if t.is_alive()]
        self.assertEqual(
            alive, [],
            "{} thread(s) did not finish within the timeout - the registry "
            "lock is probably deadlocking. If a plain Lock replaced the "
            "RLock, ablation() would block on its own "
            "lock.".format(len(alive)))
        self.assertEqual(
            bad, [],
            "Readers observed a patched registry while studies were "
            "running. First few: {}\\n"
            "This is the bug REGISTRY_LOCK exists to prevent: a request "
            "served alongside a sensitivity or ablation study returned "
            "numbers computed against a coefficient the caller never asked "
            "for, with a 200 status and no error.".format(bad[:3]))

    def test_a_reader_cannot_see_a_patch_that_is_still_open(self):
        """The deterministic reproduction.

        The stress test above only catches this by luck of scheduling: a
        dict assignment is atomic under the GIL, so a reader never sees a
        half-written Factor - it sees a fully-written WRONG one, and only
        if it happens to read inside the window a study holds the patch.
        Relying on that timing makes a test that passes with the bug
        present, which is worse than no test.

        So this one opens the window and holds it open. One thread takes
        the registry lock and patches the reject ceiling to 90,000 mg/L -
        exactly what sensitivity() does - then waits. Meanwhile this
        thread asks for the published-band validation.

        With reader-side locking the question simply waits its turn and
        gets 30.6%. Without it, the answer comes back instantly as
        18,340 / 90,000 = 20.4% - a wrong number, served with no error.
        """
        want = self.EXPECTED_REJECT_PCT_AT_CPCB_INLET
        patched_tds = 90_000.0
        wrong = round(100.0 * 18_340.0 / patched_tds, 1)
        self.assertNotAlmostEqual(
            wrong, want, places=1,
            msg="The patched value must produce a visibly different answer "
                "or this test proves nothing.")

        patch_open = threading.Event()
        reader_done = threading.Event()
        result = {}

        def holder():
            # Mirrors what scenarios.sensitivity() does: take the registry
            # lock, patch a coefficient, do work, restore.
            with factors.REGISTRY_LOCK:
                with scenarios._with_factor("ro_max_reject_tds_mg_l",
                                            patched_tds):
                    patch_open.set()
                    # hold the window open well past the reader's attempt
                    reader_done.wait(timeout=2.0)

        t = threading.Thread(target=holder, daemon=True)
        t.start()
        self.assertTrue(patch_open.wait(timeout=5.0),
                        "patching thread never started")

        started = time.time()
        v = narrative.validation()
        result["pct"] = v["points"][-1]["predicted_reject_frac_pct"]
        result["waited"] = time.time() - started
        reader_done.set()
        t.join(timeout=5.0)

        self.assertAlmostEqual(
            result["pct"], want, places=1,
            msg="A reader observed an open patch. The published-band "
                "validation returned {:.1f}% instead of {:.1f}%, because it "
                "read the reject ceiling while a study had it patched to "
                "{:.0f} mg/L. It waited only {:.3f}s, so it did not take "
                "the registry lock. Every API response computed during a "
                "sensitivity or ablation run is affected this way - wrong "
                "numbers, 200 status, no error.".format(
                    result["pct"], want, patched_tds, result["waited"]))

    def test_registry_is_intact_afterwards(self):
        """Belt and braces: after all that contention the registry must be
        exactly what it was at import."""
        self.assertEqual(factors.evidence_summary().get("MEASURED", 0), 0)
        self.assertGreater(factors.get("mee_steam_economy"), 0.0)
        self.assertAlmostEqual(
            factors.get("mee_specific_thermal_kwh_per_m3"),
            factors.get("h_vap_kwh_per_kg") * 1000.0
            / factors.get("mee_steam_economy"),
            places=2,
            msg="The derived thermal coefficient no longer matches its "
                "inputs - a sensitivity run leaked a recomputed value.")


if __name__ == "__main__":
    unittest.main(verbosity=2)
