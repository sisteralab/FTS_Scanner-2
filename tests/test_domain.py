from __future__ import annotations

import unittest

from fts_scanner.domain.models import ScanSettings


class TestDomainModels(unittest.TestCase):
    def test_scan_settings_derived_values(self) -> None:
        settings = ScanSettings(
            wait_time_ms=400,
            positive_border_mm=10.0,
            negative_border_mm=10.0,
            step_units=10,
            repeats=2,
        )

        self.assertEqual(settings.start_steps, -4000)
        self.assertEqual(settings.total_span_steps, 8000)
        self.assertEqual(settings.point_count, 801)
        self.assertEqual(settings.resolution_thz, 3.0)


if __name__ == "__main__":
    unittest.main()
