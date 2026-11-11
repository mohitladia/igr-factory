from __future__ import annotations

import unittest
from types import SimpleNamespace

from dashboard.studio_server import PORT, StudioHandler, get_run_details


class DashboardSafetyTests(unittest.TestCase):
    def test_local_origin_is_allowed(self) -> None:
        handler = SimpleNamespace(headers={"Origin": f"http://127.0.0.1:{PORT}"})
        self.assertTrue(StudioHandler._origin_allowed(handler))

    def test_untrusted_origin_is_rejected(self) -> None:
        handler = SimpleNamespace(headers={"Origin": "https://attacker.example"})
        self.assertFalse(StudioHandler._origin_allowed(handler))

    def test_path_traversal_run_ids_are_rejected(self) -> None:
        self.assertIsNone(get_run_details("../.env"))
        self.assertIsNone(get_run_details("..\\.env"))


if __name__ == "__main__":
    unittest.main()
