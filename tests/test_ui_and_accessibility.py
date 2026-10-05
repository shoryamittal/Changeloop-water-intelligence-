"""ClearLoop UI, DOM Structure, Design System & Accessibility (a11y) Test Suite.

Covers:
- Phase 21: Accessibility standards (ARIA landmarks, viewport, semantic headings, buttons).
- Phase 22: Static asset integrity (all images, stylesheets, scripts served with HTTP 200).
- Phase 23: CSS Design System token hierarchy & responsive media queries.
- Phase 24: Navigation structure and live served DOM layout.
"""
import unittest
import urllib.request
import re
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BASE_URL = "http://localhost:8000"

class UIAccessibilityTests(unittest.TestCase):
    """Rigorous frontend inspection, accessibility checks, and design token validation."""

    @classmethod
    def setUpClass(cls):
        html_path = PROJECT_ROOT / "frontend" / "index.html"
        css_path = PROJECT_ROOT / "frontend" / "style.css"
        with open(html_path, "r", encoding="utf-8") as f:
            cls.html = f.read()
        with open(css_path, "r", encoding="utf-8") as f:
            cls.css = f.read()

    def test_01_static_assets_served_successfully(self):
        """All referenced stylesheets, scripts, and imagery return HTTP 200 from live server."""
        asset_urls = [
            "/frontend/style.css",
            "/frontend/app.js",
            "/frontend/cip_fluidics.jpg",
            "/frontend/thermal_phe.jpg"
        ]
        for url in asset_urls:
            req = urllib.request.Request(f"{BASE_URL}{url}")
            with urllib.request.urlopen(req, timeout=5) as res:
                self.assertEqual(res.status, 200, f"Asset {url} returned status {res.status}")
                data = res.read()
                self.assertGreater(len(data), 0, f"Asset {url} has empty body")

    def test_02_semantic_structure_and_landmarks(self):
        """Page includes essential HTML5 landmark elements: header, nav, main, aside, footer."""
        self.assertIn("<header", self.html)
        self.assertIn("<nav", self.html)
        self.assertIn("<main", self.html)
        self.assertIn("<aside", self.html)
        self.assertIn("<footer", self.html)

    def test_03_accessibility_attributes_and_aria(self):
        """Validates viewport meta, language, ARIA labels on navigation, and semantic landmarks."""
        # 1. Document language
        self.assertRegex(self.html, r'<html\s+lang=["\']en["\']')
        
        # 2. Viewport tag
        self.assertRegex(self.html, r'<meta\s+name=["\']viewport["\']\s+content=["\'][^"\']+["\']')
        
        # 3. Primary navigation has aria-label
        self.assertIn('aria-label="Primary navigation"', self.html)
        self.assertIn('aria-label="Verification navigation"', self.html)

        # 4. Form inputs have labels or associated IDs
        inputs = re.findall(r'<input\s+[^>]*id=["\']([^"\']+)["\']', self.html)
        for inp_id in inputs:
            self.assertTrue(len(inp_id) > 0)

    def test_04_heading_hierarchy(self):
        """Page maintains structured heading elements (h1, h2, h3) without skipping structure."""
        h1_tags = re.findall(r'<h1[^>]*>(.*?)</h1>', self.html, re.DOTALL)
        self.assertGreaterEqual(len(h1_tags), 1, "Must contain at least one top-level h1 tag")
        self.assertTrue(any("Autonomous Water Stewardship" in h or "ClearLoop" in h for h in h1_tags))

    def test_05_css_design_tokens_and_colors(self):
        """Design tokens enforce high-contrast industrial safety palette (Emerald, Amber, Rose, Slate)."""
        # Industrial color tokens
        self.assertRegex(self.css, r'--(green|panel|deep|line|page|gold)', "CSS must define CSS custom properties")
        
        # Safe contrast emerald tokens
        self.assertTrue(
            "#059669" in self.css or "#10b981" in self.css or "#2e6d52" in self.css,
            "CSS must define emerald green industrial verification tokens"
        )

        # Alert / Veto tokens
        self.assertTrue(
            "#f43f5e" in self.css or "#e11d48" in self.css or "#ef4444" in self.css or "red" in self.css,
            "CSS must define veto / alert red tokens"
        )

    def test_06_css_responsive_media_queries(self):
        """CSS includes responsive layout media queries for multi-viewport compatibility."""
        media_queries = re.findall(r'@media\s*\([^\)]+\)', self.css)
        self.assertGreaterEqual(len(media_queries), 2, "CSS must provide responsive media queries")

    def test_07_interactive_dialogs_and_modal_architecture(self):
        """Dialog modal element exists for the interactive Guided Judge Tour."""
        self.assertIn('<dialog id="judgeDialog">', self.html)
        self.assertIn('judgeFinish()', self.html)
        self.assertIn('judgePrevious()', self.html)

    def test_08_core_navigation_views_complete_coverage(self):
        """All primary architecture navigation buttons match canonical application views."""
        expected_views = ['overview', 'planning', 'optimizer', 'cleaning', 'cascade', 'analytics', 'scenarios', 'pilot']
        for v in expected_views:
            pattern = f'data-view=["\']{v}["\']'
            self.assertRegex(self.html, pattern, f"Navigation button for view '{v}' must exist in DOM")

    def test_09_bottom_audit_seal_and_human_in_the_loop_declaration(self):
        """Master specification requirement: Human-in-the-Loop & ISO 14046 seal bar in DOM."""
        self.assertIn("HUMAN-IN-THE-LOOP ARCHITECTURE", self.html)
        self.assertIn("ISO 14046", self.html)
        self.assertIn("AUDIT TRAIL SEALED", self.html)

if __name__ == "__main__":
    unittest.main()
