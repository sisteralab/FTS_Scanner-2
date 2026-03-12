from __future__ import annotations

import os
import tempfile
import unittest
from datetime import datetime
import json
import math
from pathlib import Path

from PySide6.QtCore import QCoreApplication

from fts_scanner.store.measure_store import MeasureManager, MeasureModel, MeasureTableModel, MeasureType


class TestMeasureStore(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._app = QCoreApplication.instance() or QCoreApplication([])

    def setUp(self) -> None:
        MeasureManager._instances.clear()
        MeasureManager.latest_id = 0
        MeasureManager.table = None

    def test_create_and_filter(self) -> None:
        one = MeasureManager.create(measure_type=MeasureType.SPECTROGRAM, data={"points": []})
        MeasureManager.create(measure_type=MeasureType.SPECTROGRAM, data={"points": [1]})

        self.assertEqual(one.id, 1)
        self.assertEqual(MeasureManager.count(), 2)
        self.assertIsNotNone(MeasureManager.get(id=2))

    def test_table_model_updates(self) -> None:
        model = MeasureTableModel()
        MeasureManager.table = model

        MeasureManager.create(measure_type=MeasureType.SPECTROGRAM, data={"points": [1, 2, 3]})
        self.assertEqual(model.rowCount(), 1)
        self.assertEqual(model.columnCount(), len(MeasureModel.ind_attr_map))

    def test_save_all_creates_dump(self) -> None:
        MeasureManager.create(
            measure_type=MeasureType.SPECTROGRAM,
            data={"points": [{"x": 1, "ts": datetime.now()}]},
        )

        with tempfile.TemporaryDirectory() as tmp:
            cwd = os.getcwd()
            try:
                os.chdir(tmp)
                path = MeasureManager.save_all()
                self.assertIsNotNone(path)
                self.assertTrue(Path(path).exists())
                self.assertEqual(Path(path).suffix, ".json")
            finally:
                os.chdir(cwd)

    def test_to_json_contains_quicklook_arrays(self) -> None:
        measure = MeasureManager.create(
            measure_type=MeasureType.SPECTROGRAM,
            data={
                "settings": {"step_units": 10},
                "points": [
                    {
                        "index": idx,
                        "repeat": 0,
                        "position_steps": idx * 10,
                        "signal": float(idx),
                        "timestamp": datetime.now(),
                    }
                    for idx in range(16)
                ],
            },
        )
        payload = measure.to_json()
        quicklook = payload["data"]["quicklook"]
        self.assertEqual(len(quicklook["points_steps"]), 16)
        self.assertEqual(len(quicklook["raw_signal"]), 16)
        self.assertGreater(len(quicklook["frequency_thz"]), 0)
        self.assertEqual(len(quicklook["frequency_thz"]), len(quicklook["spectrum"]))
        self.assertEqual(len(quicklook["frequency_thz"]), len(quicklook["spectrum_raw"]))
        self.assertAlmostEqual(
            quicklook["spectrum"][1],
            math.sqrt(quicklook["spectrum_raw"][1]),
            places=8,
        )
        # OPD uses factor 2 => first bin is c / (N * 2 * step_um).
        expected_bin_1_thz = 299.792458 / (16 * 2 * 10 * 2.5)
        self.assertAlmostEqual(quicklook["frequency_thz"][1], expected_bin_1_thz, places=9)
        json.dumps(payload, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    unittest.main()
